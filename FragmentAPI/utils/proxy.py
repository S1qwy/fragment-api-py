"""
Proxy configuration utilities for Fragment API requests.

Supports HTTP, HTTPS, SOCKS4, and SOCKS5 proxies with optional authentication.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from FragmentAPI.exceptions import ConfigurationError

logger = logging.getLogger("FragmentAPI")

PROXY_PATTERN = re.compile(
    r"^(https?|socks[45])://"
    r"(?:([^:@]+):([^@]+)@)?"
    r"([^:]+):(\d+)$",
    re.IGNORECASE,
)

SUPPORTED_SCHEMES = frozenset({"http", "https", "socks4", "socks5"})


def parse_proxy(proxy: str) -> dict[str, Any]:
    """Parse a proxy URL string into components.

    Args:
        proxy: Proxy URL (e.g. "socks5://user:pass@host:port").

    Returns:
        Dict with keys: scheme, host, port, username, password, url.

    Raises:
        ConfigurationError: If proxy format is invalid.
    """
    match = PROXY_PATTERN.match(proxy.strip())
    if not match:
        raise ConfigurationError(ConfigurationError.INVALID_PROXY.format(proxy=proxy))

    scheme = match.group(1).lower()
    username = match.group(2)
    password = match.group(3)
    host = match.group(4)
    port = int(match.group(5))

    if scheme not in SUPPORTED_SCHEMES:
        raise ConfigurationError(ConfigurationError.INVALID_PROXY.format(proxy=proxy))

    return {
        "scheme": scheme,
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "url": proxy.strip(),
    }


def build_curl_proxy_args(proxy: str | None) -> dict[str, Any]:
    """Build proxy keyword arguments for curl_cffi sessions.

    Args:
        proxy: Proxy URL string or None.

    Returns:
        Dict of keyword arguments to pass to curl_cffi AsyncSession.
    """
    if not proxy:
        return {}

    parsed = parse_proxy(proxy)
    logger.debug("Configuring proxy: %s://%s:%d", parsed["scheme"], parsed["host"], parsed["port"])

    return {"proxy": parsed["url"]}