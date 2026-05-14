<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python</h1>

<p align="center">
  <strong>Professional Python library for Fragment.com automation</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py.svg?style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/pyversions/fragment-api-py.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://pepy.tech/projects/fragment-api-py/"><img src="https://static.pepy.tech/personalized-badge/fragment-api-py?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads" alt="PyPI Downloads"></a>
  <a href="https://t.me/fragment_api_py"><img src="https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=flat-square&logo=telegram" alt="Telegram"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
</p>

---

**Fragment API Python** — complete Fragment.com automation: purchase Stars/Premium, giveaways, marketplace, bids, number management. **Async-only**.

📚 [Documentation](https://fragment.s1qwy.ru) | 💬 [Telegram Chat](https://t.me/fragment_api_py)

---

## Features

- **Async-only** — `FragmentClient` with full async/await support
- **Purchases** — Stars (50–10M), Premium (3/6/12 months), TON Ads, `payment_method="ton"|"usdt_ton"`
- **Giveaways** — Stars and Premium for channels
- **Bids** — `place_bid(item_type=1|3|5, slug, bid)` — if bid equals buy-now price, purchase is instant
- **Marketplace** — search usernames, numbers, gifts with filters and pagination
- **Wallet** — V4R2 and V5R1 (W5) support
- **Auto-authentication** — obtain cookies via TON wallet and Telegram
- **Anonymous numbers** — manage login codes and terminate sessions
- **NFT Management** — withdraw gifts to wallet, transfer to other users
- **Stars Revenue** — withdraw earned Stars to wallet
- **Errors** — complete exception hierarchy; report unknown errors via [issues](https://github.com/S1qwy/fragment-api-py/issues)

---

## Installation

```bash
pip install fragment-api-py
```

---

## Quick Start

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    client = FragmentClient(
        seed="24 words...",
        cookies={"stel_ssid": "...", "stel_token": "...", ...}
    )

    # Wallet info
    w = await client.get_wallet()
    print(f"{w.balance_ton} TON, {w.balance_usdt} USDT")

    # Purchase Stars (USDT)
    await client.purchase_stars("@durov", 100, payment_method="usdt_ton")

    # Purchase Premium (TON, show sender)
    await client.purchase_premium("@durov", 6, show_sender=True)

    # Place bid on username (type 1)
    await client.place_bid(1, "username", bid=150)  # 150 TON

    # Stars giveaway in channel
    await client.giveaway_stars("@channel", winners=5, amount=1000)

    # Search marketplace
    items = await client.search_usernames("gold", filter="sale")

asyncio.run(main())
```

## Auto-cookie Authentication (authenticate method)

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

    client = FragmentClient(seed="...", cookies=cookies)

asyncio.run(main())
```

## Async Context Manager

```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    async with FragmentClient(seed="...", cookies=...) as client:
        wallet = await client.get_wallet()
        result = await client.place_bid(3, "123456789", bid=50)  # number

asyncio.run(main())
```

## Requirements

- Python 3.10+
- Fragment cookies: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`
- TON wallet seed phrase

## Reporting Errors

For unknown errors — create an [Issue](https://github.com/S1qwy/fragment-api-py/issues) or message in [Telegram chat](https://t.me/fragment_api_py). This helps expand the exception database.

---

**MIT License**