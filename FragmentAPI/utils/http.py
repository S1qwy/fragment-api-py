"""
HTTP utilities for Fragment API requests.

Handles page loading, API hash extraction, and Fragment API POST requests.
Uses curl_cffi for browser impersonation to bypass anti-bot protection.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from curl_cffi import requests

from FragmentAPI.exceptions import (
    FragmentPageError,
    ParseError,
)
from FragmentAPI.types.constants import (
    BASE_HEADERS,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
)

logger = logging.getLogger("FragmentAPI")


def build_headers(page_url: str = FRAGMENT_BASE_URL) -> dict[str, str]:
    """Build HTTP headers for a specific Fragment page."""
    return {
        **BASE_HEADERS,
        "referer": page_url,
        "x-aj-referer": page_url,
    }


def _make_ajax_headers(headers: dict[str, str]) -> dict[str, str]:
    """Build headers for AJAX page navigation."""
    h = dict(headers)
    h["accept"] = "application/json, text/javascript, */*; q=0.01"
    h["x-requested-with"] = "XMLHttpRequest"
    h.pop("content-type", None)
    return h


def _make_full_page_headers() -> dict[str, str]:
    """Build headers for full HTML page load."""
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": BASE_HEADERS["user-agent"],
    }


def _extract_hash_from_text(text: str, url: str) -> str:
    """Extract API hash from any text containing the fragment API URL."""
    match = re.search(r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", text)
    if not match:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=url)
        )
    return match.group(1)


def _parse_response(response: Any, context: str) -> dict[str, Any]:
    """Parse JSON from HTTP response."""
    try:
        return response.json()
    except Exception as exc:
        raise ParseError(
            ParseError.UNPARSEABLE.format(context=context, exc=exc)
        ) from exc


async def fetch_page_ajax(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Fetch a Fragment page via AJAX navigation.

    Fragment returns JSON with keys (v, t, h, j, s, rc) when the
    request includes X-Requested-With: XMLHttpRequest header.

    Args:
        cookies: Fragment session cookies.
        headers: HTTP headers with referer set.
        page_url: Full URL of the Fragment page.
        timeout: HTTP request timeout in seconds.

    Returns:
        Parsed JSON dict from Fragment response.

    Raises:
        FragmentPageError: If page returns non-200 status or redirect.
    """
    ajax_headers = _make_ajax_headers(headers)
    logger.debug("AJAX fetch: %s", page_url)

    async with requests.AsyncSession(
        cookies=cookies,
        timeout=timeout,
        impersonate="chrome120",
        allow_redirects=True,
    ) as session:
        response = await session.get(page_url, headers=ajax_headers)

    if response.status_code == 302:
        raise FragmentPageError(
            FragmentPageError.ITEM_NOT_FOUND.format(url=page_url)
        )
    if response.status_code != 200:
        logger.error("Fragment returned HTTP %d for %s", response.status_code, page_url)
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url)
        )
    return _parse_response(response, f"page {page_url}")


async def fetch_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Fetch the API hash from Fragment homepage via full page load.

    The API hash is required for all Fragment API POST requests
    and changes periodically.

    Args:
        cookies: Fragment session cookies.
        headers: HTTP headers (used for reference only).
        page_url: Page URL for context in error messages.
        timeout: HTTP request timeout in seconds.

    Returns:
        Hex string API hash extracted from page HTML.

    Raises:
        FragmentPageError: If page cannot be loaded or hash not found.
    """
    full_headers = _make_full_page_headers()
    logger.debug("Fetching Fragment API hash from homepage")

    async with requests.AsyncSession(
        cookies=cookies,
        timeout=timeout,
        impersonate="chrome120",
    ) as session:
        response = await session.get("https://fragment.com", headers=full_headers)

    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url="https://fragment.com",
            )
        )
    return _extract_hash_from_text(response.text, "https://fragment.com")


async def post_fragment_api(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, str],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST a request to the Fragment API.

    Args:
        session: Active curl_cffi async session.
        fragment_hash: API hash from fetch_fragment_hash.
        headers: HTTP headers with referer.
        data: Form data dict with 'method' key.

    Returns:
        Parsed JSON response from Fragment API.
    """
    method_name = data.get("method", "unknown")
    logger.debug("POST Fragment API method=%s", method_name)

    resp = await session.post(
        f"{FRAGMENT_BASE_URL}/api?hash={fragment_hash}",
        headers=headers,
        data=data,
    )
    return _parse_response(resp, method_name)


post_FragmentAPI = post_fragment_api