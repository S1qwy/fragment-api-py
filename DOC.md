## <img src="https://img.shields.io/badge/-Installation_&_Requirements-black?style=flat-square" valign="middle">

```bash
pip install fragment-api-py
```

- Python 3.10+
- TON wallet seed phrase (12/18/24 words)
- **Fragment cookies** (`stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`)
- **Tonconsole API Key** (get one for free at [tonconsole.com](https://tonconsole.com/))

---

## <img src="https://img.shields.io/badge/-Quick_Start-black?style=flat-square" valign="middle">

```python
import asyncio
from FragmentAPI import FragmentClient
from FragmentAPI.types.results import EvmPaymentResult

async def main():
    # Initialize with strictly required credentials
    async with FragmentClient(
        seed="24 words...",
        api_key="AF...", # Your Tonconsole API key is strictly required
        cookies={
            "stel_ssid": "...", 
            "stel_token": "...", 
            "stel_dt": "...", 
            "stel_ton_token": "..."
        },
        wallet_version="V5R1",
    ) as client:
        
        # 1. Wallet info
        wallet = await client.get_wallet()
        print(f"Balance: {wallet.balance_ton} TON, {wallet.balance_usdt} USDT")
        
        # 2. Purchase stars
        result = await client.purchase_stars("@durov", 100)
        print(f"TX: {result.transaction_id}")
        
        # 3. Execute batch operations
        batch = await client.batch_purchase([
            {"type": "premium", "username": "@durov", "months": 3},
            {"type": "stars", "username": "@telegram", "amount": 250}
        ])
        print(f"Batch Succeeded: {batch.succeeded}/{batch.total}")

        # 4. EVM payment (returns invoice)
        evm_result = await client.purchase_stars("@durov", 50, payment_method="usdc_base")
        if isinstance(evm_result, EvmPaymentResult):
            inv = evm_result.invoice
            print(f"Send {inv.invoice_amount} {inv.token_symbol} to {inv.invoice_address}")
            print(f"Chain: {inv.invoice_chain_name}")

asyncio.run(main())
```

---

## <img src="https://img.shields.io/badge/-Auto_Authentication-black?style=flat-square" valign="middle">

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # Automatic authentication via TON wallet and Telegram
    cookies = await FragmentClient.authenticate(
        seed="24 words...",
        wallet_version="V5R1",
        phone="+71234567890"  # Optional: omit for QR code flow
    )
    
    # Use obtained cookies alongside your Tonconsole API key
    async with FragmentClient(
        seed="24 words...", 
        api_key="AF...",
        cookies=cookies
    ) as client:
        profile = await client.get_profile()
        print(f"Logged in as: {profile.name}")

asyncio.run(main())
```

---

## <img src="https://img.shields.io/badge/-EVM_Payment_Methods-black?style=flat-square" valign="middle">

| Method | Chain | Token | Flow |
|--------|-------|-------|------|
| `ton` | TON | TON | Automatic TX |
| `usdt_ton` | TON | USDT | Automatic TX |
| `usdt_eth` | Ethereum | USDT | Returns invoice |
| `usdt_pol` | Polygon | USDT | Returns invoice |
| `usdc_eth` | Ethereum | USDC | Returns invoice |
| `usdc_base` | BASE | USDC | Returns invoice |
| `usdc_pol` | Polygon | USDC | Returns invoice |

---

## <img src="https://img.shields.io/badge/-Client_Configuration-black?style=flat-square" valign="middle">

### `FragmentClient`
The main entry point for the Fragment API library.
```python
FragmentClient(
    seed: str,
    wallet_version: str = "V5R1",
    cookies: dict | str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
    stats_enabled: bool = False
)
```

---

## <img src="https://img.shields.io/badge/-API_Methods-black?style=flat-square" valign="middle">

### Authentication & Account
* `authenticate(seed, wallet_version="V5R1", phone=None, print_qr=True, on_status=None, timeout=30.0) -> dict[str, str]`
  Static method to authenticate via TON proof and Telegram OAuth. Returns dictionary of session cookies.
* `get_profile() -> ProfileInfo`
  Get Fragment account profile information, verified status, and linked wallet.
* `get_wallet() -> WalletInfo`
  Return address, state, TON and USDT balance of the configured wallet.
* `get_sessions() -> list[SessionInfo]`
  Get active Fragment sessions.
* `terminate_session(session_id: str) -> bool`
  Terminate a specific Fragment session by its ID.

### Purchases & Top-ups
* `purchase_stars(username: str, amount: int, show_sender: bool = True, payment_method: str = "ton") -> StarsResult | EvmPaymentResult`
  Send Telegram Stars to a user.
* `purchase_premium(username: str, months: int, show_sender: bool = True, payment_method: str = "ton") -> PremiumResult | EvmPaymentResult`
  Gift Telegram Premium to a user (3, 6, or 12 months).
* `topup_ton(username: str, amount: int, show_sender: bool = True) -> AdsTopupResult`
  Top up TON to a recipient's Telegram Ads balance.
* `batch_purchase(items: list[dict[str, Any]], payment_method: str = "ton") -> BatchResult`
  Execute multiple Stars, Premium, or Ads top-up purchases in grouped batches. Supports `ton` and `usdt_ton`.

### Giveaways
* `giveaway_stars(channel: str, winners: int, amount: int, payment_method: str = "ton") -> GiveawayStarsResult | EvmPaymentResult`
  Run a Telegram Stars giveaway in a specific channel.
* `giveaway_premium(channel: str, winners: int, months: int = 3, payment_method: str = "ton") -> GiveawayPremiumResult | EvmPaymentResult`
  Run a Telegram Premium giveaway in a specific channel.

### Recipient Search
* `get_stars_recipient(username: str) -> RecipientInfo | None`
* `get_premium_recipient(username: str, months: int = 3) -> RecipientInfo | None`
* `get_ads_topup_recipient(username: str) -> RecipientInfo | None`
* `get_giveaway_stars_recipient(channel: str, winners: int = 1, amount: int = 500) -> RecipientInfo | None`
* `get_giveaway_premium_recipient(channel: str, winners: int = 1, months: int = 3) -> RecipientInfo | None`

### Marketplace & Auctions
* `search_usernames(query="", sort=None, filter=None, offset_id=None) -> UsernamesResult`
  Search Fragment marketplace for Telegram usernames.
* `search_numbers(query="", sort=None, filter=None, offset_id=None) -> NumbersResult`
  Search Fragment marketplace for anonymous Telegram numbers.
* `search_gifts(query="", collection=None, sort=None, filter=None, view=None, attr=None, offset=None) -> GiftsResult`
  Search Fragment gifts marketplace with optional attribute filters.
* `place_bid(item_type: int, slug: str, bid: int) -> BidResult`
  Place a bid or buy-now on a Fragment marketplace item. (`1` = Username, `3` = Number, `5` = Gift).
* `start_auction(item_type: int, slug: str, min_amount: int, max_amount: int = 0) -> StartAuctionResult`
  Start an auction for a username or gift you own.
* `sell_asset(item_type: int, slug: str, price: int) -> StartAuctionResult`
  Sell a username or gift at a fixed price.

### Asset Information & History
* `get_username_info(username: str) -> UsernameInfo`
  Get detailed marketplace info (bids, status, owner) about a username.
* `get_number_info(number: str) -> NumberInfo`
  Get detailed marketplace info about an anonymous number.
* `get_gift_info(slug: str) -> GiftInfo`
  Get detailed marketplace info about a specific gift.
* `get_stars_prices() -> StarsPrices` / `get_stars_price(quantity: int) -> StarsPrice`
  Fetch fiat and TON rates for Telegram Stars.
* `get_premium_prices() -> PremiumPrices`
  Fetch fiat and TON rates for Telegram Premium.
* `get_stars_history(sort="desc") -> list[StarsTransaction]`
* `get_premium_history(sort="desc") -> list[PremiumTransaction]`
* `get_topup_history(sort="asc") -> list[TopupTransaction]`
* `get_orders_history(item_type: int, username: str, offset_id: str) -> dict`
* `get_owners_history(item_type: int, username: str, offset_id: str) -> dict`

### My Assets & Assignments
* `get_my_assets(item_type: str = "usernames") -> MyAssetsResult`
  List assets currently owned by your account.
* `get_my_bids(item_type: str = "usernames", sort="desc") -> MyBidsResult`
  List your bidding history.
* `get_assign_accounts(item_type: int, slug: str) -> AssignAccountsResult`
  Get list of Telegram accounts available for asset assignment.
* `assign_to_telegram(item_type: int, slug: str, assign_to: str | None = None) -> AssignResult`
  Assign an owned username or gift to a specific Telegram account.

### NFTs & Withdrawals
* `search_nft_transfer_recipient(query: str) -> NftTransferRecipient | None`
* `init_nft_transfer(slug: str, recipient: str) -> NftTransferRequest`
* `transfer_nft(req_id: str, show_sender: bool = True) -> TransactionResult`
* `init_nft_withdrawal(transaction: str, keep_gift: bool = False) -> NftWithdrawalInitResult`
* `confirm_nft_withdrawal(transaction: str, confirm_hash: str, keep_gift: bool = False) -> NftWithdrawalConfirmResult`
* `get_nft_withdrawal_state(transaction: str) -> dict`
* `init_stars_withdrawal(transaction: str, withdrawal_data: str) -> StarsWithdrawalInitResult`
* `confirm_stars_withdrawal(transaction: str, withdrawal_data: str, confirm_hash: str) -> StarsWithdrawalConfirmResult`
* `get_stars_withdrawal_state(transaction: str) -> StarsWithdrawalState`

### Anonymous Numbers (+888)
* `get_login_code(number: str) -> LoginCodeResult`
  Fetch the current pending login code for an anonymous number.
* `toggle_login_codes(number: str, can_receive: bool) -> None`
  Enable or disable login code delivery for a number.
* `terminate_sessions(number: str) -> TerminateSessionsResult`
  Terminate all active Telegram sessions tied to an anonymous number.

### Advanced
* `confirm_request(req_id: str, boc: str, referer: str) -> dict`
  Confirm a transaction payload locally manually.
* `call(method: str, data: dict | None = None, page_url: str = FRAGMENT_BASE_URL) -> dict`
  Send a raw, generic JSON RPC payload to the Fragment API.

---

## <img src="https://img.shields.io/badge/-Models_&_Types-black?style=flat-square" valign="middle">

Below are the primary dataclass models returned by the SDK methods:

### Results & Invoices
* **`BatchResult`**: `total`, `succeeded`, `failed`, `chunks_sent`, `items` (list of `BatchItemResult`).
* **`BatchItemResult`**: `type`, `username`, `amount`, `ok`, `result`, `error`, `chunk_index`.
* **`EvmPaymentResult`**: `item_kind`, `target`, `amount`, `payment_method`, `invoice` (`EvmInvoice`).
* **`EvmInvoice`**: `req_id`, `invoice_address`, `invoice_token`, `invoice_chain_id`, `invoice_chain_name`, `invoice_amount_hex`, `invoice_amount`, `invoice_amount_raw`, `token_symbol`, `token_decimals`, `expires_at`, `payment_method`, `api_hash`, `page_url`.
* **`TransactionResult`**: `tx_hash`, `boc`, `seqno_before`, `seqno_after`, `balance_before`, `balance_after`, `confirmed`.
* **`StarsResult`** / **`PremiumResult`**: `transaction_id`, `username`, `amount`, `payment_method`.
* **`GiveawayStarsResult`** / **`GiveawayPremiumResult`**: `transaction_id`, `channel`, `winners`, `amount`, `payment_method`.
* **`AdsTopupResult`**: `transaction_id`, `username`, `amount`.
* **`BidResult`**: `transaction_id`, `item_type`, `slug`, `bid`, `confirm_method`, `confirm_id`.

### User & Asset Info
* **`ProfileInfo`**: `name`, `username`, `photo_url`, `identity_verified`, `wallet_address`, `wallet_label`, `wallet_verified`.
* **`WalletInfo`**: `address`, `state`, `balance_ton`, `balance_usdt`.
* **`SessionInfo`**: `session_id`, `device`, `location`, `date`, `is_current`.
* **`RecipientInfo`**: `recipient`, `name`, `photo_url`, `myself`.
* **`UsernameInfo`** / **`NumberInfo`** / **`GiftInfo`**: Contains comprehensive info: `status`, `item_type`, `ton_rate`, `auction` (`AuctionInfo`), `purchased_date`, `owner_wallet`, and complete histories (`bid_history`, `owner_history`).

### Marketplace Data
* **`UsernamesResult`** / **`NumbersResult`**: `items` (list of dicts), `next_offset_id`.
* **`GiftsResult`**: `items` (list of dicts), `next_offset`.
* **`AuctionInfo`**: `highest_bid`, `bid_step`, `minimum_bid`, `sell_price`, `buy_now_price`.
* **`BidHistoryEntry`** / **`OwnerHistoryEntry`**: `price`, `date`, `wallet`.
* **`MyAssetsResult`** / **`MyBidsResult`**: `items` (list of `MyAsset` or `MyBid`), `ton_rate`, `total_count`.
* **`StarsPrices`** / **`PremiumPrices`**: `packages`/`options`, `ton_rate`.

### Operations & Actions
* **`AssignResult`**: `ok`, `message`, `need_pay`, `req_id`, `amount`, `assign_name`.
* **`AssignAccountsResult`**: `accounts` (list of `TelegramAccount`), `can_disable`.
* **`LoginCodeResult`**: `number`, `code`, `active_sessions`.
* **`TerminateSessionsResult`**: `number`, `message`.
* **`StartAuctionResult`**: `ok`, `req_id`.
* **`NftTransferRecipient`**: `myself`, `recipient`, `name`, `photo_url`.
* **`NftWithdrawalInitResult`** / **`StarsWithdrawalInitResult`**: `ok`, `confirm_message`, `confirm_button`, `confirm_hash`, `error`.
* **`NftWithdrawalConfirmResult`** / **`StarsWithdrawalConfirmResult`**: `ok`, `need_update`, `mode`, `html`, `error`.

---

## <img src="https://img.shields.io/badge/-Exceptions-black?style=flat-square" valign="middle">

All SDK exceptions inherit from `FragmentBaseError`.

- **`ClientError`**
  - **`ConfigError`**: Raised when required client parameters are missing or invalid (e.g., missing keys, invalid wallet version, out-of-range purchase amounts).
  - **`CookieError`**: Raised when Fragment cookies are missing or malformed.
- **`OperationError`**
  - **`WalletError`**: Issues tied to the TON wallet itself (e.g., insufficient balance to cover tx and gas).
  - **`ProxyError`**: Connection issues with proxy or fallback node.
  - **`UnexpectedError`**: General wrapper for unexpected internal exceptions.
- **`FragmentAPIError`**
  - **`FragmentPageError`**: Raised when Fragment pages cannot be fetched or HTML structures change unexpectedly (e.g., missing API hashes).
  - **`UserNotFoundError`**: Target Telegram user is not found on Fragment.
  - **`AnonymousNumberError`**: Number is not associated with your account or session termination failed.
  - **`TransactionError`**: Failed to broadcast a TON transaction or invalid Fragment payloads.
    - **`ConfirmationTimeout`**: Transaction was sent but seqno/balance confirmation was not received in time.
    - **`SeqnoError`**: Failed to fetch or validate wallet seqno.
  - **`ParseError`**: API response could not be parsed as valid JSON/HTML.
  - **`VerificationError`**: Triggered when Fragment restricts operations due to missing KYC verification.

---

## <img src="https://img.shields.io/badge/-Support_&_License-black?style=flat-square" valign="middle">

**Reporting Errors**  
Create an [Issue](https://github.com/s1qwy/fragment-api-py/issues) or message in the [Telegram chat](https://t.me/fragment_api_py).

**Support the Project**  
If you find this library useful, consider supporting its development:

<p align="center">
  <a href="https://app.tonkeeper.com/transfer/UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj">
    <img src="https://img.shields.io/badge/Donate-TON-0098ea?style=for-the-badge&logo=ton&logoColor=white" alt="Donate TON">
  </a>
</p>

<p align="center">
  <code>UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj</code>
</p>

**License**  
**MIT License** — free for commercial and personal use.

---

<p align="center">
  <a href="https://github.com/s1qwy/fragment-api-py">GitHub</a> •
  <a href="https://t.me/fragment_api_py">Telegram</a>
</p>
