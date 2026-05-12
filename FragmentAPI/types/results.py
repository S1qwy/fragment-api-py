'''
Result dataclasses for Fragment API operations
'''

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WalletInfo:
    '''Wallet state information.'''

    address: str
    state: str
    balance_ton: float
    balance_usdt: float

    def __repr__(self) -> str:
        return (
            f"WalletInfo(address='{self.address}', "
            f"state='{self.state}', balance_ton={self.balance_ton}, "
            f"balance_usdt={self.balance_usdt})"
        )


@dataclass
class PremiumResult:
    '''Result of a successful Telegram Premium gift.'''

    transaction_id: str
    username: str
    amount: int
    payment_method: str = "ton"

    def __repr__(self) -> str:
        return (
            f"PremiumResult(username='{self.username}', "
            f"amount={self.amount} months, payment='{self.payment_method}', "
            f"tx='{self.transaction_id}')"
        )


@dataclass
class StarsResult:
    '''Result of a successful Telegram Stars purchase.'''

    transaction_id: str
    username: str
    amount: int
    payment_method: str = "ton"

    def __repr__(self) -> str:
        return (
            f"StarsResult(username='{self.username}', "
            f"amount={self.amount} stars, payment='{self.payment_method}', "
            f"tx='{self.transaction_id}')"
        )


@dataclass
class AdsTopupResult:
    '''Result of a successful Telegram Ads TON top-up.'''

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
    '''Result of a successful Stars giveaway.'''

    transaction_id: str
    channel: str
    winners: int
    amount: int
    payment_method: str = "ton"

    def __repr__(self) -> str:
        return (
            f"GiveawayStarsResult(channel='{self.channel}', "
            f"winners={self.winners}, amount={self.amount} stars, "
            f"payment='{self.payment_method}', tx='{self.transaction_id}')"
        )


@dataclass
class GiveawayPremiumResult:
    '''Result of a successful Premium giveaway.'''

    transaction_id: str
    channel: str
    winners: int
    amount: int
    payment_method: str = "ton"

    def __repr__(self) -> str:
        return (
            f"GiveawayPremiumResult(channel='{self.channel}', "
            f"winners={self.winners}, amount={self.amount} months, "
            f"payment='{self.payment_method}', tx='{self.transaction_id}')"
        )


@dataclass
class BidResult:
    '''Result of a successful bid or buy-now transaction.'''

    transaction_id: str
    item_type: int
    slug: str
    bid: int
    confirm_method: str | None = None
    confirm_id: str | None = None

    def __repr__(self) -> str:
        type_names = {1: "username", 3: "number", 5: "gift"}
        t = type_names.get(self.item_type, str(self.item_type))
        return (
            f"BidResult(type='{t}', slug='{self.slug}', "
            f"bid={self.bid} TON, tx='{self.transaction_id}')"
        )


@dataclass
class UsernamesResult:
    '''Result of username marketplace search.'''

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return (
            f"UsernamesResult(items={len(self.items)}, "
            f"next_offset_id={self.next_offset_id!r})"
        )


@dataclass
class NumbersResult:
    '''Result of anonymous numbers marketplace search.'''

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return (
            f"NumbersResult(items={len(self.items)}, "
            f"next_offset_id={self.next_offset_id!r})"
        )


@dataclass
class GiftsResult:
    '''Result of gifts marketplace search.'''

    items: list[dict[str, Any]]
    next_offset: int | None

    def __repr__(self) -> str:
        return (
            f"GiftsResult(items={len(self.items)}, "
            f"next_offset={self.next_offset!r})"
        )


@dataclass
class BidHistoryEntry:
    '''Single bid history entry.'''

    price: str | None
    date: str | None
    wallet: str | None


@dataclass
class OwnerHistoryEntry:
    '''Single ownership history entry.'''

    price: str | None
    date: str | None
    wallet: str | None


@dataclass
class AuctionInfo:
    '''Auction pricing information.'''

    highest_bid: str | None = None
    bid_step: str | None = None
    minimum_bid: str | None = None
    sell_price: str | None = None
    buy_now_price: str | None = None


@dataclass
class UsernameInfo:
    '''Detailed information about a Fragment username.'''

    username: str
    status: str
    item_type: int
    ton_rate: float
    auction: AuctionInfo | None = None
    auction_end: str | None = None
    owner_wallet: str | None = None
    purchased_date: str | None = None
    bid_history: list[BidHistoryEntry] = field(default_factory=list)
    owner_history: list[OwnerHistoryEntry] = field(default_factory=list)
    bid_history_next_offset: str | None = None
    owner_history_next_offset: str | None = None

    def __repr__(self) -> str:
        return (
            f"UsernameInfo(username='@{self.username}', status='{self.status}', "
            f"bids={len(self.bid_history)}, owners={len(self.owner_history)})"
        )


