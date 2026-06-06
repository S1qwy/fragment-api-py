from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import Any


@dataclass
class PreparedTransactionMessage:
    '''Single message of a prepared TON transaction.'''

    address: str
    amount: str
    payload: str | None = None
    state_init: str | None = None


@dataclass
class PreparedTransaction:
    '''Unsigned Fragment transaction payload for external signing.'''

    req_id: str
    item_kind: str
    target: str
    amount: int
    valid_until: int
    messages: list[PreparedTransactionMessage] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
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


@dataclass
class EvmInvoice:
    '''EVM payment invoice details from Fragment.'''

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


@dataclass
class EvmPaymentResult:
    '''Result of initiating an EVM payment.'''

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


@dataclass
class TransactionResult:
    '''Result of a TON transaction with confirmation details.'''

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


@dataclass
class WalletInfo:
    '''Wallet state information.'''

    address: str
    state: str
    balance_ton: float
    balance_usdt: float

    def __repr__(self) -> str:
        return (
            f"WalletInfo("
            f"address='{self.address}', "
            f"state='{self.state}', "
            f"balance_ton={self.balance_ton}, "
            f"balance_usdt={self.balance_usdt}"
            f")"
        )


@dataclass
class RecipientInfo:
    '''Resolved recipient from Fragment search.'''

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


@dataclass
class PremiumResult:
    '''Result of a successful Telegram Premium gift.'''

    transaction_id: str
    username: str
    amount: int
    payment_method: str = "ton"

    def __repr__(self) -> str:
        return (
            f"PremiumResult("
            f"username='{self.username}', "
            f"amount={self.amount} months, "
            f"payment='{self.payment_method}', "
            f"tx='{self.transaction_id}'"
            f")"
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
            f"StarsResult("
            f"username='{self.username}', "
            f"amount={self.amount} stars, "
            f"payment='{self.payment_method}', "
            f"tx='{self.transaction_id}'"
            f")"
        )


@dataclass
class AdsTopupResult:
    '''Result of a successful Telegram Ads TON top-up.'''

    transaction_id: str
    username: str
    amount: int

    def __repr__(self) -> str:
        return (
            f"AdsTopupResult("
            f"username='{self.username}', "
            f"amount={self.amount} TON, "
            f"tx='{self.transaction_id}'"
            f")"
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
            f"GiveawayStarsResult("
            f"channel='{self.channel}', "
            f"winners={self.winners}, "
            f"amount={self.amount} stars, "
            f"payment='{self.payment_method}', "
            f"tx='{self.transaction_id}'"
            f")"
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
            f"GiveawayPremiumResult("
            f"channel='{self.channel}', "
            f"winners={self.winners}, "
            f"amount={self.amount} months, "
            f"payment='{self.payment_method}', "
            f"tx='{self.transaction_id}'"
            f")"
        )


@dataclass
class NftWithdrawalInitResult:
    '''Result of NFT withdrawal initialization.'''

    ok: bool
    confirm_message: str | None = None
    confirm_button: str | None = None
    confirm_hash: str | None = None
    error: str | None = None

    def __repr__(self) -> str:
        if self.error:
            return f"NftWithdrawalInitResult(ok=False, error='{self.error}')"
        return (
            f"NftWithdrawalInitResult("
            f"ok=True, "
            f"confirm_hash='{self.confirm_hash}', "
            f"button='{self.confirm_button}'"
            f")"
        )


@dataclass
class NftWithdrawalConfirmResult:
    '''Result of NFT withdrawal confirmation.'''

    ok: bool
    need_update: bool
    mode: str
    html: str | None = None
    error: str | None = None

    def __repr__(self) -> str:
        if self.error:
            return f"NftWithdrawalConfirmResult(ok=False, error='{self.error}')"
        return (
            f"NftWithdrawalConfirmResult("
            f"ok={self.ok}, "
            f"mode='{self.mode}', "
            f"need_update={self.need_update}"
            f")"
        )


@dataclass
class StarsWithdrawalState:
    '''Stars withdrawal state from Fragment page.'''

    transaction: str
    withdrawal_data: str

    def __repr__(self) -> str:
        return (
            f"StarsWithdrawalState("
            f"transaction='{self.transaction[:16]}...', "
            f"withdrawal_data='{self.withdrawal_data[:16]}...'"
            f")"
        )


@dataclass
class StarsWithdrawalInitResult:
    '''Result of Stars withdrawal initialization.'''

    ok: bool
    confirm_message: str | None = None
    confirm_button: str | None = None
    confirm_hash: str | None = None
    error: str | None = None

    def __repr__(self) -> str:
        if self.error:
            return f"StarsWithdrawalInitResult(ok=False, error='{self.error}')"
        return (
            f"StarsWithdrawalInitResult("
            f"ok=True, "
            f"confirm_hash='{self.confirm_hash}', "
            f"button='{self.confirm_button}'"
            f")"
        )


