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
    ADS_TOPUP_PAGE,
    DEVICE_FINGERPRINT,
)
from FragmentAPI.types.results import AdsTopupResult
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


async def _resolve_topup_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict,
    username: str,
) -> str:
    '''Resolve an Ads top-up recipient ID via Fragment API.'''
    await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "updateAdsTopupState",
            "mode": "new",
        },
    )

    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "searchAdsTopupRecipient",
            "query": username,
        },
    )
    recipient = (result.get("found") or {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            UserNotFoundError.NOT_FOUND.format(username=username),
        )
    return recipient


async def _init_ads_topup(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict,
    recipient: str,
    amount: int,
) -> str:
    '''Run initAdsTopupRequest and return Fragment req_id.'''
    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "initAdsTopupRequest",
            "recipient": recipient,
            "amount": amount,
        },
    )
    if result.get("error"):
        raise FragmentAPIError(result["error"])

    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            FragmentAPIError.NO_REQUEST_ID.format(
                context="TON topup",
            )
        )
    return req_id


async def _topup_ton_with_cookies(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool,
) -> AdsTopupResult:
    '''Full Ads topup flow using cookies + seed.'''
    headers = build_headers(ADS_TOPUP_PAGE)

    async with httpx.AsyncClient(
        cookies=client.cookies,
        timeout=client.timeout,
    ) as session:
        fragment_hash = await fetch_fragment_hash(
            client.cookies,
            headers,
            ADS_TOPUP_PAGE,
            client.timeout,
        )

        recipient = await _resolve_topup_recipient(
            session,
            fragment_hash,
            headers,
            username,
        )
        req_id = await _init_ads_topup(
            session,
            fragment_hash,
            headers,
            recipient,
            amount,
        )

        account = await build_account_info(client)
        transaction = await post_FragmentAPI(
            session,
            fragment_hash,
            headers,
            {
                "method": "getAdsTopupLink",
                "account": json.dumps(account),
                "device": DEVICE_FINGERPRINT,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
            },
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

    tx_result = await execute_transaction(client, transaction)

    if tx_result.boc and req_id:
        try:
            await client.confirm_request(
                req_id,
                tx_result.boc,
                referer="ads/topup",
            )
        except Exception:
            pass

    return AdsTopupResult(
        transaction_id=tx_result.tx_hash,
        username=username,
        amount=amount,
    )


async def _topup_ton_no_cookies(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool,
) -> AdsTopupResult:
    '''Ads topup flow without cookies via REST API.'''
    wallet_info = await fetch_wallet_info(client)
    sender_address = wallet_info.address

    prepared = await prepare_via_rest_api(
        endpoint="/api/v1/topup",
        payload={
            "username": username,
            "amount": amount,
            "show_sender": show_sender,
        },
        item_kind="topup",
        target=username,
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
                referer=prepared.confirm_referer or "ads/topup",
            )
        except Exception:
            pass

    return AdsTopupResult(
        transaction_id=tx_result.tx_hash,
        username=username,
        amount=amount,
    )


async def topup_ton(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult:
    '''Top up TON to a recipient Telegram Ads balance. Works with or without cookies.'''
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigError(ConfigError.INVALID_TON_AMOUNT)

    try:
        if client.has_cookies:
            return await _topup_ton_with_cookies(
                client, username, amount, show_sender,
            )
        else:
            return await _topup_ton_no_cookies(
                client, username, amount, show_sender,
            )
    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc