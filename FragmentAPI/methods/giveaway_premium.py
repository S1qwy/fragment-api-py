"""
Premium giveaway methods - async and sync
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
from FragmentAPI.types.constants import DEVICE_FINGERPRINT, PREMIUM_GIVEAWAY_PAGE
from FragmentAPI.types.results import GiveawayPremiumResult
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


async def giveaway_premium(
    client: "AsyncFragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
) -> GiveawayPremiumResult:
    """Run a Telegram Premium giveaway for a channel (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        channel: Channel username (with or without @).
        winners: Number of winners - integer from 1 to 24 000.
        months: Premium duration per winner - 3, 6, or 12. Defaults to 3.

    Returns:
        GiveawayPremiumResult with transaction_id, channel, winners, and amount.

    Raises:
        ConfigError: If winners or months are invalid.
        UserNotFoundError: If channel not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigError(ConfigError.INVALID_WINNERS_PREMIUM)
    if months not in (3, 6, 12):
        raise ConfigError(ConfigError.INVALID_MONTHS)

    try:
        headers = build_headers(PREMIUM_GIVEAWAY_PAGE)
        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
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
                    UserNotFoundError.NOT_FOUND.format(username=channel)
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
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Premium giveaway"
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

        tx_hash = await execute_transaction(client, transaction)
        return GiveawayPremiumResult(
            transaction_id=tx_hash,
            channel=channel,
            winners=winners,
            amount=months,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def giveaway_premium_sync(
    client: "FragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
) -> GiveawayPremiumResult:
    """Run a Telegram Premium giveaway for a channel (sync).

    Args:
        client: Authenticated FragmentClient instance.
        channel: Channel username (with or without @).
        winners: Number of winners - integer from 1 to 24 000.
        months: Premium duration per winner - 3, 6, or 12. Defaults to 3.

    Returns:
        GiveawayPremiumResult with transaction_id, channel, winners, and amount.

    Raises:
        ConfigError: If winners or months are invalid.
        UserNotFoundError: If channel not found on Fragment.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigError(ConfigError.INVALID_WINNERS_PREMIUM)
    if months not in (3, 6, 12):
        raise ConfigError(ConfigError.INVALID_MONTHS)

    try:
        headers = build_headers(PREMIUM_GIVEAWAY_PAGE)
        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies,
                headers,
                PREMIUM_GIVEAWAY_PAGE,
                client.timeout,
            )

            result = post_FragmentAPI_sync(
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
                    UserNotFoundError.NOT_FOUND.format(username=channel)
                )

            result = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiveawayPremiumRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "months": str(months),
                },
            )
            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Premium giveaway"
                    )
                )

            account = build_account_info_sync(client)
            transaction = post_FragmentAPI_sync(
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

        tx_hash = execute_transaction_sync(client, transaction)
        return GiveawayPremiumResult(
            transaction_id=tx_hash,
            channel=channel,
            winners=winners,
            amount=months,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc
