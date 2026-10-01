"""Typed public results and explicit transaction lifecycle information."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class FragmentBaseModel(BaseModel):
    """Common model configuration."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class PreparedTransactionMessage(FragmentBaseModel):
    """A TON internal message expressed in integer nanotons."""

    address: str
    amount: str
    payload: str | None = None
    state_init: str | None = Field(default=None, alias="stateInit")


class PreparedTransaction(FragmentBaseModel):
    """A complete unsigned payment including its separate native-TON fee.

    sender_address identifies the account used to request the invoice.
    An external signer must use that account unless Fragment explicitly permits
    another sender. Preparing a transaction does not imply payment or fulfillment.
    """

    req_id: str = ""
    item_kind: str
    target: str
    amount: int
    valid_until: int
    messages: list[PreparedTransactionMessage] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
    sender_address: str | None = None
    confirm_referer: str | None = None
    payment_method: str = "ton"
    payment_nanoton: int = 0
    fee_nanoton: int = 0
    gas_reserve_nanoton: int = 0
    required_nanoton: int = 0


class TransactionResult(FragmentBaseModel):
    """Broadcast receipt distinct from Fragment fulfillment confirmation.

    tx_hash is the normalized external-message identifier returned by tonutils,
    not necessarily the eventual on-chain transaction hash.
    """

    tx_hash: str
    boc: str | None = None
    status: Literal["broadcast", "confirmed", "unknown"] = "broadcast"
    confirmed: bool = False
    seqno_before: int | None = None
    seqno_after: int | None = None
    balance_before: float | None = None
    balance_after: float | None = None
    payment_nanoton: int = 0
    fee_nanoton: int = 0
    confirmation_error: str | None = None


class EvmInvoice(FragmentBaseModel):
    """An external EVM invoice without a library TON fee."""

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
    api_hash: str = ""
    page_url: str


class EvmPaymentResult(FragmentBaseModel):
    """An EVM invoice awaiting external payment."""

    item_kind: str
    target: str
    amount: int
    payment_method: str
    invoice: EvmInvoice


class WalletInfo(FragmentBaseModel):
    """Wallet balances; an unavailable USDT balance is represented by None."""

    address: str
    state: str
    gram_balance: float
    usdt_balance: float | None
    balance_nanoton: int = 0

    @property
    def balance_ton(self) -> float:
        """Return the native TON balance."""
        return self.gram_balance

    @property
    def balance_usdt(self) -> float | None:
        """Return the USDT balance."""
        return self.usdt_balance


class RecipientInfo(FragmentBaseModel):
    """A resolved Fragment recipient token."""

    recipient: str
    name: str
    photo_url: str | None = None
    myself: bool = False


class PurchaseItem(FragmentBaseModel):
    """One purchase with strictly typed integer quantities."""

    type: str
    username: str
    amount: StrictInt | None = None
    months: StrictInt | None = None
    show_sender: bool = True


class PurchaseResult(FragmentBaseModel):
    """Purchase broadcast and fulfillment result."""

    transaction_id: str
    type: str
    username: str
    amount: int
    payment_method: str = "ton"
    confirmed: bool = False
    fee_nanoton: int = 0
    req_id: str | None = None
    confirmation_error: str | None = None


class PremiumResult(PurchaseResult):
    """Premium purchase compatibility result."""

    type: str = "premium"


class StarsResult(PurchaseResult):
    """Stars purchase compatibility result."""

    type: str = "stars"


class AdsTopupResult(PurchaseResult):
    """Ads top-up compatibility result."""

    type: str = "ton"


class GiveawayStarsResult(FragmentBaseModel):
    """Stars giveaway receipt using the total package amount."""

    transaction_id: str
    channel: str
    winners: int
    amount: int
    payment_method: str = "ton"
    confirmed: bool = False
    fee_nanoton: int = 0
    req_id: str | None = None
    confirmation_error: str | None = None


class GiveawayPremiumResult(GiveawayStarsResult):
    """Premium giveaway receipt; amount is the duration in months."""


class WithdrawalInitResult(FragmentBaseModel):
    """Withdrawal initialization and approval challenge."""

    ok: bool
    confirm_message: str | None = None
    confirm_button: str | None = None
    confirm_hash: str | None = None
    error: str | None = None


class WithdrawalConfirmResult(FragmentBaseModel):
    """Withdrawal confirmation response."""

    ok: bool
    need_update: bool = False
    mode: str = "unknown"
    html: str | None = None
    error: str | None = None


class NftWithdrawalInitResult(WithdrawalInitResult):
    """NFT withdrawal initialization."""


class NftWithdrawalConfirmResult(WithdrawalConfirmResult):
    """NFT withdrawal confirmation."""


class StarsWithdrawalInitResult(WithdrawalInitResult):
    """Stars withdrawal initialization."""


class StarsWithdrawalConfirmResult(WithdrawalConfirmResult):
    """Stars withdrawal confirmation."""


class AdsWithdrawalInitResult(WithdrawalInitResult):
    """Ads withdrawal initialization."""


class AdsWithdrawalConfirmResult(WithdrawalConfirmResult):
    """Ads withdrawal confirmation."""


class StarsWithdrawalState(FragmentBaseModel):
    """Opaque Stars withdrawal state."""

    transaction: str
    withdrawal_data: str


class BidResult(FragmentBaseModel):
    """Bid broadcast receipt."""

    transaction_id: str
    item_type: int
    slug: str
    bid: int
    confirm_method: str | None = None
    confirm_id: str | None = None
    confirmed: bool = False
    fee_nanoton: int = 0


class OfferResult(FragmentBaseModel):
    """Offer broadcast receipt."""

    transaction_id: str
    item_type: int
    slug: str
    amount: int
    req_id: str | None = None
    confirmed: bool = False
    fee_nanoton: int = 0


class UsernamesResult(FragmentBaseModel):
    """Username listings and cursor."""

    items: list[dict[str, Any]] = Field(default_factory=list)
    next_offset_id: str | None = None


class NumbersResult(UsernamesResult):
    """Number listings and cursor."""


class GiftsResult(FragmentBaseModel):
    """Gift listings and cursor."""

    items: list[dict[str, Any]] = Field(default_factory=list)
    next_offset: int | None = None


class BidHistoryEntry(FragmentBaseModel):
    """One item history entry."""

    price: str | None = None
    date: str | None = None
    wallet: str | None = None


class OwnerHistoryEntry(BidHistoryEntry):
    """Ownership history entry."""


class OfferHistoryEntry(BidHistoryEntry):
    """Offer history entry."""


class AuctionInfo(FragmentBaseModel):
    """Auction price fields."""

    highest_bid: str | None = None
    bid_step: str | None = None
    minimum_bid: str | None = None
    sell_price: str | None = None
    buy_now_price: str | None = None


class RateModel(FragmentBaseModel):
    """Compatibility model exposing TON and historical GRAM naming."""

    gram_rate: float = 0.0

    @property
    def ton_rate(self) -> float:
        """Return the TON exchange rate."""
        return self.gram_rate


class ItemInfo(RateModel):
    """Common item detail fields."""

    status: str = "Unknown"
    item_type: int
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


class UsernameInfo(ItemInfo):
    """Username details."""

    username: str


class NumberInfo(ItemInfo):
    """Anonymous-number details."""

    number: str
    display_number: str
    restricted: bool = False


class GiftAttribute(FragmentBaseModel):
    """Gift attribute and rarity."""

    name: str
    value: str
    rarity: str | None = None


class GiftInfo(ItemInfo):
    """Collectible gift details."""

    slug: str
    name: str
    image_url: str | None = None
    sticker_url: str | None = None
    attributes: list[GiftAttribute] = Field(default_factory=list)
    issued: str | None = None


class GiftCollection(FragmentBaseModel):
    """Gift collection filter."""

    slug: str
    name: str
    count: int
    image_url: str | None = None


class GiftAttributeValue(FragmentBaseModel):
    """Gift trait filter value."""

    name: str
    value: str
    count: int
    image_url: str | None = None


class GiftAttributeCategory(FragmentBaseModel):
    """Gift trait category."""

    field: str
    name: str
    total_count: int
    items: list[GiftAttributeValue] = Field(default_factory=list)


class GiftFiltersInfo(FragmentBaseModel):
    """Available collections and trait categories."""

    collections: list[GiftCollection] = Field(default_factory=list)
    attributes: list[GiftAttributeCategory] = Field(default_factory=list)


class StarsPrice(FragmentBaseModel):
    """Stars price in decimal currency strings."""

    stars: int
    gram_price: str
    usd_price: str

    @property
    def ton_price(self) -> str:
        """Return the native TON price."""
        return self.gram_price


class StarsPrices(RateModel):
    """Stars package prices."""

    packages: list[StarsPrice] = Field(default_factory=list)


class PremiumPriceOption(FragmentBaseModel):
    """Premium price option."""

    months: int
    label: str
    gram_price: str
    usd_price: str
    discount: str | None = None

    @property
    def ton_price(self) -> str:
        """Return the native TON price."""
        return self.gram_price


class PremiumPrices(RateModel):
    """Premium duration prices."""

    options: list[PremiumPriceOption] = Field(default_factory=list)


class StarsTransaction(FragmentBaseModel):
    """Stars account history entry."""

    recipient: str
    stars: int
    price_gram: str
    date: str

    @property
    def price_ton(self) -> str:
        """Return the native price."""
        return self.price_gram


class PremiumTransaction(FragmentBaseModel):
    """Premium account history entry."""

    recipient: str
    duration: str
    price_gram: str
    date: str

    @property
    def price_ton(self) -> str:
        """Return the native price."""
        return self.price_gram


class TopupTransaction(FragmentBaseModel):
    """Ads top-up history entry."""

    recipient: str
    amount: int
    date: str


class ProfileInfo(FragmentBaseModel):
    """Authenticated account profile."""

    name: str
    username: str
    photo_url: str | None = None
    identity_verified: bool = False
    wallet_address: str | None = None
    wallet_label: str | None = None
    wallet_verified: bool = False


class SessionInfo(FragmentBaseModel):
    """Authenticated Fragment session."""

    session_id: str
    device: str
    location: str
    date: str | None = None
    is_current: bool = False


class MyBid(FragmentBaseModel):
    """Authenticated bid history entry."""

    item_type: str
    slug: str
    name: str
    bid: float
    status: str
    date: str
    image_url: str | None = None
    description: str | None = None


class MyBidsResult(RateModel):
    """Authenticated bids."""

    items: list[MyBid] = Field(default_factory=list)
    total_count: int = 0


class MyAsset(FragmentBaseModel):
    """Authenticated owned asset."""

    item_type: str
    slug: str
    name: str
    description: str | None = None
    image_url: str | None = None
    assigned_to: str | None = None
    assigned_name: str | None = None


class MyAssetsResult(RateModel):
    """Authenticated owned assets."""

    items: list[MyAsset] = Field(default_factory=list)
    total_count: int = 0


class TelegramAccount(FragmentBaseModel):
    """An assignment destination."""

    id: str
    name: str
    type: str
    photo_url: str | None = None


class AssignAccountsResult(FragmentBaseModel):
    """Available assignment destinations."""

    accounts: list[TelegramAccount] = Field(default_factory=list)
    can_disable: bool = False


class AssignResult(FragmentBaseModel):
    """Assignment operation result."""

    ok: bool
    message: str | None = None
    need_pay: bool = False
    req_id: str | None = None
    amount: str | None = None
    assign_name: str | None = None


class StartAuctionResult(FragmentBaseModel):
    """Auction broadcast receipt."""

    ok: bool
    req_id: str | None = None
    transaction_id: str | None = None
    confirmed: bool = False


class NftTransferRecipient(RecipientInfo):
    """NFT transfer destination."""


class NftTransferRequest(FragmentBaseModel):
    """NFT transfer initialization."""

    req_id: str
    myself: bool = False
    item_title: str = ""
    content: str = ""
    button: str = ""


class LoginCodeResult(FragmentBaseModel):
    """Pending anonymous-number login code."""

    number: str
    code: str | None = None
    active_sessions: int = 0

    def __repr__(self) -> str:
        """Omit the login code from diagnostic representations."""
        return f"LoginCodeResult(number={self.number!r}, active_sessions={self.active_sessions})"


class TerminateSessionsResult(FragmentBaseModel):
    """Anonymous-number session termination result."""

    number: str
    message: str | None = None


class BatchItemResult(FragmentBaseModel):
    """One batch outcome, including unresolved broadcast outcomes."""

    type: str
    username: str
    amount: int
    ok: bool
    result: Any = None
    error: str | None = None
    chunk_index: int = 0
    status: Literal["prepared", "broadcast", "confirmed", "failed", "unknown"] = "failed"


class BatchResult(FragmentBaseModel):
    """Batch results; succeeded means broadcast, not necessarily fulfillment."""

    total: int
    succeeded: int
    failed: int
    chunks_sent: int
    items: list[BatchItemResult] = Field(default_factory=list)
    prepared_transactions: list[PreparedTransaction] = Field(default_factory=list)


class NoKycBatchResult(BatchResult):
    """Compatibility result name for wallet-auth batch operations."""


class GatewayRechargeResult(FragmentBaseModel):
    """Gateway recharge receipt."""

    transaction_id: str
    account_id: str
    credits: int
    req_id: str | None = None
    confirmed: bool = False
    fee_nanoton: int = 0
    confirmation_error: str | None = None


class GatewayPriceInfo(FragmentBaseModel):
    """Gateway credit quote."""

    credits: int
    gram_price: str
    usd_price: str | None = None


class AdsRechargeResult(FragmentBaseModel):
    """Ads recharge receipt."""

    transaction_id: str
    account_id: str
    amount: int
    req_id: str | None = None
    confirmed: bool = False
    fee_nanoton: int = 0
    confirmation_error: str | None = None


class SubscriptionResult(FragmentBaseModel):
    """Auction subscription state."""

    ok: bool
    subscribed: bool
    item_type: int
    slug: str


__all__ = [
    name for name, value in globals().items()
    if isinstance(value, type)
    and issubclass(value, FragmentBaseModel)
    and value.__module__ == __name__
]