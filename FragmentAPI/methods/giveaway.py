"""
Giveaway methods for Stars and Premium on Fragment.

Handles both GRAM-based (on-chain) and EVM-based payment flows
for running giveaways through Fragment's API.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from curl_cffi import requests

from FragmentAPI.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    EVM_PAYMENT_METHODS,
    GRAM_PAYMENT_METHODS,
    PREMIUM_GIVEAWAY_PAGE,
    PREMIUM_MONTHS_VALID,
    STARS_GIVEAWAY_PACKAGES,
    STARS_GIVEAWAY_PAGE,
    VALID_PAYMENT_METHODS,
)
from FragmentAPI.types.results import (
    EvmPaymentResult,
    GiveawayPremiumResult,
    GiveawayStarsResult,
)
from FragmentAPI.methods.purchase import _normalize_payment_method
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_fragment_api,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

logger = logging.getLogger("FragmentAPI")


def _validate_stars_giveaway(amount: int, winners: int) -> None:
    """Validate stars giveaway parameters."""
    if amount not in STARS_GIVEAWAY_PACKAGES:
        raise ConfigurationError(
            ConfigurationError.INVALID_GIVEAWAY_PACKAGE.format(
                amount=amount,
                packages=", ".join(str(p) for p in sorted(STARS_GIVEAWAY_PACKAGES)),
            )
        )

    max_winners = min(max(amount // 100, 1), 10_000)
    if not isinstance(winners, int) or not (1 <= winners <= max_winners):
        raise ConfigurationError(
            ConfigurationError.INVALID_GIVEAWAY_WINNERS.format(
                winners=winners, max_winners=max_winners, amount=amount,
            )
        )


async def giveaway_stars(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
    payment_method: str = "gram",
) -> GiveawayStarsResult | EvmPaymentResult:
    """Run a Telegram Stars giveaway for a channel.

    Args:
        client: Authenticated FragmentClient instance.
        channel: Telegram channel username.
        winners: Number of giveaway winners.
        amount: Total Stars amount (must be from allowed packages).
        payment_method: Payment method string.

    Returns:
        GiveawayStarsResult for GRAM payments, EvmPaymentResult for EVM.

    Raises:
        ConfigurationError: If parameters are invalid.
        UserNotFoundError: If the channel is not found.
        VerificationError: If KYC is required.
    """
    _validate_stars_giveaway(amount, winners)

    api_payment = _normalize_payment_method(payment_method)
    if api_payment not in {_normalize_payment_method(m) for m in VALID_PAYMENT_METHODS}:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method, supported=", ".join(sorted(VALID_PAYMENT_METHODS)),
            )
        )

    is_gram = api_payment in {_normalize_payment_method(m) for m in GRAM_PAYMENT_METHODS}
    if is_gram:
        client._require_wallet()

    try:
        headers = build_headers(STARS_GIVEAWAY_PAGE)

        async with requests.AsyncSession(
            cookies=client.cookies, timeout=client.timeout, impersonate="chrome120",
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, STARS_GIVEAWAY_PAGE, client.timeout,
            )

            result = await post_fragment_api(
                session, fragment_hash, headers,
                {
                    "method": "searchStarsGiveawayRecipient",
                    "query": channel,
                    "quantity": winners,
                    "stars": amount,
                },
            )
            recipient = (result.get("found") or {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=channel))

            init_result = await post_fragment_api(
                session, fragment_hash, headers,
                {
                    "method": "initGiveawayStarsRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "stars": str(amount),
                    "payment_method": api_payment,
                },
            )
            if init_result.get("error"):
                raise FragmentAPIError(init_result["error"])
            req_id = init_result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(context="Stars giveaway")
                )

            if is_gram:
                account = await build_account_info(client)
                transaction = await post_fragment_api(
                    session, fragment_hash, headers,
                    {
                        "method": "getGiveawayStarsLink",
                        "account": json.dumps(account),
                        "device": DEVICE_FINGERPRINT,
                        "transaction": 1,
                        "id": req_id,
                    },
                )
                if transaction.get("need_verify"):
                    raise VerificationError(VerificationError.KYC_REQUIRED)

                if not transaction.get("evm"):
                    tx_result = await execute_transaction(client, transaction)
                    if tx_result.boc and req_id:
                        try:
                            await client.confirm_request(req_id, tx_result.boc, referer="stars/giveaway")
                        except Exception:
                            pass
                    return GiveawayStarsResult(
                        transaction_id=tx_result.tx_hash, channel=channel,
                        winners=winners, amount=amount, payment_method=payment_method,
                    )

            invoice = await fetch_evm_invoice(
                cookies=client.cookies, page_path="/stars/giveaway",
                recipient=recipient, payment_method=api_payment,
                quantity=winners, amount=amount, timeout=client.timeout,
            )
            return EvmPaymentResult(
                item_kind="giveaway_stars", target=channel,
                amount=amount, payment_method=payment_method, invoice=invoice,
            )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def giveaway_premium(
    client: "FragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: str = "gram",
) -> GiveawayPremiumResult | EvmPaymentResult:
    """Run a Telegram Premium giveaway for a channel.

    Args:
        client: Authenticated FragmentClient instance.
        channel: Telegram channel username.
        winners: Number of giveaway winners (1 to 24,000).
        months: Premium duration (3, 6, or 12 months).
        payment_method: Payment method string.

    Returns:
        GiveawayPremiumResult for GRAM payments, EvmPaymentResult for EVM.

    Raises:
        ConfigurationError: If parameters are invalid.
        UserNotFoundError: If the channel is not found.
        VerificationError: If KYC is required.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigurationError(ConfigurationError.INVALID_WINNERS_PREMIUM)
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)

    api_payment = _normalize_payment_method(payment_method)
    if api_payment not in {_normalize_payment_method(m) for m in VALID_PAYMENT_METHODS}:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method, supported=", ".join(sorted(VALID_PAYMENT_METHODS)),
            )
        )

    is_gram = api_payment in {_normalize_payment_method(m) for m in GRAM_PAYMENT_METHODS}
    if is_gram:
        client._require_wallet()

    try:
        headers = build_headers(PREMIUM_GIVEAWAY_PAGE)

        async with requests.AsyncSession(
            cookies=client.cookies, timeout=client.timeout, impersonate="chrome120",
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, PREMIUM_GIVEAWAY_PAGE, client.timeout,
            )

            result = await post_fragment_api(
                session, fragment_hash, headers,
                {
                    "method": "searchPremiumGiveawayRecipient",
                    "query": channel,
                    "quantity": winners,
                    "months": months,
                },
            )
            recipient = (result.get("found") or {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=channel))

            init_result = await post_fragment_api(
                session, fragment_hash, headers,
                {
                    "method": "initGiveawayPremiumRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "months": str(months),
                    "payment_method": api_payment,
                },
            )
            if init_result.get("error"):
                raise FragmentAPIError(init_result["error"])
            req_id = init_result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(context="Premium giveaway")
                )

            if is_gram:
                account = await build_account_info(client)
                transaction = await post_fragment_api(
                    session, fragment_hash, headers,
                    {
                        "method": "getGiveawayPremiumLink",
                        "account": json.dumps(account),
                        "device": DEVICE_FINGERPRINT,
                        "transaction": 1,
                        "id": req_id,
                    },
                )
                if transaction.get("need_verify"):
                    raise VerificationError(VerificationError.KYC_REQUIRED)

                if not transaction.get("evm"):
                    tx_result = await execute_transaction(client, transaction)
                    if tx_result.boc and req_id:
                        try:
                            await client.confirm_request(req_id, tx_result.boc, referer="premium/giveaway")
                        except Exception:
                            pass
                    return GiveawayPremiumResult(
                        transaction_id=tx_result.tx_hash, channel=channel,
                        winners=winners, amount=months, payment_method=payment_method,
                    )

            invoice = await fetch_evm_invoice(
                cookies=client.cookies, page_path="/premium/giveaway",
                recipient=recipient, payment_method=api_payment,
                winners=winners, months=months, timeout=client.timeout,
            )
            return EvmPaymentResult(
                item_kind="giveaway_premium", target=channel,
                amount=months, payment_method=payment_method, invoice=invoice,
            )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc