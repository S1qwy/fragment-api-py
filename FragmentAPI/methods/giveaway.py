"""Compatibility giveaway entry points."""

from __future__ import annotations

from typing import Any

from FragmentAPI.utils.validation import stars_giveaway

_validate_stars_giveaway = stars_giveaway


async def giveaway_stars(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a Stars giveaway."""
    return await client.giveaway_stars(*args, **kwargs)


async def giveaway_premium(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a Premium giveaway."""
    return await client.giveaway_premium(*args, **kwargs)


__all__ = ["giveaway_stars", "giveaway_premium"]