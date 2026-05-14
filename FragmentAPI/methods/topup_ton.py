'''
TON Ads top-up method — async only with confirmReq.
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
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


async def topup_ton(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult:
    '''
    Top up TON to a recipient Telegram Ads balance.

    Args:
        client: Authenticated FragmentClient instance.
        username: Recipient Telegram username.
        amount: Amount in TON — 1 to 1000000000.
        show_sender: Show your name as the sender.

    Returns:
        AdsTopupResult with transaction_id, username, and amount.
    '''
    if not isinstance(amount, int) or not (1 <= amount <= 1000000000):
        raise ConfigError(ConfigError.INVALID_TON_AMOUNT)

    try:
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
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=username),
                )

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

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc