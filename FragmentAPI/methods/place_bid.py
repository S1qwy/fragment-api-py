'''
Place bid / buy now methods for Fragment marketplace items - async and sync
'''

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
)
from FragmentAPI.types.constants import DEVICE_FINGERPRINT, FRAGMENT_BASE_URL
from FragmentAPI.types.results import BidResult
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


_TYPE_URL_MAP = {
    1: "username",
    3: "number",
    5: "gift",
}


def _item_page_url(item_type: int, slug: str) -> str:
    '''Build the Fragment page URL for an item.'''
    prefix = _TYPE_URL_MAP.get(item_type, "username")
    return f"{FRAGMENT_BASE_URL}/{prefix}/{slug}"


async def place_bid(
    client: "AsyncFragmentClient",
    item_type: int,
    slug: str,
    bid: int,
) -> BidResult:
    '''Place a bid or buy-now on a Fragment marketplace item (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        item_type: Item type - 1 (username), 3 (number), 5 (gift).
        slug: Item identifier (username without @, number without +, gift slug).
        bid: Bid amount in TON (integer). Must be >= minimum bid or == buy-now price.

    Returns:
        BidResult with transaction_id, item_type, slug, bid, and confirm info.

    Raises:
        ConfigError: If item_type or bid is invalid.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    '''
    if item_type not in (1, 3, 5):
        raise ConfigError("Invalid item_type: must be 1 (username), 3 (number), or 5 (gift).")
    if not isinstance(bid, int) or bid < 1:
        raise ConfigError("Invalid bid amount: must be a positive integer (TON).")

    try:
        page_url = _item_page_url(item_type, slug)
        headers = build_headers(page_url)

        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, page_url, client.timeout
            )

            account = await build_account_info(client)
            transaction = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getBidLink",
                    "account": json.dumps(account),
                    "device": DEVICE_FINGERPRINT,
                    "transaction": "1",
                    "type": str(item_type),
                    "username": slug,
                    "bid": str(bid),
                },
            )

        if transaction.get("error"):
            raise FragmentAPIError(str(transaction["error"]))

        confirm_method = transaction.get("confirm_method")
        confirm_params = transaction.get("confirm_params", {})

        tx_hash = await execute_transaction(client, transaction)
        return BidResult(
            transaction_id=tx_hash,
            item_type=item_type,
            slug=slug,
            bid=bid,
            confirm_method=confirm_method,
            confirm_id=confirm_params.get("id"),
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def place_bid_sync(
    client: "FragmentClient",
    item_type: int,
    slug: str,
    bid: int,
) -> BidResult:
    '''Place a bid or buy-now on a Fragment marketplace item (sync).

    Args:
        client: Authenticated FragmentClient instance.
        item_type: Item type - 1 (username), 3 (number), 5 (gift).
        slug: Item identifier (username without @, number without +, gift slug).
        bid: Bid amount in TON (integer). Must be >= minimum bid or == buy-now price.

    Returns:
        BidResult with transaction_id, item_type, slug, bid, and confirm info.

    Raises:
        ConfigError: If item_type or bid is invalid.
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    '''
    if item_type not in (1, 3, 5):
        raise ConfigError("Invalid item_type: must be 1 (username), 3 (number), or 5 (gift).")
    if not isinstance(bid, int) or bid < 1:
        raise ConfigError("Invalid bid amount: must be a positive integer (TON).")

    try:
        page_url = _item_page_url(item_type, slug)
        headers = build_headers(page_url)

        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, page_url, client.timeout
            )

            account = build_account_info_sync(client)
            transaction = post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getBidLink",
                    "account": json.dumps(account),
                    "device": DEVICE_FINGERPRINT,
                    "transaction": "1",
                    "type": str(item_type),
                    "username": slug,
                    "bid": str(bid),
                },
            )

        if transaction.get("error"):
            raise FragmentAPIError(str(transaction["error"]))

        confirm_method = transaction.get("confirm_method")
        confirm_params = transaction.get("confirm_params", {})

        tx_hash = execute_transaction_sync(client, transaction)
        return BidResult(
            transaction_id=tx_hash,
            item_type=item_type,
            slug=slug,
            bid=bid,
            confirm_method=confirm_method,
            confirm_id=confirm_params.get("id"),
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc