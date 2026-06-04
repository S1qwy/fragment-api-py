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
from FragmentAPI.methods._prepare import (
    prepare_via_rest_api,
    prepared_to_transaction_data,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    EVM_PAYMENT_METHODS,
    STARS_GIVEAWAY_PAGE,
    STARS_GIVEAWAY_PACKAGES,
    TON_PAYMENT_METHODS,
    VALID_PAYMENT_METHODS,
)
from FragmentAPI.types.results import (
    EvmPaymentResult,
    GiveawayStarsResult,
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
    fetch_wallet_info,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


def _validate_stars_giveaway(amount: int, winners: int) -> None:
    '''Validate stars giveaway parameters.'''
    if amount not in STARS_GIVEAWAY_PACKAGES:
        raise ConfigError(
            ConfigError.INVALID_GIVEAWAY_PACKAGE.format(
                amount=amount,
                packages=", ".join(
                    str(p) for p in sorted(STARS_GIVEAWAY_PACKAGES)
                ),
            )
        )

    max_winners = amount // 100
    if max_winners < 1:
        max_winners = 1
    if max_winners > 10_000:
        max_winners = 10_000

    if not isinstance(winners, int) or not (1 <= winners <= max_winners):
        raise ConfigError(
            ConfigError.INVALID_GIVEAWAY_WINNERS.format(
                winners=winners,
                max_winners=max_winners,
                amount=amount,
            )
        )


async def _resolve_giveaway_stars_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict,
    channel: str,
    winners: int,
    amount: int,
) -> str:
    '''Resolve a Stars giveaway recipient via Fragment API.'''
    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "searchStarsGiveawayRecipient",
            "query": channel,
            "quantity": winners,
            "stars": amount,
        },
    )
    recipient = (result.get("found") or {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            UserNotFoundError.NOT_FOUND.format(username=channel),
        )
    return recipient


async def _init_giveaway_stars(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict,
    recipient: str,
    winners: int,
    amount: int,
    payment_method: str,
) -> str:
    '''Run initGiveawayStarsRequest and return Fragment req_id.'''
    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "initGiveawayStarsRequest",
            "recipient": recipient,
            "quantity": str(winners),
            "stars": str(amount),
            "payment_method": payment_method,
        },
    )
    if result.get("error"):
        raise FragmentAPIError(result["error"])

    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            FragmentAPIError.NO_REQUEST_ID.format(
                context="Stars giveaway",
            )
        )
    return req_id


async def _giveaway_stars_with_cookies(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
    payment_method: str,
) -> GiveawayStarsResult | EvmPaymentResult:
    '''Full Stars giveaway flow using cookies + seed.'''
    headers = build_headers(STARS_GIVEAWAY_PAGE)

    async with httpx.AsyncClient(
        cookies=client.cookies,
        timeout=client.timeout,
    ) as session:
        fragment_hash = await fetch_fragment_hash(
            client.cookies,
            headers,
            STARS_GIVEAWAY_PAGE,
            client.timeout,
        )

        recipient = await _resolve_giveaway_stars_recipient(
            session,
            fragment_hash,
            headers,
            channel,
            winners,
            amount,
        )
        req_id = await _init_giveaway_stars(
            session,
            fragment_hash,
            headers,
            recipient,
            winners,
            amount,
            payment_method,
        )

        account = await build_account_info(client)
        transaction = await post_FragmentAPI(
            session,
            fragment_hash,
            headers,
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

    if payment_method in EVM_PAYMENT_METHODS or transaction.get("evm"):
        invoice = await fetch_evm_invoice(
            cookies=client.cookies,
            page_path="/stars/giveaway",
            recipient=recipient,
            payment_method=payment_method,
            quantity=winners,
            amount=amount,
            timeout=client.timeout,
        )
        return EvmPaymentResult(
            item_kind="giveaway_stars",
            target=channel,
            amount=amount,
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
                referer="stars/giveaway",
            )
        except Exception:
            pass

    return GiveawayStarsResult(
        transaction_id=tx_result.tx_hash,
        channel=channel,
        winners=winners,
        amount=amount,
        payment_method=payment_method,
    )


async def _giveaway_stars_no_cookies(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
    payment_method: str,
) -> GiveawayStarsResult:
    '''Stars giveaway flow without cookies via REST API.'''
    wallet_info = await fetch_wallet_info(client)
    sender_address = wallet_info.address

    prepared = await prepare_via_rest_api(
        endpoint="/api/v1/giveaway/stars",
        payload={
            "channel": channel,
            "winners": winners,
            "amount": amount,
            "payment_method": payment_method,
        },
        item_kind="giveaway_stars",
        target=channel,
        amount=amount,
        sender_wallet_address=sender_address,
        timeout=client.timeout,
    )

    tx_data = prepared_to_transaction_data(prepared)
    tx_result = await execute_transaction(client, tx_data)

    if tx_result.boc and prepared.req_id:
        try:
            await client.confirm_request(
                prepared.req_id,
                tx_result.boc,
                referer=prepared.confirm_referer or "stars/giveaway",
            )
        except Exception:
            pass

    return GiveawayStarsResult(
        transaction_id=tx_result.tx_hash,
        channel=channel,
        winners=winners,
        amount=amount,
        payment_method=payment_method,
    )


async def giveaway_stars(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
    payment_method: str = "ton",
) -> GiveawayStarsResult | EvmPaymentResult:
    '''Run a Telegram Stars giveaway for a channel. Works with or without cookies.'''
    _validate_stars_giveaway(amount, winners)
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ConfigError(ConfigError.INVALID_PAYMENT_METHOD)

    try:
        if client.has_cookies:
            return await _giveaway_stars_with_cookies(
                client, channel, winners, amount, payment_method,
            )
        else:
            if payment_method not in TON_PAYMENT_METHODS:
                raise ConfigError(
                    "No-cookie mode supports only TON payment methods.",
                )
            return await _giveaway_stars_no_cookies(
                client, channel, winners, amount, payment_method,
            )
    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc