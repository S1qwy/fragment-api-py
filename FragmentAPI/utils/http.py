"""Reusable Fragment transport with bounded hash refresh and explicit status handling."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any
from urllib.parse import urlsplit

from curl_cffi import requests

from FragmentAPI.exceptions import (
    AlreadySubscribedError,
    FragmentAPIError,
    FragmentPageError,
    PaidMessageLimitError,
    ParseError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    BASE_HEADERS,
    DEFAULT_TIMEOUT,
    FRAGMENT_API_URL,
    FRAGMENT_BASE_URL,
    HASH_TTL,
)
from FragmentAPI.utils.proxy import build_curl_proxy_args

HASH_RE = re.compile(r"/api\?hash=([a-fA-F0-9]+)")


def build_headers(page_url: str = FRAGMENT_BASE_URL) -> dict[str, str | None]:
    """Build API request headers."""
    return {**BASE_HEADERS, "referer": page_url, "x-aj-referer": page_url}


def validate_page_url(url: str) -> str:
    """Restrict authenticated requests to Fragment itself."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "fragment.com"
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise FragmentAPIError("Authenticated requests require an HTTPS fragment.com URL.")
    return url


def parse_json_response(response: Any, context: str) -> dict[str, Any]:
    """Require a successful HTTP response containing a JSON object."""
    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code, url=str(response.url)
            )
        )
    try:
        result = response.json()
        if not isinstance(result, dict):
            raise TypeError("Expected a JSON object.")
        return result
    except Exception as exc:
        raise ParseError(
            ParseError.UNPARSEABLE.format(context=context, exc=exc)
        ) from exc


def raise_api_error(result: dict[str, Any]) -> None:
    """Map known Fragment failures before callers inspect recipient or invoice fields."""
    if result.get("need_verify"):
        raise VerificationError(VerificationError.KYC_REQUIRED)
    error = result.get("error")
    if not error:
        return
    text = str(error)
    lowered = text.casefold()
    if "already subscribed" in lowered:
        raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
    if "minimum" in lowered and "star" in lowered:
        raise PaidMessageLimitError(
            PaidMessageLimitError.MINIMUM_REQUIRED.format(error=text)
        )
    raise FragmentAPIError(text)


class FragmentTransport:
    """One cookie jar, connection pool, and hash cache per client.

    A rejected hash is refreshed once. Network failures on POST are not
    automatically replayed because the server may already have applied them.
    """

    def __init__(
        self,
        session: requests.AsyncSession,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.session = session
        self.timeout = timeout
        self._hashes: dict[str, tuple[str, float]] = {}
        self._hash_lock = asyncio.Lock()

    def invalidate(self) -> None:
        """Discard session-bound cached hashes."""
        self._hashes.clear()

    async def get_text(self, page_url: str) -> str:
        """Fetch a full page using the existing session."""
        validate_page_url(page_url)
        response = await self.session.get(
            page_url,
            headers={"referer": FRAGMENT_BASE_URL},
            allow_redirects=False,
        )
        if response.status_code in (301, 302, 303, 307, 308):
            raise FragmentPageError(
                FragmentPageError.ITEM_NOT_FOUND.format(url=page_url)
            )
        if response.status_code != 200:
            raise FragmentPageError(
                FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url)
            )
        return response.text

    async def hash(self, page_url: str, force: bool = False) -> str:
        """Fetch or reuse the API hash for a page."""
        validate_page_url(page_url)
        async with self._hash_lock:
            cached = self._hashes.get(page_url)
            if not force and cached and time.monotonic() - cached[1] < HASH_TTL:
                return cached[0]
            text = (await self.get_text(page_url)).replace("\\/", "/")
            match = HASH_RE.search(text)
            if not match:
                raise FragmentPageError(
                    FragmentPageError.HASH_NOT_FOUND.format(url=page_url)
                )
            value = match.group(1)
            self._hashes[page_url] = value, time.monotonic()
            return value

    async def call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        page_url: str = FRAGMENT_BASE_URL,
    ) -> dict[str, Any]:
        """POST once, refreshing once only for an explicit Bad request response."""
        validate_page_url(page_url)
        payload = {**(data or {}), "method": method}
        for attempt in range(2):
            api_hash = await self.hash(page_url, force=attempt == 1)
            response = await self.session.post(
                f"{FRAGMENT_API_URL}?hash={api_hash}",
                headers=build_headers(page_url),
                data=payload,
                allow_redirects=False,
            )
            result = parse_json_response(response, method)
            if str(result.get("error", "")).strip().casefold() != "bad request":
                return result
        return result

    async def page(self, page_url: str) -> dict[str, Any]:
        """Fetch AJAX page data or normalize a full HTML response."""
        validate_page_url(page_url)
        headers = build_headers(page_url)
        headers.pop("content-type", None)
        response = await self.session.get(
            page_url, headers=headers, allow_redirects=False
        )
        if response.status_code in (301, 302, 303, 307, 308):
            raise FragmentPageError(
                FragmentPageError.ITEM_NOT_FOUND.format(url=page_url)
            )
        if response.status_code != 200:
            raise FragmentPageError(
                FragmentPageError.BAD_STATUS.format(status=response.status_code, url=page_url)
            )
        try:
            result = response.json()
        except ValueError:
            text = response.text
            state: dict[str, Any] = {}
            match = re.search(r"ajInit\(", text)
            if match:
                try:
                    embedded, _ = json.JSONDecoder().raw_decode(text[match.end():].lstrip())
                    state = embedded.get("state", {})
                except (ValueError, AttributeError):
                    state = {}
            return {"h": text, "s": state}
        if not isinstance(result, dict):
            raise ParseError("Page response must be a JSON object.")
        return result


async def fetch_fragment_hash(
    cookies: dict[str, Any],
    headers: dict[str, Any],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
    proxy: str | None = None,
) -> str:
    """Compatibility helper for standalone callers."""
    async with requests.AsyncSession(
        cookies=cookies, timeout=timeout, impersonate="chrome",
        **build_curl_proxy_args(proxy),
    ) as session:
        return await FragmentTransport(session, timeout).hash(page_url)


async def fetch_page_ajax(
    cookies: dict[str, Any],
    headers: dict[str, Any],
    page_url: str,
    timeout: float = DEFAULT_TIMEOUT,
    proxy: str | None = None,
) -> dict[str, Any]:
    """Compatibility helper for standalone callers."""
    async with requests.AsyncSession(
        cookies=cookies, timeout=timeout, impersonate="chrome",
        **build_curl_proxy_args(proxy),
    ) as session:
        return await FragmentTransport(session, timeout).page(page_url)


async def post_fragment_api(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    """Compatibility POST helper with one explicit rejected-hash recovery."""
    response = await session.post(
        f"{FRAGMENT_API_URL}?hash={fragment_hash}",
        headers=headers, data=data, allow_redirects=False,
    )
    result = parse_json_response(response, str(data.get("method", "request")))
    if str(result.get("error", "")).strip().casefold() == "bad request":
        return await FragmentTransport(session).call(
            str(data["method"]),
            {key: value for key, value in data.items() if key != "method"},
            str(headers.get("referer", FRAGMENT_BASE_URL)),
        )
    return result


post_FragmentAPI = post_fragment_api