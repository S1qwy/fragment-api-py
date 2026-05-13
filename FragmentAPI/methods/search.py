'''
Marketplace search methods — async only.
'''

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

import httpx

from FragmentAPI.exceptions import (
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
)
from FragmentAPI.types.constants import (
    FRAGMENT_BASE_URL,
    GIFTS_PAGE,
    NUMBERS_PAGE,
)
from FragmentAPI.types.results import (
    GiftsResult,
    NumbersResult,
    UsernamesResult,
)
from FragmentAPI.utils.html import (
    parse_auction_rows,
    parse_gift_items,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


def _build_search_data(
    query: str,
    item_type: str,
    sort: str | None = None,
    filter_: str | None = None,
    offset_id: str | None = None,
) -> dict[str, Any]:
    '''Build search request data dict.'''
    data: dict[str, Any] = {
        "method": "searchAuctions",
        "type": item_type,
        "query": query,
    }
    if sort is not None:
        data["sort"] = sort
    if filter_ is not None:
        data["filter"] = filter_
    if offset_id is not None:
        data["offset_id"] = offset_id
    return data


async def search_usernames(
    client: "FragmentClient",
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult:
    '''
    Search Fragment marketplace for Telegram usernames.

    Args:
        client: Authenticated FragmentClient instance.
        query: Search text. Empty string browses all.
        sort: "price_desc", "price_asc", "listed", or "ending".
        filter: "auction", "sale", "sold", or "" (available).
        offset_id: Pagination cursor from previous result.

    Returns:
        UsernamesResult with items and next_offset_id.
    '''
    try:
        headers = build_headers(FRAGMENT_BASE_URL)
        data = _build_search_data(
            query,
            "usernames",
            sort,
            filter,
            offset_id,
        )

        async with httpx.AsyncClient(
            cookies=client.cookies,
            timeout=client.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies,
                headers,
                FRAGMENT_BASE_URL,
                client.timeout,
            )
            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                data,
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_oid = str(raw_noi) if raw_noi else None

        return UsernamesResult(
            items=items,
            next_offset_id=next_oid,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc


async def search_numbers(
    client: "FragmentClient",
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> NumbersResult:
    '''
    Search Fragment marketplace for anonymous Telegram numbers.

    Args:
        client: Authenticated FragmentClient instance.
        query: Search text. Empty string browses all.
        sort: "price_desc", "price_asc", "listed", or "ending".
        filter: "auction", "sale", "sold", or "" (available).
        offset_id: Pagination cursor from previous result.

    Returns:
        NumbersResult with items and next_offset_id.
    '''
    try:
        headers = build_headers(NUMBERS_PAGE)
        data = _build_search_data(
            query,
            "numbers",
            sort,
            filter,
            offset_id,
        )

        async with httpx.AsyncClient(
            cookies=client.cookies,
            timeout=client.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies,
                headers,
                NUMBERS_PAGE,
                client.timeout,
            )
            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                data,
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_oid = str(raw_noi) if raw_noi else None

        return NumbersResult(
            items=items,
            next_offset_id=next_oid,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc


async def search_gifts(
    client: "FragmentClient",
    query: str = "",
    collection: str | None = None,
    sort: str | None = None,
    filter: str | None = None,
    view: str | None = None,
    attr: dict[str, list[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult:
    '''
    Search Fragment gifts marketplace.

    Args:
        client: Authenticated FragmentClient instance.
        query: Search text. Empty string browses all.
        collection: Gift collection slug.
        sort: Sort order.
        filter: Filter value.
        view: Active attribute tab name.
        attr: Attribute filters.
        offset: Page offset from previous result.

    Returns:
        GiftsResult with items and next_offset.
    '''
    data: dict[str, Any] = {
        "method": "searchAuctions",
        "type": "gifts",
        "query": query,
    }
    if collection is not None:
        data["collection"] = collection
    if sort is not None:
        data["sort"] = sort
    if filter is not None:
        data["filter"] = filter
    if view is not None:
        data["view"] = view
    if attr is not None:
        for trait, values in attr.items():
            data[f"attr[{trait}]"] = values
    if offset is not None:
        data["offset"] = offset

    try:
        headers = build_headers(GIFTS_PAGE)

        async with httpx.AsyncClient(
            cookies=client.cookies,
            timeout=client.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies,
                headers,
                GIFTS_PAGE,
                client.timeout,
            )
            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                data,
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items, next_offset = parse_gift_items(result.get("html") or "")

        return GiftsResult(
            items=items,
            next_offset=next_offset,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc