<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python SDK</h1>

<p align="center">
  <strong>Async Python library for Fragment.com automation</strong><br>
  <strong>v10.0.0 — GRAM Rebrand | Batch Operations | EVM Payments | Full Marketplace</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py.svg?style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/pyversions/fragment-api-py.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://pepy.tech/projects/fragment-api-py/"><img src="https://static.pepy.tech/personalized-badge/fragment-api-py?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads" alt="Downloads"></a>
  <a href="https://t.me/fragment_api_lib"><img src="https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=flat-square&logo=telegram" alt="Telegram"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/s1qwy/fragment-api-py"><img src="https://img.shields.io/badge/GitHub-s1qwy/fragment--api--py-181717?style=flat-square&logo=github" alt="GitHub"></a>
  <a href="DOC.md"><img src="https://img.shields.io/badge/Documentation-DOC.md-6366f1?style=flat-square" alt="Docs"></a>
</p>

---

## What's New in v10.0.0

| Feature | Description |
|---------|-------------|
| **GRAM Rebrand** | All TON references updated to GRAM following the Telegram Open Network rebrand. `ton` payment method and `balance_ton` properties remain as backward-compatible aliases. |
| **Three Operating Modes** | Full mode (cookies + seed + api_key), EVM-only mode (cookies without `stel_ton_token`), Read-only mode (cookies only). |
| **NFT Management** | Transfer gifts between users, withdraw NFTs to wallet, manage Stars revenue withdrawals. |
| **Auction & Selling** | Start auctions, sell assets at fixed prices, place bids on usernames, numbers, and gifts. |
| **Asset Assignment** | Assign owned usernames and gifts to specific Telegram accounts. |

---

## Features

- **Async-first** — Full async/await support with `FragmentClient`.
- **Purchases** — Stars (50–10M), Premium (3/6/12 months), GRAM Ads top-up.
- **Batch Operations** — Multiple purchases in grouped on-chain transactions.
- **EVM Payments** — USDT/USDC on Ethereum, Polygon, and BASE chains.
- **Giveaways** — Stars and Premium giveaways for channels (up to 24K winners).
- **Marketplace** — Search/bid on usernames, numbers, and gifts with full pagination.
- **Auctions** — Start auctions, set fixed prices, place bids, buy-now.
- **NFTs** — Transfer, withdraw to wallet, manage Stars revenue.
- **Wallet** — V4R2 and V5R1 support via `tonutils`. GRAM and USDT balances.
- **Authentication** — Auto-authenticate via TON wallet proof + Telegram OAuth (QR/phone).
- **Anonymous Numbers** — Login codes, toggle delivery, terminate sessions (+888).
- **Asset Management** — List owned assets, bid history, assign to Telegram accounts.

---

## Installation

```bash
pip install fragment-api-py
```

**Requirements:**
- Python 3.10+
- Fragment cookies (`stel_ssid`, `stel_dt`, `stel_token`; `stel_ton_token` for wallet operations)
- TON wallet seed phrase (12/18/24 words) — for on-chain transactions
- Tonconsole or Toncenter API key — for blockchain interactions

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

For complete method signatures, parameters, return types, and models, see the **[Full Documentation (DOC.md)](DOC.md)**.

### Purchases & Giveaways
| Method | Description |
|--------|-------------|
| `purchase()` | Unified single/batch purchase |
| `purchase_stars()` | Send Stars to a user |
| `purchase_premium()` | Gift Premium to a user |
| `topup_gram()` | Top up GRAM to Ads balance |
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

### Asset Info & History
| Method | Description |
|--------|-------------|
| `get_username_info()` | Detailed username info |
| `get_number_info()` | Detailed number info |
| `get_gift_info()` | Detailed gift info |
| `get_stars_prices()` | Stars package prices |
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
| `get_my_assets()` | Owned assets |
| `get_my_bids()` | Bid history |
| `assign_to_telegram()` | Assign asset to account |

### NFTs & Withdrawals
| Method | Description |
|--------|-------------|
| `transfer_nft()` | Transfer gift to user |
| `init_nft_withdrawal()` | Withdraw NFT to wallet |
| `init_stars_withdrawal()` | Withdraw Stars revenue |

### Anonymous Numbers
| Method | Description |
|--------|-------------|
| `get_login_code()` | Fetch pending login code |
| `toggle_login_codes()` | Enable/disable code delivery |
| `terminate_sessions()` | Terminate all sessions |

---

## Support & License

**Issues:** [GitHub Issues](https://github.com/s1qwy/fragment-api-py/issues) or [Telegram Chat](https://t.me/fragment_api_lib)

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
  <a href="DOC.md">Documentation</a> •
  <a href="https://t.me/fragment_api_lib">Telegram</a>
</p>