@dataclass
class StarsWithdrawalConfirmResult:
    '''Result of Stars withdrawal confirmation.'''

    ok: bool
    need_update: bool
    mode: str
    html: str | None = None
    error: str | None = None

    def __repr__(self) -> str:
        if self.error:
            return f"StarsWithdrawalConfirmResult(ok=False, error='{self.error}')"
        return (
            f"StarsWithdrawalConfirmResult("
            f"ok={self.ok}, "
            f"mode='{self.mode}', "
            f"need_update={self.need_update}"
            f")"
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
            f"BidResult("
            f"type='{t}', "
            f"slug='{self.slug}', "
            f"bid={self.bid} TON, "
            f"tx='{self.transaction_id}'"
            f")"
        )


@dataclass
class UsernamesResult:
    '''Result of username marketplace search.'''

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return (
            f"UsernamesResult("
            f"items={len(self.items)}, "
            f"next_offset_id={self.next_offset_id!r}"
            f")"
        )


@dataclass
class NumbersResult:
    '''Result of anonymous numbers marketplace search.'''

    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return (
            f"NumbersResult("
            f"items={len(self.items)}, "
            f"next_offset_id={self.next_offset_id!r}"
            f")"
        )


@dataclass
class GiftsResult:
    '''Result of gifts marketplace search.'''

    items: list[dict[str, Any]]
    next_offset: int | None

    def __repr__(self) -> str:
        return (
            f"GiftsResult("
            f"items={len(self.items)}, "
            f"next_offset={self.next_offset!r}"
            f")"
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
            f"UsernameInfo("
            f"username='@{self.username}', "
            f"status='{self.status}', "
            f"bids={len(self.bid_history)}, "
            f"owners={len(self.owner_history)}"
            f")"
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
            f"NumberInfo("
            f"number='{self.display_number}', "
            f"status='{self.status}', "
            f"restricted={self.restricted}"
            f")"
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
            f"GiftInfo("
            f"name='{self.name}', "
            f"status='{self.status}', "
            f"attrs={len(self.attributes)}"
            f")"
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
        return (
            f"StarsPrices("
            f"packages={len(self.packages)}, "
            f"ton_rate={self.ton_rate}"
            f")"
        )


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
        return (
            f"PremiumPrices("
            f"options={len(self.options)}, "
            f"ton_rate={self.ton_rate}"
            f")"
        )


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
class TopupTransaction:
    '''Single topup transaction from Ads history.'''

    recipient: str
    amount: int
    date: str

    def __repr__(self) -> str:
        return (
            f"TopupTransaction("
            f"recipient='{self.recipient}', "
            f"amount={self.amount} TON, "
            f"date='{self.date}'"
            f")"
        )


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
            f"ProfileInfo("
            f"name='{self.name}', "
            f"username='@{self.username}', "
            f"verified={self.identity_verified}"
            f")"
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
            f"SessionInfo("
            f"device='{self.device}', "
            f"location='{self.location}', "
            f"current={self.is_current}"
            f")"
        )


@dataclass
class MyBid:
    '''Single bid entry from My Bid History.'''

    item_type: str
    slug: str
    name: str
    bid: float
    status: str
    date: str
    image_url: str | None = None
    description: str | None = None

    def __repr__(self) -> str:
        return (
            f"MyBid("
            f"type='{self.item_type}', "
            f"name='{self.name}', "
            f"bid={self.bid} TON, "
            f"status='{self.status}'"
            f")"
        )


@dataclass
class MyBidsResult:
    '''Result of My Bid History query.'''

    items: list[MyBid]
    ton_rate: float
    total_count: int

    def __repr__(self) -> str:
        return (
            f"MyBidsResult("
            f"items={len(self.items)}, "
            f"ton_rate={self.ton_rate}, "
            f"total={self.total_count}"
            f")"
        )


@dataclass
class MyAsset:
    '''Single asset from My Assets page.'''

    item_type: str
    slug: str
    name: str
    description: str | None = None
    image_url: str | None = None
    assigned_to: str | None = None
    assigned_name: str | None = None

    def __repr__(self) -> str:
        return (
            f"MyAsset("
            f"type='{self.item_type}', "
            f"name='{self.name}', "
            f"assigned_to='{self.assigned_name}'"
            f")"
        )


