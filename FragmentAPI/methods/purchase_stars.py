"""
Telegram Stars purchase methods - async and sync
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.types.constants import DEVICE_FINGERPRINT, STARS_PAGE
from FragmentAPI.types.results import StarsResult
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


async def purchase_stars(
    client: "AsyncFragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> StarsResult:
    """Send Telegram Stars to a user (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        username: Recipient's Telegram username (with or without @).
        amount: Number of Stars - integer from 50 to 1 000 000.
        show_sender: Show your name as the gift sender. Defaults to True.

    Returns:
        StarsResult with transaction_id, username, and amount.

    Raises:
        ConfigError: If amount is not 50-1 000 000.
        UserNotFoundError: If user not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (50 <= amount <= 1_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_AMOUNT)

    try:
        headers = build_headers(STARS_PAGE)
        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, STARS_PAGE, client.timeout
            )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchStarsRecipient",
                    "query": username,
                    "quantity": "",
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
                    "method": "initBuyStarsRequest",
                    "recipient": recipient,
                    "quantity": amount,
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Stars purchase"
                    )
                )

            account = await build_account_info(client)
            transaction = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getBuyStarsLink",
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
        return StarsResult(
            transaction_id=tx_hash, username=username, amount=amount
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def purchase_stars_sync(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> StarsResult:
    """Send Telegram Stars to a user (sync).

    Args:
        client: Authenticated FragmentClient instance.
        username: Recipient's Telegram username (with or without @).
        amount: Number of Stars - integer from 50 to 1 000 000.
        show_sender: Show your name as the gift sender. Defaults to True.

    Returns:
        StarsResult with transaction_id, username, and amount.

    Raises:
        ConfigError: If amount is not 50-1 000 000.
        UserNotFoundError: If user not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(amount, int) or not (50 <= amount <= 1_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_AMOUNT)

    try:
        headers = build_headers(STARS_PAGE)
        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, STARS_PAGE, client.timeout
            )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchStarsRecipient",
                    "query": username,
                    "quantity": "",
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
                    "method": "initBuyStarsRequest",
                    "recipient": recipient,
                    "quantity": amount,
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Stars purchase"
                    )
                )

            account = build_account_info_sync(client)
            transaction = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getBuyStarsLink",
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
        return StarsResult(
            transaction_id=tx_hash, username=username, amount=amount
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc
