'''
Premium giveaway method — async only with EVM support.
'''

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    EVM_PAYMENT_METHODS,
    PREMIUM_GIVEAWAY_PAGE,
    TON_PAYMENT_METHODS,
    VALID_PAYMENT_METHODS,
)
from FragmentAPI.types.results import (
    EvmPaymentResult,
    GiveawayPremiumResult,
)
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


async def giveaway_premium(
    client: "FragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: str = "ton",
) -> GiveawayPremiumResult | EvmPaymentResult:
    '''Run a Telegram Premium giveaway for a channel.'''
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigError(ConfigError.INVALID_WINNERS_PREMIUM)
    if months not in (3, 6, 12):
        raise ConfigError(ConfigError.INVALID_MONTHS)
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ConfigError(ConfigError.INVALID_PAYMENT_METHOD)

    try:
        headers = build_headers(PREMIUM_GIVEAWAY_PAGE)

        async with httpx.AsyncClient(
            cookies=client.cookies,
            timeout=client.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies,
                headers,
                PREMIUM_GIVEAWAY_PAGE,
                client.timeout,
            )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchPremiumGiveawayRecipient",
                    "query": channel,
                    "quantity": winners,
                    "months": months,
                },
            )
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=channel),
                )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiveawayPremiumRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "months": str(months),
                    "payment_method": payment_method,
                },
            )
            if result.get("error"):
                raise FragmentAPIError(result["error"])

            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Premium giveaway",
                    )
                )

            account = await build_account_info(client)
            transaction = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
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

        if payment_method in EVM_PAYMENT_METHODS or transaction.get("evm"):
            invoice = await fetch_evm_invoice(
                cookies=client.cookies,
                page_path="/premium/giveaway",
                recipient=recipient,
                payment_method=payment_method,
                winners=winners,
                months=months,
                timeout=client.timeout,
            )
            return EvmPaymentResult(
                item_kind="giveaway_premium",
                target=channel,
                amount=months,
                payment_method=payment_method,
                invoice=invoice,
            )

        if payment_method not in TON_PAYMENT_METHODS:
            raise FragmentAPIError(
                f"Unsupported payment_method flow: {payment_method}"
            )

        tx_result = await execute_transaction(client, transaction)

        if tx_result.boc and req_id:
            try:
                await client.confirm_request(
                    req_id,
                    tx_result.boc,
                    referer="premium/giveaway",
                )
            except Exception:
                pass

        return GiveawayPremiumResult(
            transaction_id=tx_result.tx_hash,
            channel=channel,
            winners=winners,
            amount=months,
            payment_method=payment_method,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc