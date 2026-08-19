"""
Place bid / buy now method for Fragment marketplace items.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from curl_cffi import requests

from FragmentAPI.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    FRAGMENT_BASE_URL,
    ITEM_TYPE_URL_PREFIX,
    VALID_ITEM_TYPES,
)
from FragmentAPI.types.results import BidResult
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_fragment_api,
)
from FragmentAPI.utils.proxy import build_curl_proxy_args
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

logger = logging.getLogger("FragmentAPI")


def _item_page_url(item_type: int, slug: str) -> str:
    """Build the Fragment page URL for an item."""
    prefix = ITEM_TYPE_URL_PREFIX.get(item_type, "username")
    return f"{FRAGMENT_BASE_URL}/{prefix}/{slug}"


async def place_bid(
    client: "FragmentClient",
    item_type: int,
    slug: str,
    bid: int,
) -> BidResult:
    """Place a bid or buy-now on a Fragment marketplace item.

    Args:
        client: Authenticated FragmentClient instance.
        item_type: 1 (username), 3 (number), 5 (gift).
        slug: Item identifier on Fragment.
        bid: Bid amount in GRAM (integer).

    Returns:
        BidResult with transaction details.

    Raises:
        ConfigurationError: If parameters are invalid.
        FragmentAPIError: If Fragment rejects the bid.
    """
    if item_type not in VALID_ITEM_TYPES:
        raise ConfigurationError(ConfigurationError.INVALID_ITEM_TYPE.format(item_type=item_type))
    if not isinstance(bid, int) or bid < 1:
        raise ConfigurationError(ConfigurationError.INVALID_BID_AMOUNT)

    client._require_wallet()

    try:
        page_url = _item_page_url(item_type, slug)
        headers = build_headers(page_url)
        proxy_args = build_curl_proxy_args(client.proxy)

        async with requests.AsyncSession(
            cookies=client.cookies, timeout=client.timeout, impersonate="chrome120",
            **proxy_args,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, page_url, client.timeout, proxy=client.proxy,
            )

            account = await build_account_info(client)
            transaction = await post_fragment_api(
                session, fragment_hash, headers,
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

        logger.info("Placing bid %d GRAM on %s/%s", bid, ITEM_TYPE_URL_PREFIX.get(item_type, ""), slug)
        tx_result = await execute_transaction(client, transaction)

        return BidResult(
            transaction_id=tx_result.tx_hash,
            item_type=item_type,
            slug=slug,
            bid=bid,
            confirm_method=confirm_method,
            confirm_id=confirm_params.get("id"),
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc