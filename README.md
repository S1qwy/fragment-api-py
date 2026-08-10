<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python SDK</h1>

<p align="center">
  <strong>Professional Python library for Fragment.com automation</strong><br>
  <strong>v9.0.0 — Batch Operations | EVM Payments | Tonconsole Integration</strong>
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
</p>

---

## <img src="https://img.shields.io/badge/-What's_New_in_v9.0.0-black?style=flat-square" valign="middle">

| Feature | Description |
|---------|-------------|
| **Strict Initialization** | `api_key` (Tonconsole) and `cookies` are now **strictly required** for all operations. Built-in proxies and No-KYC modes were removed to guarantee maximum reliability and security. |
| **Batch Operations** | Execute multiple sequential transactions efficiently in a single on-chain operation using the unified `batch_purchase` method. |
| **EVM Payments** | Native support for 5 EVM methods: `usdt_eth`, `usdt_pol`, `usdc_eth`, `usdc_base`, `usdc_pol`. |

---

## <img src="https://img.shields.io/badge/-Features-black?style=flat-square" valign="middle">

- **Async-only** — `FragmentClient` with full async/await support.
- **Reliable Networking** — Requires a direct Tonconsole `api_key` for maximum uptime.
- **Purchases** — Stars (50–10M), Premium (3/6/12 months), TON Ads.
- **Giveaways** — Stars and Premium for channels (up to 24k winners).
- **Bids** — `place_bid(item_type=1|3|5, slug, bid)` — instant buy if bid = buy-now price.
- **Marketplace** — Search usernames, numbers, gifts with filters and pagination.
- **Wallet** — V4R2 and V5R1 (W5) support via `tonutils`.
- **Auto-authentication** — Obtain cookies via TON wallet and Telegram.
- **Anonymous numbers** — Manage login codes, terminate sessions (+888).
- **NFT Management** — Withdraw gifts to wallet, transfer to users.

---

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
  <a href="https://fragment.s1qwy.ru">Documentation</a> •
  <a href="https://t.me/fragment_api_py">Telegram</a>
</p>
