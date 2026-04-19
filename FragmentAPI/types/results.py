"""
Result dataclasses for Fragment API operations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WalletInfo:
    """Wallet state information."""

    address: str
    state: str
    balance: float

    def __repr__(self) -> str:
        return (
            f"WalletInfo(address='{self.address}', "
            f"state='{self.state}', balance={self.balance} TON)"
        )


@dataclass
class PremiumResult:
    """Result of a successful Telegram Premium gift."""

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return (
            f"PremiumResult(username='{self.username}', "
            f"amount={self.amount} months, tx='{self.transaction_id}')"
        )


@dataclass
class StarsResult:
    """Result of a successful Telegram Stars purchase."""

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return (
            f"StarsResult(username='{self.username}', "
            f"amount={self.amount} stars, tx='{self.transaction_id}')"
        )


@dataclass
class AdsTopupResult:
    """Result of a successful Telegram Ads TON top-up."""

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return (
            f"AdsTopupResult(username='{self.username}', "
            f"amount={self.amount} TON, tx='{self.transaction_id}')"
        )


@dataclass
class GiveawayStarsResult:
    """Result of a successful Stars giveaway."""

    transaction_id: str
    channel: str
    winners: int
    amount: int

    def __repr__(self) -> str:
        return (
            f"GiveawayStarsResult(channel='{self.channel}', "
            f"winners={self.winners}, amount={self.amount} stars, "
            f"tx='{self.transaction_id}')"
        )


@dataclass
class GiveawayPremiumResult:
    """Result of a successful Premium giveaway."""

    transaction_id: str
    channel: str
    winners: int
    amount: int

    def __repr__(self) -> str:
        return (
            f"GiveawayPremiumResult(channel='{self.channel}', "
            f"winners={self.winners}, amount={self.amount} months, "
            f"tx='{self.transaction_id}')"
        )


@dataclass
class UsernamesResult:
    """
    Result of username marketplace search.

    Each dict in items has keys:
    - slug: URL path (e.g. "username/durov")
    - name: Display value (e.g. "@durov")
    - status: Fragment label (e.g. "On auction", "For sale")
    - price: Price in TON as string (e.g. "7.00"), or None
    - date: ISO 8601 datetime, or None
    """

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return (
            f"UsernamesResult(items={len(self.items)}, "
            f"next_offset_id={self.next_offset_id!r})"
        )


@dataclass
class NumbersResult:
    """
    Result of anonymous numbers marketplace search.

    Each dict in items has keys:
    - slug: URL path (e.g. "number/8880000111")
    - name: Display value (e.g. "+888 0000 111")
    - status: Fragment label (e.g. "On auction", "For sale")
    - price: Price in TON as string, or None
    - date: ISO 8601 datetime, or None
    """

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return (
            f"NumbersResult(items={len(self.items)}, "
            f"next_offset_id={self.next_offset_id!r})"
        )


@dataclass
class GiftsResult:
    """
    Result of gifts marketplace search.

    Each dict in items has keys:
    - slug: URL path (e.g. "gift/plushpepe-1821")
    - name: Display name (e.g. "Plush Pepe #1821")
    - status: Fragment label (e.g. "Sold", "For sale")
    - price: Price in TON as string, or None
    - date: ISO 8601 datetime, or None
    """

    items: list[dict[str, Any]]
    next_offset: int | None

    def __repr__(self) -> str:
        return (
            f"GiftsResult(items={len(self.items)}, "
            f"next_offset={self.next_offset!r})"
        )
