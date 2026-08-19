"""
HTTP utilities for Fragment API requests.

Handles page loading, API hash extraction, and Fragment API POST requests.
Uses curl_cffi for browser impersonation to bypass anti-bot protection.
Supports proxy configuration and automatic retry with exponential backoff.
"""

from __future__ import annotations

import logging
import re
import time
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
from FragmentAPI.utils.proxy import build_curl_proxy_args
from FragmentAPI.utils.retry import with_retry

logger = logging.getLogger("FragmentAPI")

_hash_cache: dict[str, tuple[str, float]] = {}
_HASH_TTL: float = 120.0


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


@with_retry(context="fetch_page_ajax")
async def fetch_page_ajax(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
    proxy: str | None = None,
) -> dict[str, Any]:
    """Fetch a Fragment page via AJAX navigation with automatic retry.

    Args:
        cookies: Fragment session cookies.
        headers: HTTP headers with referer set.
        page_url: Full URL of the Fragment page.
        timeout: HTTP request timeout in seconds.
        proxy: Optional proxy URL string.

    Returns:
        Parsed JSON dict from Fragment response.

    Raises:
        FragmentPageError: If page returns non-200 status or redirect.
    """
    ajax_headers = _make_ajax_headers(headers)
    proxy_args = build_curl_proxy_args(proxy)
    logger.debug("AJAX fetch: %s", page_url)

    async with requests.AsyncSession(
        cookies=cookies,
        timeout=timeout,
        impersonate="chrome120",
        allow_redirects=True,
        **proxy_args,
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


@with_retry(context="fetch_fragment_hash")
async def fetch_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
    proxy: str | None = None,
) -> str:
    """Fetch the API hash from Fragment homepage with caching and retry.

    The API hash is required for all Fragment API POST requests
    and changes periodically. Results are cached for 120 seconds.

    Args:
        cookies: Fragment session cookies.
        headers: HTTP headers (used for reference only).
        page_url: Page URL for context in error messages.
        timeout: HTTP request timeout in seconds.
        proxy: Optional proxy URL string.

    Returns:
        Hex string API hash extracted from page HTML.
    """
    cache_key = str(sorted(cookies.items()))
    now = time.monotonic()

    cached = _hash_cache.get(cache_key)
    if cached and (now - cached[1]) < _HASH_TTL:
        logger.debug("Using cached Fragment API hash")
        return cached[0]

    full_headers = _make_full_page_headers()
    proxy_args = build_curl_proxy_args(proxy)
    logger.debug("Fetching Fragment API hash from homepage")

    async with requests.AsyncSession(
        cookies=cookies,
        timeout=timeout,
        impersonate="chrome120",
        **proxy_args,
    ) as session:
        response = await session.get("https://fragment.com", headers=full_headers)

    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url="https://fragment.com",
            )
        )

    api_hash = _extract_hash_from_text(response.text, "https://fragment.com")
    _hash_cache[cache_key] = (api_hash, now)
    return api_hash


@with_retry(context="post_fragment_api")
async def post_fragment_api(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, str],
    data: dict[str, Any],
) -> dict[str, Any]:
    """POST a request to the Fragment API with automatic retry.

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