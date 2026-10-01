"""Proxy URL parsing and curl configuration."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from FragmentAPI.exceptions import ConfigurationError


def parse_proxy(proxy: str) -> dict[str, Any]:
    """Validate an HTTP or SOCKS proxy without exposing credentials in errors."""
    try:
        parsed = urlsplit(proxy.strip())
        if parsed.scheme.lower() not in {"http", "https", "socks4", "socks5", "socks5h"}:
            raise ValueError
        if not parsed.hostname or parsed.port is None or not 1 <= parsed.port <= 65535:
            raise ValueError
        return {
            "scheme": parsed.scheme.lower(),
            "host": parsed.hostname,
            "port": parsed.port,
            "username": parsed.username,
            "password": parsed.password,
            "url": proxy.strip(),
        }
    except (ValueError, AttributeError) as exc:
        raise ConfigurationError(ConfigurationError.INVALID_PROXY) from exc


def build_curl_proxy_args(proxy: str | None) -> dict[str, Any]:
    """Return curl session proxy arguments."""
    return {"proxy": parse_proxy(proxy)["url"]} if proxy else {}