<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python SDK</h1>

<p align="center">
  <strong>Async Python library for Fragment.com automation</strong><br>
  <strong>v11.0.0 — Pydantic V2 | Selectolax Parser | Session Storage | Full Marketplace</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py.svg?style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square" alt="Python Versions"></a>
  <a href="https://pepy.tech/projects/fragment-api-py/"><img src="https://static.pepy.tech/personalized-badge/fragment-api-py?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads" alt="Downloads"></a>
  <a href="https://t.me/fragment_api_lib"><img src="https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=flat-square&logo=telegram" alt="Telegram"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
</p>

---

## What's New in v11.0.0

| Feature | Description |
|---------|-------------|
| **Pydantic V2** | Complete migration from dataclasses to Pydantic V2 models with full type validation. |
| **Selectolax Parser** | Replaced fragile regex parsing with fast CSS-selector based Selectolax (Lexbor backend). |
| **Session Storage** | Built-in cookie persistence with `FileSessionStorage` and `RedisSessionStorage` backends. |
| **Gateway API** | Full support for Telegram Gateway credit purchases and price queries. |
| **Offers** | Make offers on unlisted usernames, numbers, and gifts. |
| **Cancel Auction** | Cancel active auctions with no bids. |
| **Subscribe/Unsubscribe** | Get Telegram notifications for auction updates. |
| **Ads Withdrawal** | Withdraw Ads revenue to your wallet. |
| **Batch Operations** | Improved chunking (V4R2: 4, V5R1: 255 messages per transaction). |
| **EVM Payments** | USDT/USDC on Ethereum, Polygon, and BASE chains. |

---

## Features

- **Async-first** — Full async/await support with `FragmentClient`.
- **Pydantic Models** — All API responses return strongly-typed Pydantic models.
- **Selectolax Parsing** — Robust CSS-selector based HTML parsing.
- **Session Storage** — Persist cookies in files or Redis.
- **Purchases** — Stars (50–10M), Premium (3/6/12 months), GRAM Ads top-up.
- **Batch Operations** — Multiple purchases in grouped on-chain transactions.
- **EVM Payments** — USDT/USDC on Ethereum, Polygon, and BASE chains.
- **Giveaways** — Stars and Premium giveaways for channels (up to 24K winners).
- **Marketplace** — Search/bid on usernames, numbers, and gifts.
- **Auctions** — Start auctions, set fixed prices, place bids, buy-now.
- **Offers** — Make offers on unlisted items.
- **Gateway** — Recharge Telegram Gateway credits.
- **NFTs** — Transfer gifts, withdraw to wallet.
- **Wallet** — V4R2 and V5R1 support via `tonutils`.
- **Authentication** — Auto-authenticate via TON wallet proof + Telegram OAuth.
- **Anonymous Numbers** — Login codes, toggle delivery, terminate sessions.

---

## Installation

```bash
pip install fragment-api-py
```

**Requirements:**
- Python 3.10+
- Fragment cookies (`stel_ssid`, `stel_dt`, `stel_token`; `stel_ton_token` for wallet ops)
- TON wallet seed phrase (12/18/24 words)
- Tonconsole or Toncenter API key

