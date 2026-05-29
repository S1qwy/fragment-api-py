<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python SDK</h1>

<p align="center">
  <strong>Professional Python library for Fragment.com automation</strong><br>
  <strong>v7.0.0 — EVM Payments | Anonymous Telemetry | Live Stats Dashboard</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py.svg?style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/pyversions/fragment-api-py.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://pepy.tech/projects/fragment-api-py/"><img src="https://static.pepy.tech/personalized-badge/fragment-api-py?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads" alt="Downloads"></a>
  <a href="https://t.me/fragment_api_py"><img src="https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=flat-square&logo=telegram" alt="Telegram"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/s1qwy/fragment-api-py"><img src="https://img.shields.io/badge/GitHub-s1qwy/fragment--api--py-181717?style=flat-square&logo=github" alt="GitHub"></a>
  <a href="https://fragment.s1qwy.ru"><img src="https://img.shields.io/badge/Documentation-Live-6366f1?style=flat-square" alt="Docs"></a>
  <a href="https://fragment.s1qwy.ru/statistic"><img src="https://img.shields.io/badge/Stats-Dashboard-ec4899?style=flat-square" alt="Dashboard"></a>
</p>

---

## ✨ What's New in v7.0.0

| Feature | Description |
|---------|-------------|
| 💳 **EVM Payments** | 5 new methods: `usdt_eth`, `usdt_pol`, `usdc_eth`, `usdc_base`, `usdc_pol` |
| 📦 **EvmInvoice** | Full invoice details: address, token, chain_id, amount, expiration |
| 📊 **Anonymous Telemetry** | Helps improve the library — no sensitive data ever sent |
| 📈 **Live Dashboard** | [fragment.s1qwy.ru/statistic](https://fragment.s1qwy.ru/statistic) — real-time usage stats |

---

## 🚀 Features

- **Async-only** — `FragmentClient` with full async/await support
- **EVM Payments** — USDT/USDC on Ethereum, BASE, Polygon
- **Purchases** — Stars (50–10M), Premium (3/6/12 months), TON Ads
- **Giveaways** — Stars and Premium for channels (up to 24k winners)
- **Bids** — `place_bid(item_type=1|3|5, slug, bid)` — instant buy if bid = buy-now price
- **Marketplace** — search usernames, numbers, gifts with filters and pagination
- **Wallet** — V4R2 and V5R1 (W5) support
- **Auto-authentication** — obtain cookies via TON wallet and Telegram
- **Anonymous numbers** — manage login codes, terminate sessions (+888)
- **NFT Management** — withdraw gifts to wallet, transfer to users
- **Stars Revenue** — withdraw earned Stars to wallet
- **Error hierarchy** — complete exception handling

---

## 📦 Installation

```bash
pip install fragment-api-py
```

## 🧪 Requirements

- Python 3.10+
- Fragment cookies: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`
- TON wallet seed phrase (12/18/24 words)

---

## 🎯 Quick Start

```python
import asyncio
from FragmentAPI import FragmentClient
from FragmentAPI.types.results import EvmPaymentResult, StarsResult

async def main():
    async with FragmentClient(
        seed="24 words...",
        cookies={"stel_ssid": "...", "stel_token": "...", "stel_dt": "...", "stel_ton_token": "..."},
        wallet_version="V5R1",
    ) as client:
        
        # Wallet info
        wallet = await client.get_wallet()
        print(f"{wallet.balance_ton} TON, {wallet.balance_usdt} USDT")
        
        # TON payment (automatic)
        result = await client.purchase_stars("@durov", 100)
        print(f"TX: {result.transaction_id}")
        
        # EVM payment (returns invoice)
        result = await client.purchase_stars("@durov", 50, payment_method="usdc_base")
        if isinstance(result, EvmPaymentResult):
            inv = result.invoice
            print(f"Send {inv.invoice_amount} {inv.token_symbol}")
            print(f"To: {inv.invoice_address}")
            print(f"Chain: {inv.invoice_chain_name}")
        
        # Purchase Premium
        await client.purchase_premium("@durov", 6, show_sender=True)
        
        # Place bid (type 1=username, 3=number, 5=gift)
        await client.place_bid(1, "username", bid=150)
        
        # Stars giveaway
        await client.giveaway_stars("@channel", winners=5, amount=1000)
        
        # Search marketplace
        items = await client.search_usernames("gold", filter="sale")

asyncio.run(main())
```

---

## 🔐 Auto-cookie Authentication

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # Automatic authentication via TON wallet and Telegram
    cookies = await FragmentClient.authenticate(
        seed="24 words...",
        wallet_version="V5R1",
        telegram_phone="+71234567890"  # or telegram_auth_data
    )
    
    async with FragmentClient(seed="24 words...", cookies=cookies) as client:
        profile = await client.get_profile()
        print(f"Logged in as: {profile.name}")

asyncio.run(main())
```

---

## 📊 Anonymous Telemetry

The library sends anonymous usage statistics to help understand which features are used and what errors users encounter.

**✅ Collected:**
- Library version, wallet version (V4R2/V5R1)
- Method name, status (ok/error), duration
- Error class name, scrubbed error message (first 200 chars)

**❌ NEVER Collected:**
- Seed phrases, cookies, API keys
- Usernames (replaced with `<username>`)
- Wallet addresses (replaced with `<ton_addr>` or `<eth_addr>`)
- Transaction hashes, amounts
- IP addresses

**Disable telemetry:**
```python
FragmentClient(seed="...", cookies=..., stats_enabled=False)
```
Or set environment variable: `export FRAGMENT_DISABLE_STATS=1`

**Live Dashboard:** [fragment.s1qwy.ru/statistic](https://fragment.s1qwy.ru/statistic)

---

## 💳 EVM Payment Methods (v7.0.0)

| Method | Chain | Token | Flow |
|--------|-------|-------|------|
| `ton` | TON | TON | Automatic TX |
| `usdt_ton` | TON | USDT | Automatic TX |
| `usdt_eth` | Ethereum | USDT | Returns invoice |
| `usdt_pol` | Polygon | USDT | Returns invoice |
| `usdc_eth` | Ethereum | USDC | Returns invoice |
| `usdc_base` | BASE | USDC | Returns invoice |
| `usdc_pol` | Polygon | USDC | Returns invoice |

```python
# EVM example — you send the transaction
result = await client.purchase_stars("@durov", 50, payment_method="usdc_base")

if isinstance(result, EvmPaymentResult):
    inv = result.invoice
    # Send {inv.invoice_amount} {inv.token_symbol} 
    # to {inv.invoice_address} on chain_id={inv.invoice_chain_id}
    # before {inv.expires_at}
```

---

## 🐛 Reporting Errors

Create an [Issue](https://github.com/s1qwy/fragment-api-py/issues) or message in [Telegram chat](https://t.me/fragment_api_py).

---

## 💖 Support the Project

If you find this library useful, consider supporting its development:

<p align="center">
  <a href="https://app.tonkeeper.com/transfer/UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj">
    <img src="https://img.shields.io/badge/Donate-TON-0098ea?style=for-the-badge&logo=ton&logoColor=white" alt="Donate TON">
  </a>
</p>

<p align="center">
  <code>UQBsyxZvyQxDwAeOxoaWwO2HJoAmCKUoJlS_OpLzWHD9i2Xj</code>
</p>

---

## 📄 License

**MIT License** — free for commercial and personal use.

---

<p align="center">
  <a href="https://github.com/s1qwy/fragment-api-py">GitHub</a> •
  <a href="https://fragment.s1qwy.ru">Documentation</a> •
  <a href="https://t.me/fragment_api_py">Telegram</a> •
  <a href="https://fragment.s1qwy.ru/statistic">Live Stats</a>
</p>