@dataclass
class MyAssetsResult:
    '''Result of My Assets query.'''

    items: list[MyAsset]
    ton_rate: float
    total_count: int

    def __repr__(self) -> str:
        return (
            f"MyAssetsResult("
            f"items={len(self.items)}, "
            f"ton_rate={self.ton_rate}, "
            f"total={self.total_count}"
            f")"
        )


@dataclass
class TelegramAccount:
    '''Telegram account available for assignment.'''

    id: str
    name: str
    type: str
    photo_url: str | None = None

    def __repr__(self) -> str:
        return f"TelegramAccount(name='{self.name}', type='{self.type}')"


@dataclass
class AssignAccountsResult:
    '''Result of getting available Telegram accounts for assignment.'''

    accounts: list[TelegramAccount]
    can_disable: bool

    def __repr__(self) -> str:
        return (
            f"AssignAccountsResult("
            f"accounts={len(self.accounts)}, "
            f"can_disable={self.can_disable}"
            f")"
        )


@dataclass
class AssignResult:
    '''Result of assigning asset to Telegram account.'''

    ok: bool
    message: str | None = None
    need_pay: bool = False
    req_id: str | None = None
    amount: str | None = None
    assign_name: str | None = None

    def __repr__(self) -> str:
        return (
            f"AssignResult("
            f"ok={self.ok}, "
            f"need_pay={self.need_pay}, "
            f"message={self.message!r}"
            f")"
        )


@dataclass
class StartAuctionResult:
    '''Result of starting auction or selling asset.'''

    ok: bool
    req_id: str | None = None

    def __repr__(self) -> str:
        return f"StartAuctionResult(ok={self.ok}, req_id={self.req_id!r})"


@dataclass
class NftTransferRecipient:
    '''Recipient info for NFT transfer.'''

    myself: bool
    recipient: str
    name: str
    photo_url: str | None = None

    def __repr__(self) -> str:
        return (
            f"NftTransferRecipient("
            f"myself={self.myself}, "
            f"name='{self.name}', "
            f"recipient='{self.recipient[:16]}...'"
            f")"
        )


@dataclass
class NftTransferRequest:
    '''Result of initNftTransferRequest.'''

    req_id: str
    myself: bool
    item_title: str
    content: str
    button: str

    def __repr__(self) -> str:
        return (
            f"NftTransferRequest("
            f"req_id='{self.req_id}', "
            f"item_title='{self.item_title}'"
            f")"
        )


@dataclass
class LoginCodeResult:
    '''Result of a pending login code request.'''

    number: str
    code: str | None
    active_sessions: int

    def __repr__(self) -> str:
        code_str = f"'{self.code}'" if self.code else "None"
        return (
            f"LoginCodeResult("
            f"number='{self.number}', "
            f"code={code_str}, "
            f"active_sessions={self.active_sessions}"
            f")"
        )


@dataclass
class TerminateSessionsResult:
    '''Result of terminating anonymous number sessions.'''

    number: str
    message: str | None

    def __repr__(self) -> str:
        return (
            f"TerminateSessionsResult("
            f"number='{self.number}', "
            f"message={self.message!r}"
            f")"
        )


@dataclass
class BatchItemResult:
    '''
    Result of a single item within a batch operation.

    The type field indicates the purchase kind: "stars", "premium", or "ton".
    The amount field holds star count or TON amount for stars/ton types,
    or month count for premium type.
    '''

    type: str
    username: str
    amount: int
    ok: bool
    result: Any = None
    error: str | None = None
    chunk_index: int = 0

    def __repr__(self) -> str:
        if self.ok:
            return (
                f"BatchItemResult("
                f"type='{self.type}', "
                f"username='{self.username}', "
                f"amount={self.amount}, "
                f"ok=True, "
                f"chunk={self.chunk_index}"
                f")"
            )
        return (
            f"BatchItemResult("
            f"type='{self.type}', "
            f"username='{self.username}', "
            f"amount={self.amount}, "
            f"ok=False, "
            f"error='{self.error}', "
            f"chunk={self.chunk_index}"
            f")"
        )


@dataclass
class BatchResult:
    '''
    Result of a batch purchase operation.

    Items are grouped into chunks based on wallet version message limits
    (4 for V4R2, 255 for V5R1). Each chunk is sent as a single TON
    transaction with multiple inline messages. The chunks_sent field
    indicates how many on-chain transactions were broadcast.
    '''

    total: int
    succeeded: int
    failed: int
    chunks_sent: int
    items: list[BatchItemResult] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"BatchResult("
            f"total={self.total}, "
            f"succeeded={self.succeeded}, "
            f"failed={self.failed}, "
            f"chunks_sent={self.chunks_sent}"
            f")"
        )