# Fragment API Python SDK — Full Documentation

Complete reference for **fragment-api-py v12.0.0**.

---

## Table of Contents

- [Installation & Requirements](#installation--requirements)
- [Operating Modes](#operating-modes)
- [Client Configuration](#client-configuration)
  - [FragmentClient Constructor](#fragmentclient-constructor)
  - [Cookie Formats](#cookie-formats)
  - [Session Storage](#session-storage)
  - [Properties](#properties)
- [Authentication](#authentication)
- [Payment Methods](#payment-methods)
- [API Methods](#api-methods)
  - [Wallet](#wallet)
  - [Purchases & Top-ups](#purchases--top-ups)
  - [Batch Purchases](#batch-purchases)
  - [Giveaways](#giveaways)
  - [Recipient Search](#recipient-search)
  - [Marketplace Search](#marketplace-search)
  - [Asset Information](#asset-information)
  - [Price Queries](#price-queries)
  - [Transaction History](#transaction-history)
  - [My Assets & Bids](#my-assets--bids)
  - [Assignment](#assignment)
  - [Auction & Selling](#auction--selling)
  - [Offers](#offers)
  - [Gateway](#gateway)
  - [Ads Recharge](#ads-recharge)
  - [NFT Transfers](#nft-transfers)
  - [NFT Withdrawals](#nft-withdrawals)
  - [Stars Withdrawals](#stars-withdrawals)
  - [Ads Withdrawals](#ads-withdrawals)
  - [Anonymous Numbers (+888)](#anonymous-numbers-888)
  - [Sessions](#sessions)
  - [Low-Level / Advanced](#low-level--advanced)
- [Data Types & Models](#data-types--models)
  - [Purchase & Transaction Results](#purchase--transaction-results)
  - [EVM Payment Types](#evm-payment-types)
  - [Marketplace Item Info](#marketplace-item-info)
  - [Marketplace Search Results](#marketplace-search-results)
  - [Price Models](#price-models)
  - [History Models](#history-models)
  - [Account & Profile Models](#account--profile-models)
  - [Asset Management Models](#asset-management-models)
  - [NFT & Withdrawal Models](#nft--withdrawal-models)
  - [Gateway & Ads Recharge Models](#gateway--ads-recharge-models)
  - [Offer Models](#offer-models)
  - [Subscription Models](#subscription-models)
  - [Anonymous Number Models](#anonymous-number-models)
  - [Batch Models](#batch-models)
  - [Auction Models](#auction-models)
  - [Helper Models](#helper-models)
- [Exceptions](#exceptions)
  - [Hierarchy](#exception-hierarchy)
  - [Base Exceptions](#base-exceptions)
  - [Client Exceptions](#client-exceptions)
  - [API Exceptions](#api-exceptions)
  - [Operation Exceptions](#operation-exceptions)
- [Constants & Limits](#constants--limits)
- [Examples](#examples)
  - [No-KYC Mode — Purchase Stars](#no-kyc-mode--purchase-stars)
  - [No-KYC Mode — Prepared Transaction](#no-kyc-mode--prepared-transaction)
  - [Full Mode — Purchase Stars](#full-mode--purchase-stars)
  - [Batch Purchase](#batch-purchase-example)
  - [EVM Payment Flow](#evm-payment-flow)
  - [Search Marketplace](#search-marketplace)
  - [Anonymous Number Management](#anonymous-number-management)
  - [NFT Transfer](#nft-transfer-example)
  - [Auto Authentication](#auto-authentication-example)
- [Support & License](#support--license)

---

## Installation & Requirements

```bash
pip install fragment-api-py
```

| Requirement | Details |
|---|---|
| Python | 3.10 or higher |
| TON wallet seed phrase | 12, 18, or 24 words |
| Fragment cookies | `stel_ssid`, `stel_dt`, `stel_token` (minimum); `stel_ton_token` (for wallet operations) |
| API key | Tonconsole or Toncenter key (required for wallet/transaction operations) |

Get a free Tonconsole API key at [tonconsole.com](https://tonconsole.com/).

---

## Operating Modes

The library supports four operating modes depending on which parameters you provide:

| Mode | Required Parameters | Available Operations |
|---|---|---|
| **Full mode** | `cookies` (with `stel_ton_token`) + `seed` + `api_key` | All operations: purchases, giveaways, bids, wallet, NFT, withdrawals, gateway, offers |
| **EVM-only mode** | `cookies` (without `stel_ton_token`) | EVM payment methods, read-only search/info methods |
| **Read-only mode** | `cookies` only (no `seed`) | Search, item info, price queries |
| **No-KYC mode** | `marketapp_token` (optional, uses default) + `seed` + `api_key` (optional) | Stars, Premium, Giveaways, Ads topup/recharge, price lookups, recipient search. If seed+api_key provided, executes automatically; otherwise returns `PreparedTransaction` |

**No-KYC mode** is the major new feature in v12.0.0. It allows you to use the library without Fragment.com cookies or KYC verification. All operations are powered by the MarketApp API.

---

## Client Configuration

### FragmentClient Constructor

```python
FragmentClient(
    cookies: dict | str | None = None,
    seed: str | None = None,
    api_key: str | None = None,
    api_provider: str = "tonapi",
    wallet_version: str = "V5R1",
    timeout: float = 30.0,
    proxy: str | None = None,
    session_storage: SessionStorage | None = None,
    session_id: str | None = None,
    auto_refresh_cookies: bool = False,
    marketapp_token: str | None = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `cookies` | `dict \| str \| None` | `None` | Fragment session cookies. Optional in No-KYC mode. |
| `seed` | `str \| None` | `None` | TON wallet mnemonic phrase (12, 18, or 24 words separated by spaces). Required for any on-chain transaction. |
| `api_key` | `str \| None` | `None` | API key for TON blockchain interactions. Required alongside `seed` for wallet operations. |
| `api_provider` | `str` | `"tonapi"` | Blockchain API provider. Accepted values: `"tonapi"`, `"toncenter"`. |
| `wallet_version` | `str` | `"V5R1"` | TON wallet contract version. Accepted values: `"V4R2"`, `"V5R1"`. V5R1 supports up to 255 messages per transaction; V4R2 supports up to 4. |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds for all Fragment API calls. |
| `proxy` | `str \| None` | `None` | Proxy URL (http, socks5). Example: `"socks5://user:pass@host:port"`. |
| `session_storage` | `SessionStorage \| None` | `None` | Storage backend for cookie persistence. |
| `session_id` | `str \| None` | `None` | Identifier for the session in storage. |
| `auto_refresh_cookies` | `bool` | `False` | Automatically refresh expired cookies. |
| `marketapp_token` | `str \| None` | `None` | Custom MarketApp API key for No-KYC mode. Uses default token if not provided. |

### Cookie Formats

The `cookies` parameter accepts three formats:

**Dict:**
```python
cookies = {
    "stel_ssid": "abc123",
    "stel_dt": "-180",
    "stel_token": "xyz789",
    "stel_ton_token": "tok456"
}
```

**JSON string:**
```python
cookies = '{"stel_ssid": "abc123", "stel_dt": "-180", "stel_token": "xyz789"}'
```

**Cookie header string:**
```python
cookies = "stel_ssid=abc123; stel_dt=-180; stel_token=xyz789; stel_ton_token=tok456"
```

**Required cookie keys:**

| Key | Required | Description |
|---|---|---|
| `stel_ssid` | Always | Session identifier |
| `stel_dt` | Always | Device timezone offset |
| `stel_token` | Always | Authentication token |
| `stel_ton_token` | For wallet/write ops | TON wallet connection token. Set after connecting a TON wallet on fragment.com |

### Session Storage

The library provides built-in session storage backends for persisting cookies across restarts.

#### `FragmentClient.from_storage()` (classmethod)

Creates a client instance using stored session cookies.

```python
client = await FragmentClient.from_storage(
    session_storage=storage,
    session_id="my_session",
    seed="word1 word2 ... word24",
    api_key="AF...",
    api_provider="tonapi",
    wallet_version="V5R1",
    timeout=30.0,
    proxy=None,
    auto_refresh_cookies=False,
    marketapp_token=None,
)
```

#### `FileSessionStorage`

Stores cookies as JSON files on disk.

```python
from FragmentAPI import FileSessionStorage

storage = FileSessionStorage(
    directory=".fragment_sessions",
    file_extension=".json",
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `directory` | `str \| Path` | `".fragment_sessions"` | Directory for session files. |
| `file_extension` | `str` | `".json"` | File extension for session files. |

#### `RedisSessionStorage`

Stores cookies in Redis with optional TTL.

```python
from FragmentAPI import RedisSessionStorage

storage = RedisSessionStorage(
    redis_url="redis://localhost:6379/0",
    prefix="fragment:session:",
    ttl=3600,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `redis_url` | `str` | `"redis://localhost:6379/0"` | Redis connection URL. |
| `prefix` | `str` | `"fragment:session:"` | Key prefix for session entries. |
| `ttl` | `int \| None` | `None` | Time-to-live in seconds. |

**Example:**

```python
from FragmentAPI import FragmentClient, FileSessionStorage

storage = FileSessionStorage(directory=".fragment_sessions")

# Load existing session or authenticate
client = await FragmentClient.from_storage(
    session_storage=storage,
    session_id="my_account",
    seed="word1 word2 ... word24",
    api_key="AF...",
)

# Cookies are automatically saved on exit when used as context manager
async with client:
    profile = await client.get_profile()
```

### Properties

| Property | Type | Description |
|---|---|---|
| `has_wallet` | `bool` | `True` if both `seed` and `api_key` are configured. |
| `has_ton_token` | `bool` | `True` if `stel_ton_token` cookie is present and non-empty. |
| `has_cookies` | `bool` | `True` if Fragment cookies are configured. |
| `nokyc_mode` | `bool` | `True` if operating in No-KYC mode (no cookies). |
| `session_storage` | `SessionStorage \| None` | Returns the configured session storage backend. |

---

## Authentication

### `FragmentClient.authenticate()` (static)

Performs full Fragment authentication using TON wallet proof and optionally Telegram OAuth. Returns session cookies that can be used to construct a `FragmentClient`.

```python
cookies = await FragmentClient.authenticate(
    seed="word1 word2 ... word24",
    wallet_version="V5R1",
    phone="+71234567890",
    print_qr=True,
    on_status=my_callback,
    timeout=30.0,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `seed` | `str` | **(required)** | TON wallet mnemonic phrase. |
| `wallet_version` | `str` | `"V5R1"` | Wallet contract version (`"V4R2"` or `"V5R1"`). |
| `phone` | `str \| None` | `None` | If provided, uses phone-confirmation flow instead of QR code. Include country code (e.g. `"+71234567890"`). |
| `print_qr` | `bool` | `True` | If `True` and `phone` is `None`, prints a QR code to the terminal for Telegram scanning. |
| `on_status` | `callable \| None` | `None` | Optional callback `(status_name: str, payload: Any)` called during auth flow. Statuses: `"qr_link"`, `"refresh"`, `"consumed"`, `"confirmed"`, `"phone_sent"`. |
| `timeout` | `float` | `30.0` | HTTP timeout in seconds. |

**Returns:** `dict[str, str]` — Session cookies dictionary.

**Auth flow:**
1. Loads Fragment homepage and extracts TON proof challenge.
2. Signs the challenge with the wallet private key.
3. Sends `checkTonProofAuth` to Fragment API.
4. If `stel_token` is already set, returns cookies immediately.
5. Otherwise, initiates Telegram OAuth (QR or phone).
6. Polls until user confirms, then finalizes login.

---

## Payment Methods

| Method String | Chain | Token | Behavior |
|---|---|---|---|
| `"gram"` | TON (Gram) | GRAM | Automatic on-chain transaction. Alias for `"ton"`. |
| `"ton"` | TON (Gram) | GRAM | Automatic on-chain transaction. Internal API value. |
| `"usdt_ton"` | TON (Gram) | USDT | Automatic on-chain USDT transfer. |
| `"usdt_eth"` | Ethereum | USDT | Returns `EvmPaymentResult` with invoice details. |
| `"usdt_pol"` | Polygon | USDT | Returns `EvmPaymentResult` with invoice details. |
| `"usdc_eth"` | Ethereum | USDC | Returns `EvmPaymentResult` with invoice details. |
| `"usdc_base"` | BASE | USDC | Returns `EvmPaymentResult` with invoice details. |
| `"usdc_pol"` | Polygon | USDC | Returns `EvmPaymentResult` with invoice details. |

**Notes:**
- `"gram"` and `"ton"` are interchangeable.
- GRAM on-chain methods (`gram`, `ton`, `usdt_ton`) require `seed` + `api_key`.
- EVM methods return an `EvmPaymentResult` containing an `EvmInvoice` that you must fulfill externally.
- Batch purchases only support GRAM methods (`gram`, `ton`, `usdt_ton`).
- Ads top-up only supports GRAM methods.
- **v12.0.0:** `usdt_gram` has been removed; use `usdt_ton` instead.

---

## API Methods

### Wallet

#### `get_wallet() -> WalletInfo`

Returns address, state, GRAM balance, and USDT balance of the configured wallet.

**Requires:** `seed` + `api_key` + `stel_ton_token` (or No-KYC mode with wallet configured).

```python
wallet = await client.get_wallet()
print(wallet.address)       # "UQ..."
print(wallet.state)         # "active"
print(wallet.gram_balance)  # 12.5432
print(wallet.usdt_balance)  # 100.0
```

---

### Purchases & Top-ups

#### `purchase(items_or_type, username=None, amount=None, months=None, show_sender=True, payment_method="gram") -> PurchaseResult | BatchResult | EvmPaymentResult | PreparedTransaction | NoKycBatchResult`

Unified purchase method supporting both single and batch operations.

**In No-KYC mode:** Uses MarketApp API. Returns `PreparedTransaction` if wallet is not configured, otherwise executes automatically and returns `PurchaseResult`.

**Single purchase (type string):**
```python
result = await client.purchase("stars", username="durov", amount=100)
```

**Single purchase (dict):**
```python
result = await client.purchase({"type": "stars", "username": "durov", "amount": 100})
```

**Single purchase (PurchaseItem):**
```python
from FragmentAPI.types.results import PurchaseItem
item = PurchaseItem(type="stars", username="durov", amount=100)
result = await client.purchase(item)
```

**Batch purchase (list):**
```python
result = await client.purchase([
    {"type": "stars", "username": "durov", "amount": 100},
    {"type": "premium", "username": "telegram", "months": 3},
])
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `items_or_type` | `list \| dict \| PurchaseItem \| str` | **(required)** | List of items for batch, single item dict/PurchaseItem, or type string (`"stars"`, `"premium"`, `"gram"`, `"ton"`). |
| `username` | `str \| None` | `None` | Telegram username (when `items_or_type` is a string). |
| `amount` | `int \| None` | `None` | Stars quantity (50–10,000,000) or GRAM amount (1–1,000,000,000). |
| `months` | `int \| None` | `None` | Premium duration: `3`, `6`, or `12`. |
| `show_sender` | `bool` | `True` | Whether to show sender name in Telegram notification. |
| `payment_method` | `str` | `"gram"` | Payment method string. See [Payment Methods](#payment-methods). |

**Returns:**
- `PurchaseResult` — For single GRAM on-chain purchases.
- `EvmPaymentResult` — For single EVM purchases.
- `BatchResult` — For list inputs in full mode.
- `NoKycBatchResult` — For list inputs in No-KYC mode.
- `PreparedTransaction` — In No-KYC mode when wallet is not configured.

---

#### `purchase_stars(username, amount, show_sender=True, payment_method="gram") -> PurchaseResult | EvmPaymentResult | PreparedTransaction`

Send Telegram Stars to a user. Convenience wrapper around `purchase()`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `username` | `str` | **(required)** | Telegram username of the recipient. |
| `amount` | `int` | **(required)** | Number of Stars to send. Range: 50–10,000,000. |
| `show_sender` | `bool` | `True` | Show sender name in notification. |
| `payment_method` | `str` | `"gram"` | Payment method. |

---

#### `purchase_premium(username, months, show_sender=True, payment_method="gram") -> PurchaseResult | EvmPaymentResult | PreparedTransaction`

Gift Telegram Premium to a user.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `username` | `str` | **(required)** | Telegram username of the recipient. |
| `months` | `int` | **(required)** | Premium duration. Accepted values: `3`, `6`, `12`. |
| `show_sender` | `bool` | `True` | Show sender name in notification. |
| `payment_method` | `str` | `"gram"` | Payment method. |

**Raises:** `AlreadySubscribedError` if the user already has active Premium.

---

#### `topup_gram(username, amount, show_sender=True) -> PurchaseResult | PreparedTransaction`

Top up GRAM to a recipient's Telegram Ads balance.

**Requires:** `stel_ton_token` (full mode) or No-KYC mode with wallet configured.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `username` | `str` | **(required)** | Telegram Ads account username. |
| `amount` | `int` | **(required)** | GRAM amount. Range: 1–1,000,000,000. |
| `show_sender` | `bool` | `True` | Show sender name. |

**Note:** Only GRAM payment method is supported for ads top-ups.

---

#### `topup_ton(username, amount, show_sender=True) -> PurchaseResult | PreparedTransaction`

Alias for `topup_gram()`. Backward-compatible.

---

### Batch Purchases

#### `batch_purchase(items, payment_method="gram") -> BatchResult | NoKycBatchResult`

Execute multiple purchases as batched on-chain TON transactions. Messages are automatically chunked based on wallet version limits (V4R2: 4 messages, V5R1: 255 messages per transaction).

In No-KYC mode, each item is processed individually via MarketApp API.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `items` | `list[dict \| PurchaseItem]` | **(required)** | List of purchase items. Each item must contain `type`, `username`, and either `amount` or `months`. |
| `payment_method` | `str` | `"gram"` | Only GRAM methods supported: `"gram"`, `"ton"`, `"usdt_ton"`. |

**Item dict format:**
```python
{"type": "stars", "username": "durov", "amount": 100}
{"type": "premium", "username": "telegram", "months": 3}
{"type": "gram", "username": "adschannel", "amount": 50}
```

**Returns:** `BatchResult` (full mode) or `NoKycBatchResult` (No-KYC mode) with per-item results.

---

### Giveaways

#### `giveaway_stars(channel, winners, amount, payment_method="gram") -> GiveawayStarsResult | EvmPaymentResult | PreparedTransaction`

Run a Telegram Stars giveaway for a channel.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `str` | **(required)** | Channel username. |
| `winners` | `int` | **(required)** | Number of winners. Range: 1 to `min(amount // 100, 10000)`. |
| `amount` | `int` | **(required)** | Total Stars amount. Must be one of the allowed packages: 500, 1000, 1500, 2500, 5000, 10000, 25000, 35000, 50000, 100000, 150000, 500000, 1000000. |
| `payment_method` | `str` | `"gram"` | Payment method. |

---

#### `giveaway_premium(channel, winners, months=3, payment_method="gram") -> GiveawayPremiumResult | EvmPaymentResult | PreparedTransaction`

Run a Telegram Premium giveaway for a channel.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `str` | **(required)** | Channel username. |
| `winners` | `int` | **(required)** | Number of winners. Range: 1–24,000. |
| `months` | `int` | `3` | Premium duration: `3`, `6`, or `12`. |
| `payment_method` | `str` | `"gram"` | Payment method. |

---

### Recipient Search

These methods resolve a Telegram username to a Fragment-internal recipient ID. Return `None` if not found.

#### `get_stars_recipient(username) -> RecipientInfo | None`

| Parameter | Type | Description |
|---|---|---|
| `username` | `str` | Telegram username to search. |

#### `get_premium_recipient(username, months=3) -> RecipientInfo | None`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `username` | `str` | | Telegram username. |
| `months` | `int` | `3` | Premium duration for price context. |

#### `get_ads_topup_recipient(username) -> RecipientInfo | None`

**Requires:** `stel_ton_token` (full mode) or No-KYC mode.

| Parameter | Type | Description |
|---|---|---|
| `username` | `str` | Telegram Ads account username. |

#### `get_giveaway_stars_recipient(channel, winners=1, amount=500) -> RecipientInfo | None`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `str` | | Channel username. |
| `winners` | `int` | `1` | Number of winners. |
| `amount` | `int` | `500` | Stars amount. |

#### `get_giveaway_premium_recipient(channel, winners=1, months=3) -> RecipientInfo | None`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `str` | | Channel username. |
| `winners` | `int` | `1` | Number of winners. |
| `months` | `int` | `3` | Premium months. |

---

### Marketplace Search

#### `search_usernames(query="", sort=None, filter=None, offset_id=None) -> UsernamesResult`

Search Fragment marketplace for Telegram usernames.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | `""` | Search text. Empty string browses all. |
| `sort` | `str \| None` | `None` | Sort order: `"price_desc"`, `"price_asc"`, `"listed"`, `"ending"`. |
| `filter` | `str \| None` | `None` | Status filter: `"auction"`, `"sale"`, `"sold"`, or `""` (available). |
| `offset_id` | `str \| None` | `None` | Pagination cursor from previous `UsernamesResult.next_offset_id`. |

---

#### `search_numbers(query="", sort=None, filter=None, offset_id=None) -> NumbersResult`

Search Fragment marketplace for anonymous Telegram numbers. Same parameters as `search_usernames`.

---

#### `search_gifts(query="", collection=None, sort=None, filter=None, view=None, attr=None, offset=None) -> GiftsResult`

Search Fragment gifts marketplace.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | `""` | Search text. |
| `collection` | `str \| None` | `None` | Gift collection slug filter. |
| `sort` | `str \| None` | `None` | Sort order. |
| `filter` | `str \| None` | `None` | Status filter. |
| `view` | `str \| None` | `None` | Active attribute tab name. |
| `attr` | `dict[str, list[str]] \| None` | `None` | Attribute filter. Maps trait names to lists of accepted values. Example: `{"Background": ["Red", "Blue"]}`. |
| `offset` | `int \| None` | `None` | Page offset from previous `GiftsResult.next_offset`. |

---

### Asset Information

#### `get_username_info(username) -> UsernameInfo`

Get detailed information about a Fragment username.

| Parameter | Type | Description |
|---|---|---|
| `username` | `str` | Username to look up (with or without `@`). |

---

#### `get_number_info(number) -> NumberInfo`

Get detailed information about a Fragment anonymous number.

| Parameter | Type | Description |
|---|---|---|
| `number` | `str` | Phone number (with or without `+`, spaces, dashes). |

---

#### `get_gift_info(slug) -> GiftInfo`

Get detailed information about a Fragment gift.

| Parameter | Type | Description |
|---|---|---|
| `slug` | `str` | Gift identifier on Fragment. |

---

### Price Queries

#### `get_stars_prices() -> StarsPrices`

Get all available Telegram Stars package prices. Returns packages with GRAM and USD prices.

#### `get_stars_price(quantity) -> StarsPrice`

Get price for a specific Stars quantity.

| Parameter | Type | Description |
|---|---|---|
| `quantity` | `int` | Number of Stars. |

#### `get_premium_prices() -> PremiumPrices`

Get Telegram Premium subscription prices for all durations (3, 6, 12 months).

---

### Transaction History

All history methods require `stel_ton_token` (full mode).

#### `get_stars_history(sort="desc") -> list[StarsTransaction]`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sort` | `str` | `"desc"` | Sort order: `"desc"` (newest first) or `"asc"` (oldest first). |

#### `get_premium_history(sort="desc") -> list[PremiumTransaction]`

Same parameter as above.

#### `get_topup_history(sort="asc") -> list[TopupTransaction]`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sort` | `str` | `"asc"` | Sort order. |

#### `get_orders_history(item_type, username, offset_id) -> dict[str, Any]`

Load more bid/order history for an item (paginated).

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username), `3` (number), `5` (gift). |
| `username` | `str` | Item identifier. |
| `offset_id` | `str` | Pagination cursor. |

#### `get_owners_history(item_type, username, offset_id) -> dict[str, Any]`

Load more ownership history for an item (paginated). Same parameters as `get_orders_history`.

#### `get_offers_history(item_type, username, offset_id) -> dict[str, Any]`

Load more offer history for an item (paginated). Same parameters as above.

---

### My Assets & Bids

Both methods require `stel_ton_token` (full mode).

#### `get_my_assets(item_type="usernames") -> MyAssetsResult`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item_type` | `str` | `"usernames"` | Asset type: `"usernames"`, `"numbers"`, or `"gifts"`. |

#### `get_my_bids(item_type="usernames", sort="desc") -> MyBidsResult`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item_type` | `str` | `"usernames"` | Asset type: `"usernames"`, `"numbers"`, or `"gifts"`. |
| `sort` | `str` | `"desc"` | Sort order. |

---

### Assignment

#### `get_assign_accounts(item_type, slug) -> AssignAccountsResult`

Get list of Telegram accounts available for asset assignment.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username) or `5` (gift). |
| `slug` | `str` | Item identifier. |

#### `assign_to_telegram(item_type, slug, assign_to=None, wait_for_bot_payment=True) -> AssignResult`

Assign an owned username or gift to a Telegram account.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item_type` | `int` | **(required)** | `1` (username) or `5` (gift). |
| `slug` | `str` | **(required)** | Item identifier. |
| `assign_to` | `str \| None` | `None` | Target Telegram account ID from `get_assign_accounts()`. If `None`, assigns to the default account. |
| `wait_for_bot_payment` | `bool` | `True` | If the target is a bot, Fragment requires a payment. When `True` and wallet is configured, payment is executed automatically. |

---

### Auction & Selling

#### `place_bid(item_type, slug, bid) -> BidResult`

Place a bid or buy-now on a Fragment marketplace item.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username), `3` (number), or `5` (gift). |
| `slug` | `str` | Item identifier on Fragment. |
| `bid` | `int` | Bid amount in GRAM (integer). If equal to buy-now price, executes instant purchase. |

#### `start_auction(item_type, slug, min_amount, max_amount=0) -> StartAuctionResult`

Start an auction for an owned username or gift.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item_type` | `int` | **(required)** | `1` (username) or `5` (gift). |
| `slug` | `str` | **(required)** | Item identifier. |
| `min_amount` | `int` | **(required)** | Minimum bid / starting price in GRAM. |
| `max_amount` | `int` | `0` | If `0`, runs as auction. If equal to `min_amount`, sets a fixed sell price. |

#### `sell_asset(item_type, slug, price) -> StartAuctionResult`

Sell an owned username or gift at a fixed price. Convenience wrapper: calls `start_auction(item_type, slug, price, price)`.

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username) or `5` (gift). |
| `slug` | `str` | Item identifier. |
| `price` | `int` | Fixed sell price in GRAM. |

#### `cancel_auction(item_type, slug) -> TransactionResult`

Cancel an active auction if no bids have been placed.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username), `3` (number), or `5` (gift). |
| `slug` | `str` | Item identifier. |

**Returns:** `TransactionResult`.

#### `subscribe_to_item(item_type, slug) -> SubscriptionResult`

Subscribe to auction update notifications for an item via Telegram.

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username), `3` (number), or `5` (gift). |
| `slug` | `str` | Item identifier. |

**Returns:** `SubscriptionResult` with `ok`, `subscribed`, `item_type`, `slug`.

#### `unsubscribe_from_item(item_type, slug) -> SubscriptionResult`

Unsubscribe from auction update notifications.

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username), `3` (number), or `5` (gift). |
| `slug` | `str` | Item identifier. |

**Returns:** `SubscriptionResult`.

---

### Offers

#### `make_offer(item_type, slug, amount) -> OfferResult`

Make an offer to buy an unlisted username, number, or gift.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `item_type` | `int` | `1` (username), `3` (number), or `5` (gift). |
| `slug` | `str` | Item identifier on Fragment. |
| `amount` | `int` | Offer amount in GRAM. |

**Returns:** `OfferResult` with `transaction_id`, `item_type`, `slug`, `amount`, `req_id`.

---

### Gateway

#### `get_gateway_price(account_id, credits) -> GatewayPriceInfo`

Get price info for Telegram Gateway credits.

| Parameter | Type | Description |
|---|---|---|
| `account_id` | `str` | Gateway account identifier. |
| `credits` | `int` | Number of credits to purchase. |

**Returns:** `GatewayPriceInfo` with `credits`, `gram_price`, `usd_price`.

#### `recharge_gateway(account_id, credits) -> GatewayRechargeResult`

Recharge Telegram Gateway credits via TON payment.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `account_id` | `str` | Gateway account identifier. |
| `credits` | `int` | Number of credits to purchase. |

**Returns:** `GatewayRechargeResult` with `transaction_id`, `account_id`, `credits`, `req_id`.

---

### Ads Recharge

#### `recharge_ads(account_id, amount) -> AdsRechargeResult | PreparedTransaction`

Recharge Telegram Ads account via TON payment.

In No-KYC mode, uses MarketApp API. Returns `PreparedTransaction` if wallet is not configured.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode) or No-KYC mode with wallet configured.

| Parameter | Type | Description |
|---|---|---|
| `account_id` | `str` | Ads account identifier or full Fragment link. |
| `amount` | `int` | GRAM amount to recharge. |

**Returns:** `AdsRechargeResult` or `PreparedTransaction`.

---

### NFT Transfers

#### `search_nft_transfer_recipient(query) -> NftTransferRecipient | None`

Search for a recipient to transfer an NFT gift to.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `query` | `str` | Telegram username or search query. |

#### `init_nft_transfer(slug, recipient) -> NftTransferRequest`

Initialize an NFT transfer request.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `slug` | `str` | Gift slug identifier. |
| `recipient` | `str` | Fragment recipient ID from `search_nft_transfer_recipient()`. |

#### `transfer_nft(req_id, show_sender=True) -> TransactionResult`

Execute the NFT transfer on-chain.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `req_id` | `str` | **(required)** | Request ID from `init_nft_transfer()`. |
| `show_sender` | `bool` | `True` | Show sender name. |

---

### NFT Withdrawals

#### `get_nft_withdrawal_state(transaction) -> dict[str, Any]`

Get NFT withdrawal state from Fragment page.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `transaction` | `str` | Transaction identifier from Fragment. |

#### `init_nft_withdrawal(transaction, keep_gift=False) -> NftWithdrawalInitResult`

Initialize NFT withdrawal to your wallet.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `transaction` | `str` | **(required)** | Transaction identifier. |
| `keep_gift` | `bool` | `False` | If `True`, keeps the gift visible on Telegram after withdrawal. |

#### `confirm_nft_withdrawal(transaction, confirm_hash, keep_gift=False) -> NftWithdrawalConfirmResult`

Confirm NFT withdrawal after initialization.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `transaction` | `str` | **(required)** | Transaction identifier. |
| `confirm_hash` | `str` | **(required)** | Hash from `NftWithdrawalInitResult.confirm_hash`. |
| `keep_gift` | `bool` | `False` | Keep gift visible on Telegram. |

---

### Stars Withdrawals

#### `get_stars_withdrawal_state(transaction) -> StarsWithdrawalState`

Get Stars withdrawal state.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `transaction` | `str` | Transaction identifier. |

#### `init_stars_withdrawal(transaction, withdrawal_data) -> StarsWithdrawalInitResult`

Initialize Stars revenue withdrawal.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `transaction` | `str` | Transaction ID from `StarsWithdrawalState.transaction`. |
| `withdrawal_data` | `str` | Data string from `StarsWithdrawalState.withdrawal_data`. |

#### `confirm_stars_withdrawal(transaction, withdrawal_data, confirm_hash) -> StarsWithdrawalConfirmResult`

Confirm Stars withdrawal.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `transaction` | `str` | Transaction identifier. |
| `withdrawal_data` | `str` | Withdrawal data string. |
| `confirm_hash` | `str` | Hash from `StarsWithdrawalInitResult.confirm_hash`. |

---

### Ads Withdrawals

#### `init_ads_withdrawal(transaction_id) -> AdsWithdrawalInitResult`

Initialize Ads revenue withdrawal to wallet.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Fragment internal transaction identifier. |

**Returns:** `AdsWithdrawalInitResult` with `confirm_hash` if confirmation is needed.

#### `confirm_ads_withdrawal(transaction_id, confirm_hash) -> AdsWithdrawalConfirmResult`

Confirm Ads revenue withdrawal after user approval.

**Requires:** `seed` + `api_key` + `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Fragment internal transaction identifier. |
| `confirm_hash` | `str` | Hash from `init_ads_withdrawal()` response. |

**Returns:** `AdsWithdrawalConfirmResult` with completion status.

---

### Anonymous Numbers (+888)

All methods require `stel_ton_token` (full mode).

#### `get_login_code(number) -> LoginCodeResult`

Fetch the current pending login code for an anonymous number.

| Parameter | Type | Description |
|---|---|---|
| `number` | `str` | Anonymous phone number (with or without `+`). |

#### `toggle_login_codes(number, can_receive) -> None`

Enable or disable login code delivery for an anonymous number.

| Parameter | Type | Description |
|---|---|---|
| `number` | `str` | Anonymous phone number. |
| `can_receive` | `bool` | `True` to enable, `False` to disable. |

#### `terminate_sessions(number) -> TerminateSessionsResult`

Terminate all active Telegram sessions for an anonymous number. Requires a two-step confirmation internally.

| Parameter | Type | Description |
|---|---|---|
| `number` | `str` | Anonymous phone number. |

---

### Sessions

#### `get_sessions() -> list[SessionInfo]`

Get active Fragment sessions. **Requires:** `stel_ton_token` (full mode).

#### `terminate_session(session_id) -> bool`

Terminate a specific Fragment session.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `str` | Session ID from `SessionInfo.session_id`. |

**Returns:** `True` if session was terminated successfully.

#### `refresh_cookies() -> dict[str, str]`

Re-authenticate and refresh session cookies. Requires seed to be configured. Updates internal cookies and saves to storage if configured.

**Requires:** `seed`.

**Returns:** Updated cookies dict.

---

### Low-Level / Advanced

#### `confirm_request(req_id, boc, referer="stars/buy") -> dict[str, Any]`

Send `confirmReq` to Fragment after broadcasting a TON transaction.

**Requires:** `stel_ton_token` (full mode).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `req_id` | `str` | **(required)** | Fragment request ID. |
| `boc` | `str` | **(required)** | Base64-encoded BOC of the sent transaction. |
| `referer` | `str` | `"stars/buy"` | Fragment page path for the referer header. |

#### `call(method, data=None, *, page_url=FRAGMENT_BASE_URL) -> dict[str, Any]`

Send a raw request to the Fragment API.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `method` | `str` | **(required)** | Fragment API method name. |
| `data` | `dict \| None` | `None` | Additional form data. |
| `page_url` | `str` | `FRAGMENT_BASE_URL` | Page URL for referer and hash extraction. |

---

## Data Types & Models

All models are Pydantic V2 models imported from `FragmentAPI.types.models` or `FragmentAPI.types.results`.

### Purchase & Transaction Results

#### `PurchaseResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | TON transaction hash. |
| `type` | `str` | Purchase type: `"stars"`, `"premium"`, `"gram"`, `"ton"`. |
| `username` | `str` | Recipient username. |
| `amount` | `int` | Stars count, months, or GRAM amount depending on type. |
| `payment_method` | `str` | Payment method used. Default: `"gram"`. |

#### `PremiumResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `username` | `str` | Recipient username. |
| `amount` | `int` | Duration in months. |
| `payment_method` | `str` | Payment method. Default: `"gram"`. |

#### `StarsResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `username` | `str` | Recipient username. |
| `amount` | `int` | Stars count. |
| `payment_method` | `str` | Payment method. Default: `"gram"`. |

#### `AdsTopupResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `username` | `str` | Ads account username. |
| `amount` | `int` | GRAM amount topped up. |

#### `GiveawayStarsResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `channel` | `str` | Channel username. |
| `winners` | `int` | Number of winners. |
| `amount` | `int` | Total Stars amount. |
| `payment_method` | `str` | Payment method. Default: `"gram"`. |

#### `GiveawayPremiumResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `channel` | `str` | Channel username. |
| `winners` | `int` | Number of winners. |
| `amount` | `int` | Duration in months. |
| `payment_method` | `str` | Payment method. Default: `"gram"`. |

#### `TransactionResult`

Returned by low-level transaction methods (`transfer_nft`, `cancel_auction`, etc.).

| Field | Type | Description |
|---|---|---|
| `tx_hash` | `str` | Transaction hash string. |
| `boc` | `str \| None` | Base64-encoded BOC of the sent message. Used for `confirm_request`. |
| `seqno_before` | `int \| None` | Wallet seqno before transaction. |
| `seqno_after` | `int \| None` | Wallet seqno after confirmation. |
| `balance_before` | `float \| None` | GRAM balance before transaction. |
| `balance_after` | `float \| None` | GRAM balance after confirmation. |
| `confirmed` | `bool` | `True` if seqno incremented and balance decreased. |

#### `BidResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `item_type` | `int` | Item type: `1` (username), `3` (number), `5` (gift). |
| `slug` | `str` | Item identifier. |
| `bid` | `int` | Bid amount in GRAM. |
| `confirm_method` | `str \| None` | Fragment confirmation method name. |
| `confirm_id` | `str \| None` | Fragment confirmation ID. |

---

### EVM Payment Types

#### `EvmPaymentResult`

Returned when an EVM payment method is used.

| Field | Type | Description |
|---|---|---|
| `item_kind` | `str` | Purchase type: `"stars"`, `"premium"`, `"giveaway_stars"`, `"giveaway_premium"`. |
| `target` | `str` | Recipient username or channel. |
| `amount` | `int` | Stars, months, or GRAM amount. |
| `payment_method` | `str` | EVM payment method string. |
| `invoice` | `EvmInvoice` | Invoice details for on-chain payment. |

#### `EvmInvoice`

| Field | Type | Description |
|---|---|---|
| `req_id` | `str` | Fragment request ID. |
| `invoice_address` | `str` | EVM contract/address to send tokens to. |
| `invoice_token` | `str` | Token contract address (e.g., USDT on Ethereum). |
| `invoice_chain_id` | `int` | EVM chain ID (1 = ETH, 8453 = BASE, 137 = POL). |
| `invoice_chain_name` | `str` | Human-readable chain name: `"ETH"`, `"BASE"`, `"POL"`. |
| `invoice_amount_hex` | `str` | Token amount as hex string (e.g., `"0x5f5e100"`). |
| `invoice_amount` | `float` | Token amount as float (e.g., `10.5`). |
| `invoice_amount_raw` | `int` | Token amount as raw integer (smallest unit). |
| `token_symbol` | `str` | Token symbol: `"USDT"` or `"USDC"`. |
| `token_decimals` | `int` | Token decimal places (typically `6`). |
| `expires_at` | `int` | Invoice expiration Unix timestamp. |
| `payment_method` | `str` | Payment method string. |
| `api_hash` | `str` | Fragment API hash for confirmation. |
| `page_url` | `str` | Full Fragment invoice page URL. |

#### `PreparedTransaction`

Unsigned transaction payload for external signing scenarios (used in EVM-only mode and No-KYC mode).

| Field | Type | Description |
|---|---|---|
| `req_id` | `str` | Fragment request ID. |
| `item_kind` | `str` | Purchase type. |
| `target` | `str` | Recipient. |
| `amount` | `int` | Amount. |
| `valid_until` | `int` | Expiration timestamp. |
| `messages` | `list[PreparedTransactionMessage]` | List of transaction messages. |
| `raw` | `dict` | Raw Fragment payload. |
| `sender_address` | `str \| None` | Sender wallet address. |
| `confirm_referer` | `str \| None` | Referer path for confirmation. |

#### `PreparedTransactionMessage`

| Field | Type | Description |
|---|---|---|
| `address` | `str` | Destination TON address. |
| `amount` | `str` | Amount in nanograms as string. |
| `payload` | `str \| None` | Base64-encoded BOC payload. |
| `state_init` | `str \| None` | Base64-encoded state init. |

---

### Marketplace Item Info

#### `UsernameInfo`

| Field | Type | Description |
|---|---|---|
| `username` | `str` | Username without `@`. |
| `status` | `str` | Item status: `"Available"`, `"On Auction"`, `"Sold"`, etc. |
| `item_type` | `int` | Always `1` for usernames. |
| `gram_rate` | `float` | Current GRAM/USD exchange rate. |
| `auction` | `AuctionInfo \| None` | Auction details if active. |
| `auction_end` | `str \| None` | ISO datetime string of auction end time. |
| `owner_wallet` | `str \| None` | Current owner's TON wallet address. |
| `purchased_date` | `str \| None` | ISO datetime of last purchase. |
| `bid_history` | `list[BidHistoryEntry]` | List of historical bids. |
| `owner_history` | `list[OwnerHistoryEntry]` | List of past owners. |
| `offer_history` | `list[OfferHistoryEntry]` | List of offers. |
| `bid_history_next_offset` | `str \| None` | Pagination cursor for more bid history. |
| `owner_history_next_offset` | `str \| None` | Pagination cursor for more owner history. |
| `offer_history_next_offset` | `str \| None` | Pagination cursor for more offer history. |

**Property:** `ton_rate` — Alias for `gram_rate`.

#### `NumberInfo`

| Field | Type | Description |
|---|---|---|
| `number` | `str` | Number without `+`. |
| `display_number` | `str` | Formatted display string (e.g., `"+888 1234 5678"`). |
| `status` | `str` | Item status. |
| `item_type` | `int` | Always `3` for numbers. |
| `gram_rate` | `float` | Current GRAM/USD rate. |
| `restricted` | `bool` | `True` if number has usage restrictions. |
| `auction` | `AuctionInfo \| None` | Auction details. |
| `auction_end` | `str \| None` | Auction end datetime. |
| `owner_wallet` | `str \| None` | Owner wallet address. |
| `purchased_date` | `str \| None` | Purchase datetime. |
| `bid_history` | `list[BidHistoryEntry]` | Bid history. |
| `owner_history` | `list[OwnerHistoryEntry]` | Owner history. |
| `offer_history` | `list[OfferHistoryEntry]` | Offer history. |
| `bid_history_next_offset` | `str \| None` | Pagination cursor. |
| `owner_history_next_offset` | `str \| None` | Pagination cursor. |
| `offer_history_next_offset` | `str \| None` | Pagination cursor. |

**Property:** `ton_rate` — Alias for `gram_rate`.

#### `GiftInfo`

| Field | Type | Description |
|---|---|---|
| `slug` | `str` | Gift identifier. |
| `name` | `str` | Display name of the gift. |
| `status` | `str` | Item status. |
| `item_type` | `int` | Always `5` for gifts. |
| `gram_rate` | `float` | Current GRAM/USD rate. |
| `image_url` | `str \| None` | URL of the gift preview image. |
| `sticker_url` | `str \| None` | URL of the `.tgs` sticker file. |
| `owner_wallet` | `str \| None` | Owner wallet address. |
| `purchased_date` | `str \| None` | Purchase datetime. |
| `auction` | `AuctionInfo \| None` | Auction details. |
| `auction_end` | `str \| None` | Auction end datetime. |
| `attributes` | `list[GiftAttribute]` | Gift traits/properties. |
| `issued` | `str \| None` | Issuance info string. |
| `bid_history` | `list[BidHistoryEntry]` | Bid history. |
| `owner_history` | `list[OwnerHistoryEntry]` | Owner history. |
| `offer_history` | `list[OfferHistoryEntry]` | Offer history. |
| `bid_history_next_offset` | `str \| None` | Pagination cursor. |
| `owner_history_next_offset` | `str \| None` | Pagination cursor. |
| `offer_history_next_offset` | `str \| None` | Pagination cursor. |

**Property:** `ton_rate` — Alias for `gram_rate`.

---

### Marketplace Search Results

#### `UsernamesResult`

| Field | Type | Description |
|---|---|---|
| `items` | `list[dict]` | List of item dicts with keys: `slug`, `name`, `status`, `price`, `date`. |
| `next_offset_id` | `str \| None` | Pagination cursor for next page. `None` if no more results. |

#### `NumbersResult`

Same structure as `UsernamesResult`.

#### `GiftsResult`

| Field | Type | Description |
|---|---|---|
| `items` | `list[dict]` | List of gift item dicts with keys: `slug`, `name`, `status`, `price`, `date`. |
| `next_offset` | `int \| None` | Numeric offset for next page. `None` if no more results. |

---

### Price Models

#### `StarsPrice`

| Field | Type | Description |
|---|---|---|
| `stars` | `int` | Number of Stars in this package. |
| `gram_price` | `str` | Price in GRAM as string (e.g., `"1.25"`). |
| `usd_price` | `str` | Price in USD as string (e.g., `"3.99"`). |

**Property:** `ton_price` — Alias for `gram_price`.

#### `StarsPrices`

| Field | Type | Description |
|---|---|---|
| `packages` | `list[StarsPrice]` | All available Stars packages. |
| `gram_rate` | `float` | Current GRAM/USD exchange rate. |

**Property:** `ton_rate` — Alias for `gram_rate`.

#### `PremiumPriceOption`

| Field | Type | Description |
|---|---|---|
| `months` | `int` | Duration in months. |
| `label` | `str` | Display label (e.g., `"3 months"`). |
| `gram_price` | `str` | Price in GRAM. |
| `usd_price` | `str` | Price in USD. |
| `discount` | `str \| None` | Discount badge text (e.g., `"-20%"`). |

**Property:** `ton_price` — Alias for `gram_price`.

#### `PremiumPrices`

| Field | Type | Description |
|---|---|---|
| `options` | `list[PremiumPriceOption]` | Available Premium plans. |
| `gram_rate` | `float` | Current GRAM/USD rate. |

**Property:** `ton_rate` — Alias for `gram_rate`.

---

### History Models

#### `StarsTransaction`

| Field | Type | Description |
|---|---|---|
| `recipient` | `str` | Recipient username. |
| `stars` | `int` | Stars amount. |
| `price_gram` | `str` | Price paid in GRAM. |
| `date` | `str` | ISO datetime string. |

**Property:** `price_ton` — Alias for `price_gram`.

#### `PremiumTransaction`

| Field | Type | Description |
|---|---|---|
| `recipient` | `str` | Recipient username. |
| `duration` | `str` | Duration label (e.g., `"3 months"`). |
| `price_gram` | `str` | Price paid in GRAM. |
| `date` | `str` | ISO datetime string. |

**Property:** `price_ton` — Alias for `price_gram`.

#### `TopupTransaction`

| Field | Type | Description |
|---|---|---|
| `recipient` | `str` | Ads account username. |
| `amount` | `int` | GRAM amount. |
| `date` | `str` | ISO datetime string. |

---

### Account & Profile Models

#### `WalletInfo`

| Field | Type | Description |
|---|---|---|
| `address` | `str` | TON wallet address (user-friendly, non-bounceable). |
| `state` | `str` | Wallet state: `"active"`, `"uninitialized"`, etc. |
| `gram_balance` | `float` | GRAM balance (e.g., `12.5432`). |
| `usdt_balance` | `float` | USDT balance (e.g., `100.0`). |

**Properties:**
- `balance_ton` — Alias for `gram_balance`.
- `balance_usdt` — Alias for `usdt_balance`.

#### `ProfileInfo`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Display name. |
| `username` | `str` | Telegram username without `@`. |
| `photo_url` | `str \| None` | Profile photo URL. |
| `identity_verified` | `bool` | `True` if KYC identity verification is complete. |
| `wallet_address` | `str \| None` | Linked TON wallet address. |
| `wallet_label` | `str \| None` | Shortened wallet label. |
| `wallet_verified` | `bool` | `True` if wallet is verified. |

#### `RecipientInfo`

| Field | Type | Description |
|---|---|---|
| `recipient` | `str` | Fragment-internal recipient identifier. |
| `name` | `str` | Display name. |
| `photo_url` | `str \| None` | Avatar URL. |
| `myself` | `bool` | `True` if the recipient is the authenticated user. |

#### `SessionInfo`

| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Session identifier for `terminate_session()`. |
| `device` | `str` | Device description. |
| `location` | `str` | Geographic location. |
| `date` | `str \| None` | Last activity datetime. |
| `is_current` | `bool` | `True` if this is the current active session. |

---

### Asset Management Models

#### `MyAsset`

| Field | Type | Description |
|---|---|---|
| `item_type` | `str` | `"usernames"`, `"numbers"`, or `"gifts"`. |
| `slug` | `str` | Item identifier (e.g., `"username/durov"`, `"gift/abc123"`). |
| `name` | `str` | Display name. |
| `description` | `str \| None` | Additional description text. |
| `image_url` | `str \| None` | Preview image URL (gifts only). |
| `assigned_to` | `str \| None` | Telegram account ID if assigned. |
| `assigned_name` | `str \| None` | Telegram account name if assigned. |

#### `MyAssetsResult`

| Field | Type | Description |
|---|---|---|
| `items` | `list[MyAsset]` | List of owned assets. |
| `gram_rate` | `float` | Current GRAM/USD rate. |
| `total_count` | `int` | Total number of assets of this type. |

**Property:** `ton_rate` — Alias for `gram_rate`.

#### `MyBid`

| Field | Type | Description |
|---|---|---|
| `item_type` | `str` | `"usernames"`, `"numbers"`, or `"gifts"`. |
| `slug` | `str` | Item identifier. |
| `name` | `str` | Display name. |
| `bid` | `float` | Bid amount in GRAM. |
| `status` | `str` | Bid status (e.g., `"Outbid"`, `"Winning"`, `"Won"`). |
| `date` | `str` | ISO datetime of the bid. |
| `image_url` | `str \| None` | Preview image (gifts only). |
| `description` | `str \| None` | Additional description. |

#### `MyBidsResult`

| Field | Type | Description |
|---|---|---|
| `items` | `list[MyBid]` | List of bids. |
| `gram_rate` | `float` | Current GRAM/USD rate. |
| `total_count` | `int` | Total number of bids for this item type. |

**Property:** `ton_rate` — Alias for `gram_rate`.

#### `TelegramAccount`

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Account ID used for assignment. |
| `name` | `str` | Account display name. |
| `type` | `str` | Account type description. |
| `photo_url` | `str \| None` | Account avatar URL. |

#### `AssignAccountsResult`

| Field | Type | Description |
|---|---|---|
| `accounts` | `list[TelegramAccount]` | Available accounts. |
| `can_disable` | `bool` | `True` if the "Don't display on Telegram" option is available. |

#### `AssignResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if assignment succeeded. |
| `message` | `str \| None` | Status message or error text. |
| `need_pay` | `bool` | `True` if a fee payment is required to assign. |
| `req_id` | `str \| None` | Payment request ID (if `need_pay` is `True`). |
| `amount` | `str \| None` | Fee amount (if `need_pay` is `True`). |
| `assign_name` | `str \| None` | Name of the account the asset was assigned to. |

#### `PurchaseItem`

Input model for batch purchases.

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | `str` | **(required)** | `"stars"`, `"premium"`, `"gram"`, or `"ton"`. |
| `username` | `str` | **(required)** | Recipient username. |
| `amount` | `int \| None` | `None` | Stars count or GRAM amount. |
| `months` | `int \| None` | `None` | Premium months. |
| `show_sender` | `bool` | `True` | Show sender name. |

---

### NFT & Withdrawal Models

#### `NftTransferRecipient`

| Field | Type | Description |
|---|---|---|
| `myself` | `bool` | `True` if the recipient is the authenticated user. |
| `recipient` | `str` | Fragment recipient identifier. |
| `name` | `str` | Display name. |
| `photo_url` | `str \| None` | Avatar URL. |

#### `NftTransferRequest`

| Field | Type | Description |
|---|---|---|
| `req_id` | `str` | Transfer request ID for `transfer_nft()`. |
| `myself` | `bool` | `True` if transferring to self. |
| `item_title` | `str` | Gift name. |
| `content` | `str` | Confirmation message HTML. |
| `button` | `str` | Confirmation button text. |

#### `NftWithdrawalInitResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if initialization succeeded. |
| `confirm_message` | `str \| None` | Human-readable confirmation message. |
| `confirm_button` | `str \| None` | Button label text. |
| `confirm_hash` | `str \| None` | Hash needed for `confirm_nft_withdrawal()`. |
| `error` | `str \| None` | Error message if `ok` is `False`. |

#### `NftWithdrawalConfirmResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if confirmation succeeded. |
| `need_update` | `bool` | `True` if the page needs to be refreshed. |
| `mode` | `str` | Result mode: `"done"`, `"error"`, etc. |
| `html` | `str \| None` | Updated page HTML. |
| `error` | `str \| None` | Error message if failed. |

#### `StarsWithdrawalState`

| Field | Type | Description |
|---|---|---|
| `transaction` | `str` | Transaction identifier. |
| `withdrawal_data` | `str` | Encoded withdrawal data for init/confirm. |

#### `StarsWithdrawalInitResult`

Same structure as `NftWithdrawalInitResult`.

#### `StarsWithdrawalConfirmResult`

Same structure as `NftWithdrawalConfirmResult`.

#### `StartAuctionResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if auction started successfully. |
| `req_id` | `str \| None` | Confirmation request ID. |

---

### Gateway & Ads Recharge Models

#### `GatewayPriceInfo`

| Field | Type | Description |
|---|---|---|
| `credits` | `int` | Number of credits. |
| `gram_price` | `str` | Price in GRAM. |
| `usd_price` | `str \| None` | Price in USD. |

#### `GatewayRechargeResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `account_id` | `str` | Gateway account identifier. |
| `credits` | `int` | Credits purchased. |
| `req_id` | `str \| None` | Request ID for confirmation. |

#### `AdsRechargeResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `account_id` | `str` | Ads account identifier. |
| `amount` | `int` | GRAM amount recharged. |
| `req_id` | `str \| None` | Request ID for confirmation. |

---

### Offer Models

#### `OfferResult`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | `str` | Transaction hash. |
| `item_type` | `int` | Item type: `1` (username), `3` (number), `5` (gift). |
| `slug` | `str` | Item identifier. |
| `amount` | `int` | Offer amount in GRAM. |
| `req_id` | `str \| None` | Request ID. |

---

### Subscription Models

#### `SubscriptionResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if operation succeeded. |
| `subscribed` | `bool` | `True` if subscribed after operation. |
| `item_type` | `int` | Item type. |
| `slug` | `str` | Item identifier. |

### Ads Withdrawal Models

#### `AdsWithdrawalInitResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if initialization succeeded. |
| `confirm_message` | `str \| None` | Confirmation message. |
| `confirm_button` | `str \| None` | Button label. |
| `confirm_hash` | `str \| None` | Hash for confirmation step. |
| `error` | `str \| None` | Error message if failed. |

#### `AdsWithdrawalConfirmResult`

| Field | Type | Description |
|---|---|---|
| `ok` | `bool` | `True` if confirmation succeeded. |
| `need_update` | `bool` | Page needs refresh. |
| `mode` | `str` | Result mode. |
| `html` | `str \| None` | Updated page HTML. |
| `error` | `str \| None` | Error message. |

---

### Anonymous Number Models

#### `LoginCodeResult`

| Field | Type | Description |
|---|---|---|
| `number` | `str` | The anonymous phone number queried. |
| `code` | `str \| None` | The pending login code, or `None` if no code is pending. |
| `active_sessions` | `int` | Number of active Telegram sessions on this number. |

#### `TerminateSessionsResult`

| Field | Type | Description |
|---|---|---|
| `number` | `str` | The anonymous phone number. |
| `message` | `str \| None` | Server response message. |

---

### Batch Models

#### `BatchResult`

| Field | Type | Description |
|---|---|---|
| `total` | `int` | Total number of items in the batch. |
| `succeeded` | `int` | Number of items that completed successfully. |
| `failed` | `int` | Number of items that failed. |
| `chunks_sent` | `int` | Number of on-chain transaction chunks successfully broadcast. |
| `items` | `list[BatchItemResult]` | Per-item results. |

#### `NoKycBatchResult`

| Field | Type | Description |
|---|---|---|
| `total` | `int` | Total number of items in the batch. |
| `succeeded` | `int` | Number of items that completed successfully. |
| `failed` | `int` | Number of items that failed. |
| `items` | `list[BatchItemResult]` | Per-item results. |
| `prepared_transactions` | `list[PreparedTransaction]` | Prepared transactions for external signing (if wallet not configured). |

#### `BatchItemResult`

| Field | Type | Description |
|---|---|---|
| `type` | `str` | Purchase type. |
| `username` | `str` | Recipient username. |
| `amount` | `int` | Stars, months, or GRAM amount. |
| `ok` | `bool` | `True` if this item succeeded. |
| `result` | `Any` | Result dict with `transaction_id` if successful. |
| `error` | `str \| None` | Error message if failed. |
| `chunk_index` | `int` | Index of the transaction chunk this item belongs to. |

---

### Auction Models

#### `AuctionInfo`

| Field | Type | Description |
|---|---|---|
| `highest_bid` | `str \| None` | Current highest bid in GRAM. |
| `bid_step` | `str \| None` | Minimum bid increment in GRAM. |
| `minimum_bid` | `str \| None` | Minimum allowed bid in GRAM. |
| `sell_price` | `str \| None` | Fixed sell price in GRAM (for sale items). |
| `buy_now_price` | `str \| None` | Buy-now price in GRAM (if available). |

#### `BidHistoryEntry`

| Field | Type | Description |
|---|---|---|
| `price` | `str \| None` | Bid amount in GRAM. |
| `date` | `str \| None` | ISO datetime of the bid. |
| `wallet` | `str \| None` | Bidder wallet address. |

#### `OwnerHistoryEntry`

| Field | Type | Description |
|---|---|---|
| `price` | `str \| None` | Purchase price or `"Transferred"`. |
| `date` | `str \| None` | ISO datetime. |
| `wallet` | `str \| None` | Owner wallet address. |

#### `OfferHistoryEntry`

| Field | Type | Description |
|---|---|---|
| `price` | `str \| None` | Offer amount in GRAM. |
| `date` | `str \| None` | ISO datetime of the offer. |
| `wallet` | `str \| None` | Offerer wallet address. |

---

### Helper Models

#### `GiftAttribute`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Trait name (e.g., `"Background"`). |
| `value` | `str` | Trait value (e.g., `"Red"`). |
| `rarity` | `str \| None` | Rarity percentage (e.g., `"2.5%"`). |

---

## Exceptions

All exceptions are importable from `FragmentAPI.exceptions` or `FragmentAPI.types`.

### Exception Hierarchy

```
FragmentError (base)
├── ClientError
│   ├── ConfigurationError (alias: ConfigError)
│   └── CookieError
├── FragmentAPIError
│   ├── FragmentPageError
│   ├── UserNotFoundError
│   ├── AlreadySubscribedError
│   ├── AnonymousNumberError
│   ├── TransactionError
│   │   ├── ConfirmationTimeout
│   │   └── SeqnoError
│   ├── ParseError
│   └── VerificationError
├── MarketAppAPIError (No-KYC mode API errors)
└── OperationError
    ├── WalletError
    ├── SessionStorageError
    ├── RetryExhaustedError
    └── UnexpectedError
```

### Base Exceptions

#### `FragmentError`

Base exception for all Fragment API library errors. Catch this to handle any library exception.

```python
try:
    result = await client.purchase_stars("durov", 100)
except FragmentError as e:
    print(f"Fragment operation failed: {e}")
```

---

### Client Exceptions

#### `ConfigurationError`

Raised when required client parameters are missing or invalid.

| Message Constant | Description |
|---|---|
| `MISSING_VARS` | Required parameter(s) not provided. |
| `UNSUPPORTED_VERSION` | Invalid `wallet_version` value. |
| `INVALID_MNEMONIC` | Seed phrase has wrong word count (not 12, 18, or 24). |
| `UNSUPPORTED_PROVIDER` | Invalid `api_provider` value. |
| `UNSUPPORTED_METHOD` | EVM payment not supported for this purchase type. |
| `INVALID_MONTHS` | Premium months not in {3, 6, 12}. |
| `INVALID_STARS_AMOUNT` | Stars amount outside 50–10,000,000 range. |
| `INVALID_GRAM_AMOUNT` | GRAM amount outside 1–1,000,000,000 range. |
| `INVALID_TON_AMOUNT` | Alias for `INVALID_GRAM_AMOUNT`. |
| `INVALID_WINNERS_STARS` | Stars giveaway winners outside valid range. |
| `INVALID_WINNERS_PREMIUM` | Premium giveaway winners outside 1–24,000 range. |
| `INVALID_STARS_PER_WINNER` | Stars per winner outside 500–1,000,000 range. |
| `INVALID_PAYMENT_METHOD` | Unrecognized payment method string. |
| `INVALID_GIVEAWAY_PACKAGE` | Stars giveaway amount not in allowed packages. |
| `INVALID_GIVEAWAY_WINNERS` | Winners count exceeds maximum for given amount. |
| `INVALID_ITEM_TYPE` | Item type not in {1, 3, 5}. |
| `INVALID_BID_AMOUNT` | Bid amount must be a positive integer. |
| `INVALID_OFFER_AMOUNT` | Offer amount must be a positive integer. |
| `INVALID_CREDITS_AMOUNT` | Credits amount must be a positive integer. |
| `SEED_REQUIRED` | Operation requires seed but none configured. |
| `TON_TOKEN_REQUIRED` | Operation requires `stel_ton_token` cookie. |
| `API_KEY_REQUIRED` | Operation requires API key but none configured. |
| `COOKIES_REQUIRED` | Operation requires Fragment cookies. |
| `NOKYC_UNSUPPORTED_METHOD` | No-KYC mode only supports GRAM/TON payment methods. |
| `NOKYC_UNSUPPORTED_OPERATION` | Operation not available in No-KYC mode. |
| `INVALID_PROXY` | Proxy URL format is invalid. |

---

#### `CookieError`

Raised when cookies are unreadable or missing required fields.

| Message Constant | Description |
|---|---|
| `READ_FAILED` | Cookie string could not be parsed. |
| `MISSING_KEYS` | One or more required cookie keys are empty or missing. |
| `UNSUPPORTED_BROWSER` | Browser cookie extraction not supported. |
| `BROWSER_READ_FAILED` | Failed to read cookies from browser. |
| `MISSING_BROWSER_KEYS` | Required cookies not found in browser. |
| `EXPIRED` | Session cookie has expired. |
| `REFRESH_FAILED` | Failed to refresh session cookies. |

---

### API Exceptions

#### `FragmentAPIError`

General error from Fragment API responses.

| Message Constant | Description |
|---|---|
| `NO_REQUEST_ID` | Fragment did not return a request ID. Session may have expired. |

---

#### `FragmentPageError`

Raised when Fragment pages cannot be fetched or API hash not found.

| Message Constant | Description |
|---|---|
| `BAD_STATUS` | Fragment returned non-200 HTTP status. |
| `HASH_NOT_FOUND` | Could not extract API hash from page HTML. |
| `ITEM_NOT_FOUND` | Fragment returned HTTP 302 redirect (item not found). |

---

#### `UserNotFoundError`

Raised when target Telegram user is not found on Fragment.

| Message Constant | Description |
|---|---|
| `NOT_FOUND` | Username not found on Fragment. |
| `NOT_A_USER` | Username belongs to a channel or bot, not a user account. |

---

#### `AlreadySubscribedError`

Raised when trying to gift Premium to a user who already has it.

| Message Constant | Description |
|---|---|
| `PREMIUM_ACTIVE` | Account already has active Telegram Premium. |

---

#### `AnonymousNumberError`

Raised for anonymous number operation failures.

| Message Constant | Description |
|---|---|
| `NOT_OWNED` | Number not associated with your Fragment account. |
| `TERMINATE_FAILED` | Session termination failed with server error. |

---

#### `TransactionError`

Raised when TON transaction fails to build or broadcast.

| Message Constant | Description |
|---|---|
| `INVALID_PAYLOAD` | Fragment returned empty or malformed transaction messages. |
| `BROADCAST_FAILED` | Transaction broadcast to TON network failed. |
| `BROADCAST_SSL_ERROR` | SSL certificate error during broadcast. Usually fixable with `pip install --upgrade certifi`. |
| `DUPLICATE_SEQNO` | Previous transaction with same seqno still pending. Wait and retry. |

---

#### `ConfirmationTimeout` (extends `TransactionError`)

Transaction was sent but confirmation was not received within the timeout window. The transaction may have succeeded — check the blockchain manually.

| Message Constant | Description |
|---|---|
| `TIMEOUT` | Seqno/balance did not change within timeout period. |

---

#### `SeqnoError` (extends `TransactionError`)

| Message Constant | Description |
|---|---|
| `FETCH_FAILED` | Could not retrieve wallet seqno from network. |
| `STALE` | Seqno did not increment after broadcast. |

---

#### `ParseError`

| Message Constant | Description |
|---|---|
| `UNPARSEABLE` | Fragment response could not be parsed (invalid JSON/HTML). |

---

#### `VerificationError`

| Message Constant | Description |
|---|---|
| `KYC_REQUIRED` | Fragment requires KYC identity verification. Complete at https://fragment.com/my/profile. |

---

#### `MarketAppAPIError`

Raised for errors returned by MarketApp API in No-KYC mode.

| Message Constant | Description |
|---|---|
| `API_CALL_FAILED` | MarketApp API call failed. |
| `RECIPIENT_NOT_FOUND` | Recipient not found via MarketApp API. |
| `TRANSACTION_BUILD_FAILED` | Failed to build transaction via MarketApp API. |

---

### Operation Exceptions

#### `WalletError`

Raised for TON wallet issues.

| Message Constant | Description |
|---|---|
| `LOW_GRAM_BALANCE` | Insufficient GRAM balance for transaction + gas. |
| `LOW_TON_BALANCE` | Alias for `LOW_GRAM_BALANCE`. |
| `LOW_USDT_BALANCE` | Insufficient USDT balance. |
| `GRAM_BALANCE_CHECK_FAILED` | Failed to fetch GRAM balance from network. |
| `TON_BALANCE_CHECK_FAILED` | Alias for `GRAM_BALANCE_CHECK_FAILED`. |
| `USDT_BALANCE_CHECK_FAILED` | Failed to fetch USDT balance from network. |
| `ACCOUNT_INFO_FAILED` | Failed to build wallet account info. |
| `WALLET_INFO_FAILED` | Failed to retrieve wallet info. |

---

#### `SessionStorageError`

Raised for session storage read/write errors.

| Message Constant | Description |
|---|---|
| `SAVE_FAILED` | Failed to save session to storage. |
| `LOAD_FAILED` | Failed to load session from storage. |

---

#### `RetryExhaustedError`

Raised when all retry attempts have been exhausted.

| Message Constant | Description |
|---|---|
| `EXHAUSTED` | All retry attempts exhausted for the operation. |

---

#### `UnexpectedError`

Wraps any unexpected internal exception.

| Message Constant | Description |
|---|---|
| `UNEXPECTED` | Generic wrapper for unhandled exceptions. |

---

## Constants & Limits

| Constant | Value | Description |
|---|---|---|
| `STARS_PURCHASE_MIN` | `50` | Minimum Stars per purchase. |
| `STARS_PURCHASE_MAX` | `10,000,000` | Maximum Stars per purchase. |
| `GRAM_TOPUP_MIN` | `1` | Minimum GRAM for Ads top-up. |
| `GRAM_TOPUP_MAX` | `1,000,000,000` | Maximum GRAM for Ads top-up. |
| `PREMIUM_MONTHS_VALID` | `{3, 6, 12}` | Allowed Premium durations. |
| `STARS_GIVEAWAY_MIN` | `500` | Minimum Stars per giveaway winner. |
| `STARS_GIVEAWAY_MAX` | `1,000,000` | Maximum Stars per giveaway winner. |
| `STARS_WINNERS_MIN` | `1` | Minimum giveaway winners (Stars). |
| `STARS_WINNERS_MAX` | `5` | Maximum giveaway winners (Stars, depends on amount). |
| `PREMIUM_WINNERS_MIN` | `1` | Minimum giveaway winners (Premium). |
| `PREMIUM_WINNERS_MAX` | `24,000` | Maximum giveaway winners (Premium). |
| `MIN_GRAM_BALANCE` | `0.01` | Minimum GRAM reserved for gas fees. |
| `DEFAULT_TIMEOUT` | `30.0` | Default HTTP timeout in seconds. |
| `CONFIRMATION_INTERVAL` | `3.0` | Seconds between confirmation polls. |
| `CONFIRMATION_MAX_ATTEMPTS` | `40` | Maximum confirmation poll attempts (total ~120s). |
| `WALLET_MAX_MESSAGES["V4R2"]` | `4` | Max messages per transaction for V4R2 wallets. |
| `WALLET_MAX_MESSAGES["V5R1"]` | `255` | Max messages per transaction for V5R1 wallets. |

**Stars giveaway allowed packages:** 500, 1000, 1500, 2500, 5000, 10000, 25000, 35000, 50000, 100000, 150000, 500000, 1000000.

---

## Examples

### No-KYC Mode — Purchase Stars

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # No cookies required! Just seed + API key for auto-execution
    async with FragmentClient(
        marketapp_token="your_marketapp_token",  # optional, uses default if not provided
        seed="word1 word2 word3 ... word24",
        api_key="AF...",
        wallet_version="V5R1",
    ) as client:
        result = await client.purchase_stars("durov", 500)
        print(f"Sent 500 Stars! TX: {result.transaction_id}")

asyncio.run(main())
```

### No-KYC Mode — Prepared Transaction

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # No seed + api_key -> returns PreparedTransaction for external signing
    async with FragmentClient(
        marketapp_token="your_marketapp_token",
        # no seed, no api_key
    ) as client:
        result = await client.purchase_stars("durov", 500)
        
        if isinstance(result, PreparedTransaction):
            print(f"Prepared transaction for {result.target}:")
            for msg in result.messages:
                print(f"  Send {msg.amount} GRAM to {msg.address}")

asyncio.run(main())
```

### Full Mode — Purchase Stars

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    async with FragmentClient(
        cookies={
            "stel_ssid": "...",
            "stel_dt": "-180",
            "stel_token": "...",
            "stel_ton_token": "..."
        },
        seed="word1 word2 word3 ... word24",
        api_key="AF...",
        wallet_version="V5R1",
    ) as client:
        result = await client.purchase_stars("durov", 500)
        print(f"Sent 500 Stars! TX: {result.transaction_id}")

asyncio.run(main())
```

### Batch Purchase Example

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    async with FragmentClient(
        cookies="stel_ssid=...; stel_dt=-180; stel_token=...; stel_ton_token=...",
        seed="word1 word2 ... word24",
        api_key="AF...",
    ) as client:
        batch = await client.batch_purchase([
            {"type": "stars", "username": "user1", "amount": 100},
            {"type": "stars", "username": "user2", "amount": 200},
            {"type": "premium", "username": "user3", "months": 3},
        ])
        
        print(f"Results: {batch.succeeded}/{batch.total} succeeded")
        for item in batch.items:
            status = "✓" if item.ok else f"✗ {item.error}"
            print(f"  {item.username}: {status}")

asyncio.run(main())
```

### EVM Payment Flow

```python
import asyncio
from FragmentAPI import FragmentClient
from FragmentAPI.types.results import EvmPaymentResult

async def main():
    async with FragmentClient(
        cookies={"stel_ssid": "...", "stel_dt": "-180", "stel_token": "..."},
    ) as client:
        result = await client.purchase_stars("durov", 100, payment_method="usdc_base")
        
        if isinstance(result, EvmPaymentResult):
            inv = result.invoice
            print(f"Chain: {inv.invoice_chain_name} (ID: {inv.invoice_chain_id})")
            print(f"Token: {inv.token_symbol} at {inv.invoice_token}")
            print(f"Send: {inv.invoice_amount} {inv.token_symbol}")
            print(f"To: {inv.invoice_address}")
            print(f"Expires: {inv.expires_at}")

asyncio.run(main())
```

### Search Marketplace

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    async with FragmentClient(
        cookies={"stel_ssid": "...", "stel_dt": "-180", "stel_token": "..."},
    ) as client:
        # Search usernames
        usernames = await client.search_usernames("crypto", sort="price_asc")
        for item in usernames.items:
            print(f"@{item['name']} — {item['price']} GRAM — {item['status']}")
        
        # Search gifts with attributes
        gifts = await client.search_gifts(
            collection="plush-octopus",
            attr={"Background": ["Red", "Blue"]},
            sort="price_asc",
        )
        for gift in gifts.items:
            print(f"{gift['name']} — {gift['price']} GRAM")
        
        # Get detailed info
        info = await client.get_username_info("durov")
        print(f"Status: {info.status}")
        if info.auction:
            print(f"Highest bid: {info.auction.highest_bid} GRAM")

asyncio.run(main())
```

### Anonymous Number Management

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    async with FragmentClient(
        cookies={"stel_ssid": "...", "stel_dt": "-180", "stel_token": "...", "stel_ton_token": "..."},
    ) as client:
        # Check login code
        code_result = await client.get_login_code("+88812345678")
        if code_result.code:
            print(f"Login code: {code_result.code}")
        print(f"Active sessions: {code_result.active_sessions}")
        
        # Enable code delivery
        await client.toggle_login_codes("+88812345678", can_receive=True)
        
        # Terminate all sessions
        term = await client.terminate_sessions("+88812345678")
        print(f"Result: {term.message}")

asyncio.run(main())
```

### NFT Transfer Example

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    async with FragmentClient(
        cookies={...},
        seed="word1 word2 ... word24",
        api_key="AF...",
    ) as client:
        # Find recipient
        recipient = await client.search_nft_transfer_recipient("durov")
        if not recipient:
            print("Recipient not found")
            return
        
        # Initialize transfer
        request = await client.init_nft_transfer("gift-slug-123", recipient.recipient)
        print(f"Transferring: {request.item_title}")
        
        # Execute transfer
        tx = await client.transfer_nft(request.req_id)
        print(f"Transfer complete! TX: {tx.tx_hash}")

asyncio.run(main())
```

### Auto Authentication Example

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # QR code flow (default)
    cookies = await FragmentClient.authenticate(
        seed="word1 word2 ... word24",
        wallet_version="V5R1",
        print_qr=True,
    )
    print(f"Cookies obtained: {list(cookies.keys())}")
    
    # Phone flow
    cookies = await FragmentClient.authenticate(
        seed="word1 word2 ... word24",
        phone="+71234567890",
    )
    
    # Use cookies
    async with FragmentClient(
        cookies=cookies,
        seed="word1 word2 ... word24",
        api_key="AF...",
    ) as client:
        wallet = await client.get_wallet()
        print(f"Balance: {wallet.gram_balance} GRAM")

asyncio.run(main())
```

---

## Support & License

**Reporting Issues**
Create an [Issue](https://github.com/s1qwy/fragment-api-py/issues) or message in the [Telegram chat](https://t.me/fragment_api_lib).

**Support the Project**

TON Wallet: `UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj`

**License:** MIT — free for commercial and personal use.

---

[GitHub](https://github.com/s1qwy/fragment-api-py) • [Telegram](https://t.me/fragment_api_lib)