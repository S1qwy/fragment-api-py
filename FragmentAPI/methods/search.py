"""Compatibility marketplace search entry points."""

from __future__ import annotations

from typing import Any


async def search_usernames(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Search username listings."""
    return await client.search_usernames(*args, **kwargs)


async def search_numbers(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Search number listings."""
    return await client.search_numbers(*args, **kwargs)


async def search_gifts(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Search gift listings."""
    return await client.search_gifts(*args, **kwargs)


async def get_gift_filters(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Read gift filters."""
    return await client.get_gift_filters(*args, **kwargs)


__all__ = [
    "search_usernames", "search_numbers", "search_gifts", "get_gift_filters",
]