"""Compatibility marketplace and account utility entry points."""

from __future__ import annotations

from typing import Any


async def make_offer(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Make an item offer."""
    return await client.make_offer(*args, **kwargs)


async def cancel_auction(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Cancel an auction."""
    return await client.cancel_auction(*args, **kwargs)


async def subscribe_to_item(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Subscribe to item updates."""
    return await client.subscribe_to_item(*args, **kwargs)


async def unsubscribe_from_item(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Unsubscribe from item updates."""
    return await client.unsubscribe_from_item(*args, **kwargs)


async def init_ads_withdrawal(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Initialize Ads withdrawal."""
    return await client.init_ads_withdrawal(*args, **kwargs)


async def confirm_ads_withdrawal(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Confirm Ads withdrawal."""
    return await client.confirm_ads_withdrawal(*args, **kwargs)


async def get_gateway_price(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Quote Gateway credits."""
    return await client.get_gateway_price(*args, **kwargs)


async def recharge_gateway(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Recharge Gateway credits."""
    return await client.recharge_gateway(*args, **kwargs)


async def recharge_ads(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Recharge an Ads account."""
    return await client.recharge_ads(*args, **kwargs)


__all__ = [
    "make_offer", "cancel_auction", "subscribe_to_item", "unsubscribe_from_item",
    "init_ads_withdrawal", "confirm_ads_withdrawal", "get_gateway_price",
    "recharge_gateway", "recharge_ads",
]