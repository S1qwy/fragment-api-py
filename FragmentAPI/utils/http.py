"""
HTTP utilities for Fragment API requests - both sync and async
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from FragmentAPI.exceptions import (
    FragmentPageError,
    ParseError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    BASE_HEADERS,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
)


def build_headers(page_url: str = FRAGMENT_BASE_URL) -> dict[str, str]:
    """Build HTTP headers for a specific Fragment page.

    Args:
        page_url: Fragment page URL to set as referer.

    Returns:
        Complete headers dict with referer and x-aj-referer set.
    """
    return {**BASE_HEADERS, "referer": page_url, "x-aj-referer": page_url}


def _make_page_headers(headers: dict[str, str]) -> dict[str, str]:
    """Build headers for fetching a Fragment HTML page (not XHR).

    Args:
        headers: Base headers for the page.

    Returns:
        Modified headers suitable for document navigation.
    """
    page_headers = {
        k: v
        for k, v in headers.items()
        if k
        not in (
            "accept",
            "accept-encoding",
            "content-type",
            "x-requested-with",
            "x-aj-referer",
        )
    }
    page_headers.update(
        {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "referer": f"{FRAGMENT_BASE_URL}/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "upgrade-insecure-requests": "1",
        }
    )
    return page_headers


def _extract_hash(text: str, url: str) -> str:
    """Extract API hash from Fragment page HTML.

    Args:
        text: HTML response body.
        url: Page URL for error messages.

    Returns:
        Extracted hash string.

    Raises:
        FragmentPageError: If hash is not found.
    """
    match = re.search(
        r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", text
    )
    if not match:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=url)
        )
    return match.group(1)


def _parse_response(response: httpx.Response, context: str) -> dict[str, Any]:
    """Parse JSON from httpx response.

    Args:
        response: HTTP response object.
        context: Method name for error messages.

    Returns:
        Parsed JSON dict.

    Raises:
        ParseError: If JSON parsing fails.
    """
    try:
        return response.json()
    except Exception as exc:
        raise ParseError(
            ParseError.UNPARSEABLE.format(context=context, exc=exc)
        ) from exc


async def fetch_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Fetch the API hash from a Fragment page (async).

    Fragment embeds a short-lived hash in each page's HTML that must be
    included in every subsequent API request.

    Args:
        cookies: Active Fragment session cookies.
        headers: Base headers for the page.
        page_url: URL of the Fragment page.
        timeout: HTTP timeout in seconds.

    Returns:
        Lowercase hex hash string.

    Raises:
        FragmentPageError: If page returns non-200 or hash not found.
    """
    page_headers = _make_page_headers(headers)
    async with httpx.AsyncClient(
        cookies=cookies, timeout=timeout
    ) as session:
        response = await session.get(page_url, headers=page_headers)

    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=page_url
            )
        )
    return _extract_hash(response.text, page_url)


def fetch_fragment_hash_sync(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Fetch the API hash from a Fragment page (sync).

    Args:
        cookies: Active Fragment session cookies.
        headers: Base headers for the page.
        page_url: URL of the Fragment page.
        timeout: HTTP timeout in seconds.

    Returns:
        Lowercase hex hash string.

    Raises:
        FragmentPageError: If page returns non-200 or hash not found.
    """
    page_headers = _make_page_headers(headers)
    with httpx.Client(cookies=cookies, timeout=timeout) as session:
        response = session.get(page_url, headers=page_headers)

    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=page_url
            )
        )
    return _extract_hash(response.text, page_url)


async def post_FragmentAPI(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST a request to the Fragment API (async).

    Args:
        session: Active httpx async session with cookies.
        fragment_hash: Short-lived hash from Fragment page.
        headers: Page-specific HTTP headers.
        data: Form data payload with 'method' key.

    Returns:
        Parsed API response dict.
    """
    resp = await session.post(
        f"{FRAGMENT_BASE_URL}/api?hash={fragment_hash}",
        headers=headers,
        data=data,
    )
    return _parse_response(resp, data.get("method", "request"))


def post_FragmentAPI_sync(
    session: httpx.Client,
    fragment_hash: str,
    headers: dict[str, str],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST a request to the Fragment API (sync).

    Args:
        session: Active httpx sync session with cookies.
        fragment_hash: Short-lived hash from Fragment page.
        headers: Page-specific HTTP headers.
        data: Form data payload with 'method' key.

    Returns:
        Parsed API response dict.
    """
    resp = session.post(
        f"{FRAGMENT_BASE_URL}/api?hash={fragment_hash}",
        headers=headers,
        data=data,
    )
    return _parse_response(resp, data.get("method", "request"))
