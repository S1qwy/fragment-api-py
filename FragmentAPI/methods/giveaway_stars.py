"""
Stars giveaway methods - async and sync
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
from FragmentAPI.types.constants import DEVICE_FINGERPRINT, STARS_GIVEAWAY_PAGE
from FragmentAPI.types.results import GiveawayStarsResult
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


async def giveaway_stars(
    client: "AsyncFragmentClient",
    channel: str,
    winners: int,
    amount: int,
) -> GiveawayStarsResult:
    """Run a Telegram Stars giveaway for a channel (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        channel: Channel username (with or without @).
        winners: Number of winners - integer from 1 to 5.
        amount: Stars each winner receives - 500 to 1 000 000.

    Returns:
        GiveawayStarsResult with transaction_id, channel, winners, and amount.

    Raises:
        ConfigError: If winners or amount are invalid.
        UserNotFoundError: If channel not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 5):
        raise ConfigError(ConfigError.INVALID_WINNERS_STARS)
    if not isinstance(amount, int) or not (500 <= amount <= 1_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_PER_WINNER)

    try:
        headers = build_headers(STARS_GIVEAWAY_PAGE)
        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, STARS_GIVEAWAY_PAGE, client.timeout
            )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchStarsGiveawayRecipient",
                    "query": channel,
                },
            )
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=channel)
                )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiveawayStarsRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "stars": str(amount),
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Stars giveaway"
                    )
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

        tx_hash = await execute_transaction(client, transaction)
        return GiveawayStarsResult(
            transaction_id=tx_hash,
            channel=channel,
            winners=winners,
            amount=amount,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def giveaway_stars_sync(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
) -> GiveawayStarsResult:
    """Run a Telegram Stars giveaway for a channel (sync).

    Args:
        client: Authenticated FragmentClient instance.
        channel: Channel username (with or without @).
        winners: Number of winners - integer from 1 to 5.
        amount: Stars each winner receives - 500 to 1 000 000.

    Returns:
        GiveawayStarsResult with transaction_id, channel, winners, and amount.

    Raises:
        ConfigError: If winners or amount are invalid.
        UserNotFoundError: If channel not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 5):
        raise ConfigError(ConfigError.INVALID_WINNERS_STARS)
    if not isinstance(amount, int) or not (500 <= amount <= 1_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_PER_WINNER)

    try:
        headers = build_headers(STARS_GIVEAWAY_PAGE)
        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, STARS_GIVEAWAY_PAGE, client.timeout
            )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchStarsGiveawayRecipient",
                    "query": channel,
                },
            )
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=channel)
                )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiveawayStarsRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "stars": str(amount),
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Stars giveaway"
                    )
                )

            account = build_account_info_sync(client)
            transaction = post_FragmentAPI_sync(
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

        tx_hash = execute_transaction_sync(client, transaction)
        return GiveawayStarsResult(
            transaction_id=tx_hash,
            channel=channel,
            winners=winners,
            amount=amount,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc
