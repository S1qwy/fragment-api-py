"""Compatibility marketplace bid entry point."""

from __future__ import annotations

from typing import Any


async def place_bid(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Place a bid through the client-owned transport."""
    return await client.place_bid(*args, **kwargs)


__all__ = ["place_bid"]