"""
TON Ads top-up methods - async and sync
"""

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
from FragmentAPI.types.constants import ADS_TOPUP_PAGE, DEVICE_FINGERPRINT
from FragmentAPI.types.results import AdsTopupResult
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    fetch_fragment_hash_sync,
    post_FragmentAPI,
    post_FragmentAPI_sync,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    build_account_info_sync,
    execute_transaction,
    execute_transaction_sync,
)

if TYPE_CHECKING:
    from FragmentAPI.async_client import AsyncFragmentClient
    from FragmentAPI.client import FragmentClient


async def topup_ton(
    client: "AsyncFragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult:
    """Top up TON to a recipient's Telegram Ads balance (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        username: Recipient's Telegram username (with or without @).
        amount: Amount in TON - integer from 1 to 1 000 000 000.
        show_sender: Show your name as the sender. Defaults to True.

    Returns:
        AdsTopupResult with transaction_id, username, and amount.

    Raises:
        ConfigError: If amount is not 1-1 000 000 000.
        UserNotFoundError: If recipient not found.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigError(ConfigError.INVALID_TON_AMOUNT)

    try:
        headers = build_headers(ADS_TOPUP_PAGE)
        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, ADS_TOPUP_PAGE, client.timeout
            )

            await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {"method": "updateAdsTopupState", "mode": "new"},
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
                    UserNotFoundError.NOT_FOUND.format(username=username)
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
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="TON topup"
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

        tx_hash = await execute_transaction(client, transaction)
        return AdsTopupResult(
            transaction_id=tx_hash, username=username, amount=amount
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def topup_ton_sync(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult:
    """Top up TON to a recipient's Telegram Ads balance (sync).

    Args:
        client: Authenticated FragmentClient instance.
        username: Recipient's Telegram username (with or without @).
        amount: Amount in TON - integer from 1 to 1 000 000 000.
        show_sender: Show your name as the sender. Defaults to True.

    Returns:
        AdsTopupResult with transaction_id, username, and amount.

    Raises:
        ConfigError: If amount is not 1-1 000 000 000.
        UserNotFoundError: If recipient not found.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (1 <= amount <= 1_000_000_000):
        raise ConfigError(ConfigError.INVALID_TON_AMOUNT)

    try:
        headers = build_headers(ADS_TOPUP_PAGE)
        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, ADS_TOPUP_PAGE, client.timeout
            )

            post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {"method": "updateAdsTopupState", "mode": "new"},
            )

            result = post_FragmentAPI_sync(
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
                    UserNotFoundError.NOT_FOUND.format(username=username)
                )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initAdsTopupRequest",
                    "recipient": recipient,
                    "amount": amount,
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="TON topup"
                    )
                )

            account = build_account_info_sync(client)
            transaction = post_FragmentAPI_sync(
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

        tx_hash = execute_transaction_sync(client, transaction)
        return AdsTopupResult(
            transaction_id=tx_hash, username=username, amount=amount
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc
