'''
HTTP utilities for Fragment API requests - both sync and async
'''

from __future__ import annotations

import re
from typing import Any

import httpx

from FragmentAPI.exceptions import (
    FragmentPageError,
    ParseError,
)
from FragmentAPI.types.constants import (
    BASE_HEADERS,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
)


def build_headers(page_url: str = FRAGMENT_BASE_URL) -> dict[str, str]:
    '''Build HTTP headers for a specific Fragment page.'''
    return {**BASE_HEADERS, "referer": page_url, "x-aj-referer": page_url}


def _make_ajax_headers(headers: dict[str, str]) -> dict[str, str]:
    '''Build headers for AJAX page navigation (returns JSON not full HTML).'''
    h = dict(headers)
    h["accept"] = "application/json, text/javascript, */*; q=0.01"
    h["x-requested-with"] = "XMLHttpRequest"
    h.pop("content-type", None)
    return h


def _make_full_page_headers() -> dict[str, str]:
    '''Build headers for full HTML page load (auth flow).'''
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": BASE_HEADERS["user-agent"],
    }


def _extract_hash_from_text(text: str, url: str) -> str:
    '''Extract API hash from any text containing the fragment API URL.'''
    match = re.search(
        r"(?:https://fragment\.com)?/api\?hash=([a-f0-9]+)", text
    )
    if not match:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=url)
        )
    return match.group(1)


def _extract_hash_from_ajax(data: dict[str, Any], url: str) -> str:
    '''Extract API hash from AJAX JSON response.'''
    js_content = data.get("j", "")
    html_content = data.get("h", "")
    combined = js_content + html_content
    return _extract_hash_from_text(combined, url)


def _parse_response(response: httpx.Response, context: str) -> dict[str, Any]:
    '''Parse JSON from httpx response.'''
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
    '''Fetch a Fragment page via AJAX navigation (async).

    Fragment returns JSON with keys: v, t, h, j, s, rc
    when the request includes X-Requested-With: XMLHttpRequest
    and x-aj-referer header.
    '''
    ajax_headers = _make_ajax_headers(headers)
    async with httpx.AsyncClient(
        cookies=cookies, timeout=timeout, follow_redirects=False
    ) as session:
        response = await session.get(page_url, headers=ajax_headers)

    if response.status_code == 302:
        raise FragmentPageError(
            FragmentPageError.ITEM_NOT_FOUND.format(url=page_url)
        )
    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=page_url
            )
        )
    return _parse_response(response, f"page {page_url}")


def fetch_page_ajax_sync(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    '''Fetch a Fragment page via AJAX navigation (sync).'''
    ajax_headers = _make_ajax_headers(headers)
    with httpx.Client(
        cookies=cookies, timeout=timeout, follow_redirects=False
    ) as session:
        response = session.get(page_url, headers=ajax_headers)

    if response.status_code == 302:
        raise FragmentPageError(
            FragmentPageError.ITEM_NOT_FOUND.format(url=page_url)
        )
    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=page_url
            )
        )
    return _parse_response(response, f"page {page_url}")


async def fetch_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    '''Fetch the API hash from a Fragment page via AJAX (async).'''
    return await fetch_fragment_hash_from_full_page(cookies, 'https://fragment.com', timeout)


def fetch_fragment_hash_sync(
    cookies: dict[str, Any],
    headers: dict[str, str],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    '''Fetch the API hash from a Fragment page via AJAX (sync).'''
    return fetch_fragment_hash_from_full_page_sync(cookies, 'https://fragment.com', timeout)


async def fetch_fragment_hash_from_full_page(
    cookies: dict[str, Any],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    '''Fetch hash from full HTML page load (for auth flow, async).'''
    headers = _make_full_page_headers()
    async with httpx.AsyncClient(
        cookies=cookies, timeout=timeout
    ) as session:
        response = await session.get(page_url, headers=headers)
    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=page_url
            )
        )
    return _extract_hash_from_text(response.text, page_url)


def fetch_fragment_hash_from_full_page_sync(
    cookies: dict[str, Any],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    '''Fetch hash from full HTML page load (for auth flow, sync).'''
    headers = _make_full_page_headers()
    with httpx.Client(
        cookies=cookies, timeout=timeout
    ) as session:
        response = session.get(page_url, headers=headers)
    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=page_url
            )
        )
    return _extract_hash_from_text(response.text, page_url)


async def post_FragmentAPI(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
    data: dict[str, Any],
) -> dict[str, Any]:
    '''POST a request to the Fragment API (async).'''
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
    '''POST a request to the Fragment API (sync).'''
    resp = session.post(
        f"{FRAGMENT_BASE_URL}/api?hash={fragment_hash}",
        headers=headers,
        data=data,
    )
    return _parse_response(resp, data.get("method", "request"))