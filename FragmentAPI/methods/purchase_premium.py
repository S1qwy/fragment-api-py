"""
Telegram Premium gift methods - async and sync
"""

from __future__ import annotations

import json
import time
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
from FragmentAPI.types.constants import DEVICE_FINGERPRINT, PREMIUM_PAGE
from FragmentAPI.types.results import PremiumResult
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


async def purchase_premium(
    client: "AsyncFragmentClient",
    username: str,
    months: int,
    show_sender: bool = True,
) -> PremiumResult:
    """Gift Telegram Premium to a user (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        username: Recipient's Telegram username (with or without @).
        months: Premium duration - 3, 6, or 12.
        show_sender: Show your name as the sender. Defaults to True.

    Returns:
        PremiumResult with transaction_id, username, and amount.

    Raises:
        ConfigError: If months is not 3, 6, or 12.
        UserNotFoundError: If user not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if months not in (3, 6, 12):
        raise ConfigError(ConfigError.INVALID_MONTHS)

    try:
        headers = build_headers(PREMIUM_PAGE)
        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, PREMIUM_PAGE, client.timeout
            )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchPremiumGiftRecipient",
                    "query": username,
                    "months": months,
                },
            )
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=username)
                )

            await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "updatePremiumState",
                    "mode": "new",
                    "lv": "false",
                    "dh": str(int(time.time())),
                },
            )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiftPremiumRequest",
                    "recipient": recipient,
                    "months": months,
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Premium purchase"
                    )
                )

            account = await build_account_info(client)
            transaction = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getGiftPremiumLink",
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
        return PremiumResult(
            transaction_id=tx_hash, username=username, amount=months
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def purchase_premium_sync(
    client: "FragmentClient",
    username: str,
    months: int,
    show_sender: bool = True,
) -> PremiumResult:
    """Gift Telegram Premium to a user (sync).

    Args:
        client: Authenticated FragmentClient instance.
        username: Recipient's Telegram username (with or without @).
        months: Premium duration - 3, 6, or 12.
        show_sender: Show your name as the sender. Defaults to True.

    Returns:
        PremiumResult with transaction_id, username, and amount.

    Raises:
        ConfigError: If months is not 3, 6, or 12.
        UserNotFoundError: If user not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if months not in (3, 6, 12):
        raise ConfigError(ConfigError.INVALID_MONTHS)

    try:
        headers = build_headers(PREMIUM_PAGE)
        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, PREMIUM_PAGE, client.timeout
            )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchPremiumGiftRecipient",
                    "query": username,
                    "months": months,
                },
            )
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=username)
                )

            post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "updatePremiumState",
                    "mode": "new",
                    "lv": "false",
                    "dh": str(int(time.time())),
                },
            )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiftPremiumRequest",
                    "recipient": recipient,
                    "months": months,
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Premium purchase"
                    )
                )

            account = build_account_info_sync(client)
            transaction = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getGiftPremiumLink",
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
        return PremiumResult(
            transaction_id=tx_hash, username=username, amount=months
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc
