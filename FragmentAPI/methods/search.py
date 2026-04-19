"""
Marketplace search methods - async and sync
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
from FragmentAPI.types.results import GiftsResult, NumbersResult, UsernamesResult
from FragmentAPI.utils.html import parse_auction_rows, parse_gift_items
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    fetch_fragment_hash_sync,
    post_FragmentAPI,
    post_FragmentAPI_sync,
)

if TYPE_CHECKING:
    from FragmentAPI.async_client import AsyncFragmentClient
    from FragmentAPI.client import FragmentClient


def _build_search_data(
    query: str,
    item_type: str,
    sort: str | None = None,
    filter_: str | None = None,
    offset_id: str | None = None,
) -> dict[str, Any]:
    """Build search request data dict.

    Args:
        query: Search text.
        item_type: Item type ("usernames", "numbers", "gifts").
        sort: Sort order.
        filter_: Filter value.
        offset_id: Pagination cursor.

    Returns:
        Data dict for Fragment API request.
    """
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
    client: "AsyncFragmentClient",
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult:
    """Search Fragment marketplace for Telegram usernames (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        query: Search text (e.g. "durov"). Empty string browses all.
        sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
        filter: Filter - "auction", "sale", "sold", or "" (available).
        offset_id: Pagination cursor from previous result.

    Returns:
        UsernamesResult with items and next_offset_id.

    Raises:
        FragmentAPIError: If Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    try:
        headers = build_headers(FRAGMENT_BASE_URL)
        data = _build_search_data(query, "usernames", sort, filter, offset_id)

        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, FRAGMENT_BASE_URL, client.timeout
            )
            result = await post_FragmentAPI(
                session, fragment_hash, headers, data
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_oid = str(raw_noi) if raw_noi else None
        return UsernamesResult(items=items, next_offset_id=next_oid)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def search_usernames_sync(
    client: "FragmentClient",
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult:
    """Search Fragment marketplace for Telegram usernames (sync).

    Args:
        client: Authenticated FragmentClient instance.
        query: Search text. Empty string browses all.
        sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
        filter: Filter - "auction", "sale", "sold", or "" (available).
        offset_id: Pagination cursor from previous result.

    Returns:
        UsernamesResult with items and next_offset_id.
    """
    try:
        headers = build_headers(FRAGMENT_BASE_URL)
        data = _build_search_data(query, "usernames", sort, filter, offset_id)

        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, FRAGMENT_BASE_URL, client.timeout
            )
            result = post_FragmentAPI_sync(
                session, fragment_hash, headers, data
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_oid = str(raw_noi) if raw_noi else None
        return UsernamesResult(items=items, next_offset_id=next_oid)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


async def search_numbers(
    client: "AsyncFragmentClient",
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> NumbersResult:
    """Search Fragment marketplace for anonymous Telegram numbers (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        query: Search text (e.g. "888"). Empty string browses all.
        sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
        filter: Filter - "auction", "sale", "sold", or "" (available).
        offset_id: Pagination cursor from previous result.

    Returns:
        NumbersResult with items and next_offset_id.
    """
    try:
        headers = build_headers(NUMBERS_PAGE)
        data = _build_search_data(query, "numbers", sort, filter, offset_id)

        async with httpx.AsyncClient(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, NUMBERS_PAGE, client.timeout
            )
            result = await post_FragmentAPI(
                session, fragment_hash, headers, data
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_oid = str(raw_noi) if raw_noi else None
        return NumbersResult(items=items, next_offset_id=next_oid)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def search_numbers_sync(
    client: "FragmentClient",
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> NumbersResult:
    """Search Fragment marketplace for anonymous Telegram numbers (sync).

    Args:
        client: Authenticated FragmentClient instance.
        query: Search text. Empty string browses all.
        sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
        filter: Filter - "auction", "sale", "sold", or "" (available).
        offset_id: Pagination cursor from previous result.

    Returns:
        NumbersResult with items and next_offset_id.
    """
    try:
        headers = build_headers(NUMBERS_PAGE)
        data = _build_search_data(query, "numbers", sort, filter, offset_id)

        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, NUMBERS_PAGE, client.timeout
            )
            result = post_FragmentAPI_sync(
                session, fragment_hash, headers, data
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items = parse_auction_rows(result.get("html") or "")
        raw_noi = result.get("next_offset_id")
        next_oid = str(raw_noi) if raw_noi else None
        return NumbersResult(items=items, next_offset_id=next_oid)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


async def search_gifts(
    client: "AsyncFragmentClient",
    query: str = "",
    collection: str | None = None,
    sort: str | None = None,
    filter: str | None = None,
    view: str | None = None,
    attr: dict[str, list[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult:
    """Search Fragment gifts marketplace (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        query: Search text. Empty string browses all.
        collection: Gift collection slug (e.g. "artisanbrick").
        sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
        filter: Filter - "auction", "sale", "sold", or "" (available).
        view: Active attribute tab name (e.g. "Model", "Backdrop").
        attr: Attribute filters mapping trait name to accepted values.
        offset: Page offset from previous GiftsResult.

    Returns:
        GiftsResult with items and next_offset.
    """
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
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, GIFTS_PAGE, client.timeout
            )
            result = await post_FragmentAPI(
                session, fragment_hash, headers, data
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items, next_offset = parse_gift_items(result.get("html") or "")
        return GiftsResult(items=items, next_offset=next_offset)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


def search_gifts_sync(
    client: "FragmentClient",
    query: str = "",
    collection: str | None = None,
    sort: str | None = None,
    filter: str | None = None,
    view: str | None = None,
    attr: dict[str, list[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult:
    """Search Fragment gifts marketplace (sync).

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
    """
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
        with httpx.Client(
            cookies=client.cookies, timeout=client.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                client.cookies, headers, GIFTS_PAGE, client.timeout
            )
            result = post_FragmentAPI_sync(
                session, fragment_hash, headers, data
            )

        if result.get("error"):
            raise FragmentAPIError(result["error"])

        items, next_offset = parse_gift_items(result.get("html") or "")
        return GiftsResult(items=items, next_offset=next_offset)

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc
