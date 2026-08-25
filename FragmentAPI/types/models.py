"""
Pydantic v2 models for Fragment API responses.

All API methods return strongly-typed Pydantic model instances.
Backward-compatible with previous dataclass-based results via re-exports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class FragmentBaseModel(BaseModel):
    """Base model with shared config for all Fragment API models."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class PreparedTransactionMessage(FragmentBaseModel):
    """Single message of a prepared TON transaction."""

    address: str
    amount: str
    payload: str | None = None
    state_init: str | None = None


class PreparedTransaction(FragmentBaseModel):
    """Unsigned Fragment transaction payload for external signing.

    Used both in EVM-only mode and No-KYC mode to return transaction
    details that the caller can sign and broadcast externally.
    """

    req_id: str
    item_kind: str
    target: str
    amount: int
    valid_until: int
    messages: list[PreparedTransactionMessage] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
    sender_address: str | None = None
    confirm_referer: str | None = None

    def __repr__(self) -> str:
        return (
            f"PreparedTransaction("
            f"kind='{self.item_kind}', "
            f"target='{self.target}', "
            f"amount={self.amount}, "
            f"messages={len(self.messages)}"
            f")"
        )


class EvmInvoice(FragmentBaseModel):
    """EVM payment invoice details from Fragment."""

    req_id: str
    invoice_address: str
    invoice_token: str
    invoice_chain_id: int
    invoice_chain_name: str
    invoice_amount_hex: str
    invoice_amount: float
    invoice_amount_raw: int
    token_symbol: str
    token_decimals: int
    expires_at: int
    payment_method: str
    api_hash: str
    page_url: str

    def __repr__(self) -> str:
        return (
            f"EvmInvoice("
            f"amount={self.invoice_amount} {self.token_symbol}, "
            f"chain='{self.invoice_chain_name}', "
            f"address='{self.invoice_address[:10]}...', "
            f"expires_at={self.expires_at}"
            f")"
        )


class EvmPaymentResult(FragmentBaseModel):
    """Result of initiating an EVM payment."""

    item_kind: str
    target: str
    amount: int
    payment_method: str
    invoice: EvmInvoice

    def __repr__(self) -> str:
        return (
            f"EvmPaymentResult("
            f"kind='{self.item_kind}', "
            f"target='{self.target}', "
            f"amount={self.amount}, "
            f"payment='{self.payment_method}'"
            f")"
        )


class TransactionResult(FragmentBaseModel):
    """Result of a TON transaction with confirmation details."""

    tx_hash: str
    boc: str | None = None
    seqno_before: int | None = None
    seqno_after: int | None = None
    balance_before: float | None = None
    balance_after: float | None = None
    confirmed: bool = False

    def __repr__(self) -> str:
        return (
            f"TransactionResult("
            f"tx='{self.tx_hash[:16]}...', "
            f"confirmed={self.confirmed}, "
            f"seqno={self.seqno_before}->{self.seqno_after}"
            f")"
        )


class WalletInfo(FragmentBaseModel):
    """Wallet state information with GRAM and USDT balances."""

    address: str
    state: str
    gram_balance: float
    usdt_balance: float

    @property
    def balance_ton(self) -> float:
        """Alias for gram_balance for backward compatibility."""
        return self.gram_balance

    @property
    def balance_usdt(self) -> float:
        """Alias for usdt_balance for consistency."""
        return self.usdt_balance

    def __repr__(self) -> str:
        return (
            f"WalletInfo("
            f"address='{self.address}', "
            f"state='{self.state}', "
            f"gram_balance={self.gram_balance}, "
            f"usdt_balance={self.usdt_balance}"
            f")"
        )


class RecipientInfo(FragmentBaseModel):
    """Resolved recipient from Fragment search."""

    recipient: str
    name: str
    photo_url: str | None = None
    myself: bool = False

    def __repr__(self) -> str:
        return (
            f"RecipientInfo("
            f"name='{self.name}', "
            f"recipient='{self.recipient[:24]}...', "
            f"myself={self.myself}"
            f")"
        )


class PurchaseItem(FragmentBaseModel):
    """Single item for batch purchase operation."""

    type: str
    username: str
    amount: int | None = None
    months: int | None = None
    show_sender: bool = True

    def __repr__(self) -> str:
        if self.type == "premium":
            return f"PurchaseItem(type='premium', username='{self.username}', months={self.months})"
        return f"PurchaseItem(type='{self.type}', username='{self.username}', amount={self.amount})"


class PurchaseResult(FragmentBaseModel):
    """Result of a successful purchase operation."""

    transaction_id: str
    type: str
    username: str
    amount: int
    payment_method: str = "gram"

    def __repr__(self) -> str:
        unit = "months" if self.type == "premium" else ("GRAM" if self.type in ("gram", "ton") else "stars")
        return (
            f"PurchaseResult("
            f"type='{self.type}', "
            f"username='{self.username}', "
            f"amount={self.amount} {unit}, "
            f"payment='{self.payment_method}', "
            f"tx='{self.transaction_id}'"
            f")"
        )


class PremiumResult(FragmentBaseModel):
    """Result of a successful Telegram Premium gift."""

    transaction_id: str
    username: str
    amount: int
    payment_method: str = "gram"


class StarsResult(FragmentBaseModel):
    """Result of a successful Telegram Stars purchase."""

    transaction_id: str
    username: str
    amount: int
    payment_method: str = "gram"


class AdsTopupResult(FragmentBaseModel):
    """Result of a successful Telegram Ads GRAM top-up."""

    transaction_id: str
    username: str
    amount: int


class GiveawayStarsResult(FragmentBaseModel):
    """Result of a successful Stars giveaway."""

    transaction_id: str
    channel: str
    winners: int
    amount: int
    payment_method: str = "gram"


class GiveawayPremiumResult(FragmentBaseModel):
    """Result of a successful Premium giveaway."""

    transaction_id: str
    channel: str
    winners: int
    amount: int
    payment_method: str = "gram"


class NftWithdrawalInitResult(FragmentBaseModel):
    """Result of NFT withdrawal initialization."""

    ok: bool
    confirm_message: str | None = None
    confirm_button: str | None = None
    confirm_hash: str | None = None
    error: str | None = None


class NftWithdrawalConfirmResult(FragmentBaseModel):
    """Result of NFT withdrawal confirmation."""

    ok: bool
    need_update: bool
    mode: str
    html: str | None = None
    error: str | None = None


class StarsWithdrawalState(FragmentBaseModel):
    """Stars withdrawal state from Fragment page."""

    transaction: str
    withdrawal_data: str


class StarsWithdrawalInitResult(FragmentBaseModel):
    """Result of Stars withdrawal initialization."""

    ok: bool
    confirm_message: str | None = None
    confirm_button: str | None = None
    confirm_hash: str | None = None
    error: str | None = None


class StarsWithdrawalConfirmResult(FragmentBaseModel):
    """Result of Stars withdrawal confirmation."""

    ok: bool
    need_update: bool
    mode: str
    html: str | None = None
    error: str | None = None


class AdsWithdrawalInitResult(FragmentBaseModel):
    """Result of Ads revenue withdrawal initialization."""

    ok: bool
    confirm_message: str | None = None
    confirm_button: str | None = None
    confirm_hash: str | None = None
    error: str | None = None


class AdsWithdrawalConfirmResult(FragmentBaseModel):
    """Result of Ads revenue withdrawal confirmation."""

    ok: bool
    need_update: bool = False
    mode: str = "unknown"
    html: str | None = None
    error: str | None = None


class BidResult(FragmentBaseModel):
    """Result of a successful bid or buy-now transaction."""

    transaction_id: str
    item_type: int
    slug: str
    bid: int
    confirm_method: str | None = None
    confirm_id: str | None = None


class OfferResult(FragmentBaseModel):
    """Result of a make-offer transaction."""

    transaction_id: str
    item_type: int
    slug: str
    amount: int
    req_id: str | None = None


class UsernamesResult(FragmentBaseModel):
    """Result of username marketplace search."""

    items: list[dict[str, Any]]
    next_offset_id: str | None


class NumbersResult(FragmentBaseModel):
    """Result of anonymous numbers marketplace search."""

    items: list[dict[str, Any]]
    next_offset_id: str | None


class GiftsResult(FragmentBaseModel):
    """Result of gifts marketplace search."""

    items: list[dict[str, Any]]
    next_offset: int | None


class BidHistoryEntry(FragmentBaseModel):
    """Single bid history entry."""

    price: str | None = None
    date: str | None = None
    wallet: str | None = None


class OwnerHistoryEntry(FragmentBaseModel):
    """Single ownership history entry."""

    price: str | None = None
    date: str | None = None
    wallet: str | None = None


class OfferHistoryEntry(FragmentBaseModel):
    """Single offer history entry."""

    price: str | None = None
    date: str | None = None
    wallet: str | None = None


class AuctionInfo(FragmentBaseModel):
    """Auction pricing information."""

    highest_bid: str | None = None
    bid_step: str | None = None
    minimum_bid: str | None = None
    sell_price: str | None = None
    buy_now_price: str | None = None


class UsernameInfo(FragmentBaseModel):
    """Detailed information about a Fragment username."""

    username: str
    status: str
    item_type: int
    gram_rate: float
    auction: AuctionInfo | None = None
    auction_end: str | None = None
    owner_wallet: str | None = None
    purchased_date: str | None = None
    bid_history: list[BidHistoryEntry] = Field(default_factory=list)
    owner_history: list[OwnerHistoryEntry] = Field(default_factory=list)
    offer_history: list[OfferHistoryEntry] = Field(default_factory=list)
    bid_history_next_offset: str | None = None
    owner_history_next_offset: str | None = None
    offer_history_next_offset: str | None = None

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class NumberInfo(FragmentBaseModel):
    """Detailed information about a Fragment number."""

    number: str
    display_number: str
    status: str
    item_type: int
    gram_rate: float
    restricted: bool = False
    auction: AuctionInfo | None = None
    auction_end: str | None = None
    owner_wallet: str | None = None
    purchased_date: str | None = None
    bid_history: list[BidHistoryEntry] = Field(default_factory=list)
    owner_history: list[OwnerHistoryEntry] = Field(default_factory=list)
    offer_history: list[OfferHistoryEntry] = Field(default_factory=list)
    bid_history_next_offset: str | None = None
    owner_history_next_offset: str | None = None
    offer_history_next_offset: str | None = None

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class GiftAttribute(FragmentBaseModel):
    """Gift attribute with rarity."""

    name: str
    value: str
    rarity: str | None = None


class GiftInfo(FragmentBaseModel):
    """Detailed information about a Fragment gift."""

    slug: str
    name: str
    status: str
    item_type: int
    gram_rate: float
    image_url: str | None = None
    sticker_url: str | None = None
    owner_wallet: str | None = None
    purchased_date: str | None = None
    auction: AuctionInfo | None = None
    auction_end: str | None = None
    attributes: list[GiftAttribute] = Field(default_factory=list)
    issued: str | None = None
    bid_history: list[BidHistoryEntry] = Field(default_factory=list)
    owner_history: list[OwnerHistoryEntry] = Field(default_factory=list)
    offer_history: list[OfferHistoryEntry] = Field(default_factory=list)
    bid_history_next_offset: str | None = None
    owner_history_next_offset: str | None = None
    offer_history_next_offset: str | None = None

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class StarsPrice(FragmentBaseModel):
    """Price for a specific stars amount."""

    stars: int
    gram_price: str
    usd_price: str

    @property
    def ton_price(self) -> str:
        """Alias for gram_price for backward compatibility."""
        return self.gram_price


class StarsPrices(FragmentBaseModel):
    """All available stars package prices."""

    packages: list[StarsPrice]
    gram_rate: float

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class PremiumPriceOption(FragmentBaseModel):
    """Single premium duration price."""

    months: int
    label: str
    gram_price: str
    usd_price: str
    discount: str | None = None

    @property
    def ton_price(self) -> str:
        """Alias for gram_price for backward compatibility."""
        return self.gram_price


class PremiumPrices(FragmentBaseModel):
    """Premium subscription prices."""

    options: list[PremiumPriceOption]
    gram_rate: float

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class StarsTransaction(FragmentBaseModel):
    """Single stars transaction from history."""

    recipient: str
    stars: int
    price_gram: str
    date: str

    @property
    def price_ton(self) -> str:
        """Alias for price_gram for backward compatibility."""
        return self.price_gram


class PremiumTransaction(FragmentBaseModel):
    """Single premium transaction from history."""

    recipient: str
    duration: str
    price_gram: str
    date: str

    @property
    def price_ton(self) -> str:
        """Alias for price_gram for backward compatibility."""
        return self.price_gram


class TopupTransaction(FragmentBaseModel):
    """Single topup transaction from Ads history."""

    recipient: str
    amount: int
    date: str


class ProfileInfo(FragmentBaseModel):
    """Fragment account profile information."""

    name: str
    username: str
    photo_url: str | None = None
    identity_verified: bool = False
    wallet_address: str | None = None
    wallet_label: str | None = None
    wallet_verified: bool = False


class SessionInfo(FragmentBaseModel):
    """Active session information."""

    session_id: str
    device: str
    location: str
    date: str | None = None
    is_current: bool = False


class MyBid(FragmentBaseModel):
    """Single bid entry from My Bid History."""

    item_type: str
    slug: str
    name: str
    bid: float
    status: str
    date: str
    image_url: str | None = None
    description: str | None = None


class MyBidsResult(FragmentBaseModel):
    """Result of My Bid History query."""

    items: list[MyBid]
    gram_rate: float
    total_count: int

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class MyAsset(FragmentBaseModel):
    """Single asset from My Assets page."""

    item_type: str
    slug: str
    name: str
    description: str | None = None
    image_url: str | None = None
    assigned_to: str | None = None
    assigned_name: str | None = None


class MyAssetsResult(FragmentBaseModel):
    """Result of My Assets query."""

    items: list[MyAsset]
    gram_rate: float
    total_count: int

    @property
    def ton_rate(self) -> float:
        """Alias for gram_rate for backward compatibility."""
        return self.gram_rate


class TelegramAccount(FragmentBaseModel):
    """Telegram account available for assignment."""

    id: str
    name: str
    type: str
    photo_url: str | None = None


class AssignAccountsResult(FragmentBaseModel):
    """Result of getting available Telegram accounts for assignment."""

    accounts: list[TelegramAccount]
    can_disable: bool


class AssignResult(FragmentBaseModel):
    """Result of assigning asset to Telegram account."""

    ok: bool
    message: str | None = None
    need_pay: bool = False
    req_id: str | None = None
    amount: str | None = None
    assign_name: str | None = None


class StartAuctionResult(FragmentBaseModel):
    """Result of starting auction or selling asset."""

    ok: bool
    req_id: str | None = None


class NftTransferRecipient(FragmentBaseModel):
    """Recipient info for NFT transfer."""

    myself: bool
    recipient: str
    name: str
    photo_url: str | None = None


class NftTransferRequest(FragmentBaseModel):
    """Result of initNftTransferRequest."""

    req_id: str
    myself: bool
    item_title: str
    content: str
    button: str


class LoginCodeResult(FragmentBaseModel):
    """Result of a pending login code request."""

    number: str
    code: str | None = None
    active_sessions: int = 0


class TerminateSessionsResult(FragmentBaseModel):
    """Result of terminating anonymous number sessions."""

    number: str
    message: str | None = None


class BatchItemResult(FragmentBaseModel):
    """Result of a single item within a batch operation."""

    type: str
    username: str
    amount: int
    ok: bool
    result: Any = None
    error: str | None = None
    chunk_index: int = 0


class BatchResult(FragmentBaseModel):
    """Result of a batch purchase operation."""

    total: int
    succeeded: int
    failed: int
    chunks_sent: int
    items: list[BatchItemResult] = Field(default_factory=list)


class NoKycBatchResult(FragmentBaseModel):
    """Result of a No-KYC batch purchase operation.

    In No-KYC mode each item is processed individually via MarketApp API.
    If auto_pay is enabled (wallet configured), items contains PurchaseResult-like results.
    If auto_pay is disabled, prepared_transactions contains PreparedTransaction objects
    for external signing.
    """

    total: int
    succeeded: int
    failed: int
    items: list[BatchItemResult] = Field(default_factory=list)
    prepared_transactions: list[PreparedTransaction] = Field(default_factory=list)


class GatewayRechargeResult(FragmentBaseModel):
    """Result of a Telegram Gateway credits recharge."""

    transaction_id: str
    account_id: str
    credits: int
    req_id: str | None = None


class GatewayPriceInfo(FragmentBaseModel):
    """Price info for Gateway credits purchase."""

    credits: int
    gram_price: str
    usd_price: str | None = None


class AdsRechargeResult(FragmentBaseModel):
    """Result of a Telegram Ads account recharge."""

    transaction_id: str
    account_id: str
    amount: int
    req_id: str | None = None


class SubscriptionResult(FragmentBaseModel):
    """Result of subscribe/unsubscribe to item updates."""

    ok: bool
    subscribed: bool
    item_type: int
    slug: str