@dataclass
class NumberInfo:
    '''Detailed information about a Fragment number.'''

    number: str
    display_number: str
    status: str
    item_type: int
    ton_rate: float
    restricted: bool = False
    auction: AuctionInfo | None = None
    auction_end: str | None = None
    owner_wallet: str | None = None
    purchased_date: str | None = None
    bid_history: list[BidHistoryEntry] = field(default_factory=list)
    owner_history: list[OwnerHistoryEntry] = field(default_factory=list)
    bid_history_next_offset: str | None = None
    owner_history_next_offset: str | None = None

    def __repr__(self) -> str:
        return (
            f"NumberInfo(number='{self.display_number}', status='{self.status}', "
            f"restricted={self.restricted})"
        )


@dataclass
class GiftAttribute:
    '''Gift attribute with rarity.'''

    name: str
    value: str
    rarity: str | None = None


@dataclass
class GiftInfo:
    '''Detailed information about a Fragment gift.'''

    slug: str
    name: str
    status: str
    item_type: int
    ton_rate: float
    image_url: str | None = None
    sticker_url: str | None = None
    owner_wallet: str | None = None
    purchased_date: str | None = None
    auction: AuctionInfo | None = None
    auction_end: str | None = None
    attributes: list[GiftAttribute] = field(default_factory=list)
    issued: str | None = None
    bid_history: list[BidHistoryEntry] = field(default_factory=list)
    owner_history: list[OwnerHistoryEntry] = field(default_factory=list)
    bid_history_next_offset: str | None = None
    owner_history_next_offset: str | None = None

    def __repr__(self) -> str:
        return (
            f"GiftInfo(name='{self.name}', status='{self.status}', "
            f"attrs={len(self.attributes)})"
        )


@dataclass
class StarsPrice:
    '''Price for a specific stars amount.'''

    stars: int
    ton_price: str
    usd_price: str


@dataclass
class StarsPrices:
    '''All available stars package prices.'''

    packages: list[StarsPrice]
    ton_rate: float

    def __repr__(self) -> str:
        return f"StarsPrices(packages={len(self.packages)}, ton_rate={self.ton_rate})"


@dataclass
class PremiumPriceOption:
    '''Single premium duration price.'''

    months: int
    label: str
    ton_price: str
    usd_price: str
    discount: str | None = None


@dataclass
class PremiumPrices:
    '''Premium subscription prices.'''

    options: list[PremiumPriceOption]
    ton_rate: float

    def __repr__(self) -> str:
        return f"PremiumPrices(options={len(self.options)}, ton_rate={self.ton_rate})"


@dataclass
class StarsTransaction:
    '''Single stars transaction from history.'''

    recipient: str
    stars: int
    price_ton: str
    date: str


@dataclass
class PremiumTransaction:
    '''Single premium transaction from history.'''

    recipient: str
    duration: str
    price_ton: str
    date: str


@dataclass
class ProfileInfo:
    '''Fragment account profile information.'''

    name: str
    username: str
    photo_url: str | None
    identity_verified: bool
    wallet_address: str | None
    wallet_label: str | None
    wallet_verified: bool

    def __repr__(self) -> str:
        return (
            f"ProfileInfo(name='{self.name}', username='@{self.username}', "
            f"verified={self.identity_verified})"
        )


@dataclass
class SessionInfo:
    '''Active session information.'''

    session_id: str
    device: str
    location: str
    date: str | None
    is_current: bool

    def __repr__(self) -> str:
        return (
            f"SessionInfo(device='{self.device}', location='{self.location}', "
            f"current={self.is_current})"
        )
        
        
@dataclass
class LoginCodeResult:
    '''Result of a pending login code request.'''
    number: str
    code: str | None
    active_sessions: int

    def __repr__(self) -> str:
        code_str = f"'{self.code}'" if self.code else "None"
        return f"LoginCodeResult(number='{self.number}', code={code_str}, active_sessions={self.active_sessions})"


@dataclass
class TerminateSessionsResult:
    '''Result of terminating anonymous number sessions.'''
    number: str
    message: str | None

    def __repr__(self) -> str:
        return f"TerminateSessionsResult(number='{self.number}', message={self.message!r})"