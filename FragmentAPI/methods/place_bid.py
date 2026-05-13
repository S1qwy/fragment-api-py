'''
Place bid / buy now method for Fragment marketplace items — async only.
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
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    FRAGMENT_BASE_URL,
)
from FragmentAPI.types.results import BidResult
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


_TYPE_URL_MAP = {
    1: "username",
    3: "number",
    5: "gift",
}


def _item_page_url(
    item_type: int,
    slug: str,
) -> str:
    '''Build the Fragment page URL for an item.'''
    prefix = _TYPE_URL_MAP.get(item_type, "username")
    return f"{FRAGMENT_BASE_URL}/{prefix}/{slug}"


async def place_bid(
    client: "FragmentClient",
    item_type: int,
    slug: str,
    bid: int,
) -> BidResult:
    '''
    Place a bid or buy-now on a Fragment marketplace item.

    Args:
        client: Authenticated FragmentClient instance.
        item_type: 1 (username), 3 (number), 5 (gift).
        slug: Item identifier.
        bid: Bid amount in TON (integer).

    Returns:
        BidResult with transaction details.
    '''
    if item_type not in (1, 3, 5):
        raise ConfigError(
            "Invalid item_type: must be 1 (username), "
            "3 (number), or 5 (gift)."
        )
    if not isinstance(bid, int) or bid < 1:
        raise ConfigError(
            "Invalid bid amount: must be a positive integer (TON)."
        )

    try:
        page_url = _item_page_url(item_type, slug)
        headers = build_headers(page_url)

        async with httpx.AsyncClient(
            cookies=client.cookies,
            timeout=client.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies,
                headers,
                page_url,
                client.timeout,
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

        tx_result = await execute_transaction(client, transaction)

        return BidResult(
            transaction_id=tx_result.tx_hash,
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
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc