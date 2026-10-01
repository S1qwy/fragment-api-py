"""Compatibility entry points for the unified client purchase engine."""

from __future__ import annotations

from typing import Any

from FragmentAPI.utils.validation import normalize_payment_method

_normalize_payment_method = normalize_payment_method


async def purchase(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute a single or batch purchase."""
    return await client.purchase(*args, **kwargs)


async def batch_purchase(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute an ordered purchase batch."""
    return await client.batch_purchase(*args, **kwargs)


async def purchase_stars(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Purchase Stars."""
    return await client.purchase_stars(*args, **kwargs)


async def purchase_premium(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Gift Premium."""
    return await client.purchase_premium(*args, **kwargs)


async def topup_gram(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Top up a recipient's Ads balance."""
    return await client.topup_gram(*args, **kwargs)


async def topup_ton(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Alias for native Ads top-up."""
    return await client.topup_ton(*args, **kwargs)


__all__ = [
    "purchase", "batch_purchase", "purchase_stars",
    "purchase_premium", "topup_gram", "topup_ton",
]