Get a free API key at [tonconsole.com](https://tonconsole.com/).

---

## Quick Start

```python
import asyncio
from FragmentAPI import FragmentClient
from FragmentAPI.types.results import EvmPaymentResult

async def main():
    async with FragmentClient(
        cookies={
            "stel_ssid": "...",
            "stel_token": "...",
            "stel_dt": "...",
            "stel_ton_token": "..."
        },
        seed="word1 word2 ... word24",
        api_key="AF...",
        wallet_version="V5R1",
    ) as client:
        
        # Wallet info
        wallet = await client.get_wallet()
        print(f"Balance: {wallet.gram_balance} GRAM, {wallet.usdt_balance} USDT")
        
        # Purchase Stars
        result = await client.purchase_stars("durov", 100)
        print(f"TX: {result.transaction_id}")
        
        # Batch operations
        batch = await client.batch_purchase([
            {"type": "premium", "username": "durov", "months": 3},
            {"type": "stars", "username": "telegram", "amount": 250},
        ])
        print(f"Batch: {batch.succeeded}/{batch.total} succeeded")

        # EVM payment
        evm = await client.purchase_stars("durov", 50, payment_method="usdc_base")
        if isinstance(evm, EvmPaymentResult):
            inv = evm.invoice
            print(f"Send {inv.invoice_amount} {inv.token_symbol} to {inv.invoice_address}")

asyncio.run(main())
```

---

## Session Storage

Persist cookies across restarts:

```python
from FragmentAPI import FragmentClient, FileSessionStorage, RedisSessionStorage

# File-based storage
storage = FileSessionStorage(directory=".fragment_sessions")
client = await FragmentClient.from_storage(
    session_storage=storage,
    session_id="my_session",
    seed="word1 word2 ... word24",
    api_key="AF...",
)

# Redis storage
storage = RedisSessionStorage(redis_url="redis://localhost:6379/0", ttl=3600)
client = await FragmentClient.from_storage(
    session_storage=storage,
    session_id="my_session",
    seed="word1 word2 ... word24",
    api_key="AF...",
)
```

---

## Authentication

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # Auto-authenticate via TON wallet + Telegram
    cookies = await FragmentClient.authenticate(
        seed="word1 word2 ... word24",
        wallet_version="V5R1",
        phone="+71234567890",  # Omit for QR code flow
    )
    
    async with FragmentClient(
        cookies=cookies,
        seed="word1 word2 ... word24",
        api_key="AF...",
    ) as client:
        profile = await client.get_profile()
        print(f"Logged in as: {profile.name}")

asyncio.run(main())
```

---

## Payment Methods

| Method | Chain | Token | Behavior |
|--------|-------|-------|----------|
| `gram` / `ton` | TON (Gram) | GRAM | Automatic on-chain TX |
| `usdt_gram` / `usdt_ton` | TON (Gram) | USDT | Automatic on-chain TX |
| `usdt_eth` | Ethereum | USDT | Returns invoice |
| `usdt_pol` | Polygon | USDT | Returns invoice |
| `usdc_eth` | Ethereum | USDC | Returns invoice |
| `usdc_base` | BASE | USDC | Returns invoice |
| `usdc_pol` | Polygon | USDC | Returns invoice |

---

## API Overview

### Purchases & Giveaways
| Method | Description |
|--------|-------------|
| `purchase()` | Unified single/batch purchase |
| `purchase_stars()` | Send Stars to a user |
| `purchase_premium()` | Gift Premium to a user |
| `topup_gram()` | Top up GRAM to Ads balance |
| `topup_ton()` | Alias for `topup_gram()` |
| `batch_purchase()` | Batched multi-item purchases |
| `giveaway_stars()` | Stars giveaway for a channel |
| `giveaway_premium()` | Premium giveaway for a channel |

### Marketplace
| Method | Description |
|--------|-------------|
| `search_usernames()` | Search username listings |
| `search_numbers()` | Search anonymous numbers |
| `search_gifts()` | Search gift marketplace |
| `place_bid()` | Bid or buy-now on an item |
| `start_auction()` | Start an auction |
| `sell_asset()` | Sell at a fixed price |
| `make_offer()` | Make offer on unlisted item |
| `cancel_auction()` | Cancel active auction |
| `subscribe_to_item()` | Get auction notifications |
| `unsubscribe_from_item()` | Stop auction notifications |

### Asset Info & History
| Method | Description |
|--------|-------------|
| `get_username_info()` | Detailed username info |
| `get_number_info()` | Detailed number info |
| `get_gift_info()` | Detailed gift info |
| `get_stars_prices()` | Stars package prices |
| `get_stars_price()` | Price for specific Stars quantity |
| `get_premium_prices()` | Premium prices |
| `get_stars_history()` | Stars transaction history |
| `get_premium_history()` | Premium transaction history |
| `get_topup_history()` | Ads topup history |

### Account & Assets
| Method | Description |
|--------|-------------|
| `get_wallet()` | Wallet address & balances |
| `get_profile()` | Account profile info |
| `get_sessions()` | Active sessions |
| `terminate_session()` | Terminate a session |
| `get_my_assets()` | Owned assets |
| `get_my_bids()` | Bid history |
| `assign_to_telegram()` | Assign asset to account |
| `get_assign_accounts()` | Get available accounts |

### NFTs & Withdrawals
| Method | Description |
|--------|-------------|
| `search_nft_transfer_recipient()` | Find transfer recipient |
| `init_nft_transfer()` | Initialize NFT transfer |
| `transfer_nft()` | Execute NFT transfer |
| `init_nft_withdrawal()` | Withdraw NFT to wallet |
| `confirm_nft_withdrawal()` | Confirm NFT withdrawal |
| `init_stars_withdrawal()` | Withdraw Stars revenue |
| `confirm_stars_withdrawal()` | Confirm Stars withdrawal |
| `init_ads_withdrawal()` | Withdraw Ads revenue |
| `confirm_ads_withdrawal()` | Confirm Ads withdrawal |

### Gateway
| Method | Description |
|--------|-------------|
| `get_gateway_price()` | Get Gateway credits price |
| `recharge_gateway()` | Recharge Gateway credits |

### Anonymous Numbers
| Method | Description |
|--------|-------------|
| `get_login_code()` | Fetch pending login code |
| `toggle_login_codes()` | Enable/disable code delivery |
| `terminate_sessions()` | Terminate all sessions |

### Low-Level
| Method | Description |
|--------|-------------|
| `call()` | Send raw Fragment API request |
| `confirm_request()` | Confirm transaction after broadcast |

---

## Exceptions

All exceptions inherit from `FragmentError`:

| Exception | Description |
|-----------|-------------|
| `ConfigurationError` | Invalid client configuration |
| `CookieError` | Missing or invalid cookies |
| `FragmentPageError` | Page loading or hash extraction failed |
| `UserNotFoundError` | Target user not found |
| `AlreadySubscribedError` | User already has Premium |
| `AnonymousNumberError` | Anonymous number operation failed |
| `TransactionError` | TON transaction failed |
| `ConfirmationTimeout` | Transaction not confirmed in time |
| `WalletError` | Balance insufficient or wallet issues |
| `VerificationError` | KYC verification required |
| `ParseError` | Failed to parse API response |
| `SessionStorageError` | Storage read/write failed |
| `UnexpectedError` | Unexpected internal error |

---

## Support & License

**Issues:** [GitHub Issues](https://github.com/s1qwy/fragment-api-py/issues)

**Support the Project:**

<p align="center">
  <a href="https://app.tonkeeper.com/transfer/UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj">
    <img src="https://img.shields.io/badge/Donate-GRAM-0098ea?style=for-the-badge&logo=ton&logoColor=white" alt="Donate GRAM">
  </a>
</p>

<p align="center">
  <code>UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj</code>
</p>

**License:** MIT — free for commercial and personal use.

---

<p align="center">
  <a href="https://github.com/s1qwy/fragment-api-py">GitHub</a> •
  <a href="https://github.com/s1qwy/fragment-api-py/DOC.md">Documentation</a> •
  <a href="https://t.me/fragment_api_lib">Telegram</a>
</p>