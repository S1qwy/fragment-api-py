<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python SDK</h1>

<p align="center">
  <strong>Professional Python library for Fragment.com automation</strong><br>
  <strong>v8.0.0 — No KYC Mode | Batch Operations | EVM Payments | Live Stats Dashboard</strong>
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

## <img src="https://img.shields.io/badge/-What's_New_in_v8.0.0-black?style=flat-square" valign="middle">

| Feature | Description |
|---------|-------------|
| **No KYC Mode** | Operate without Fragment cookies or account. Execute purchases and giveaways directly via a hosted REST API (`fragment-api.tech`). |
| **Batch Operations** | Execute multiple sequential transactions easily with `batch_purchase_stars`, `batch_purchase_premium`, and `batch_topup_ton`. |
| **EVM Payments** | Native support for 5 EVM methods: `usdt_eth`, `usdt_pol`, `usdc_eth`, `usdc_base`, `usdc_pol`. |
| **Anonymous Telemetry** | Helps improve the library. No sensitive data is ever sent. View stats at [fragment.s1qwy.ru/statistic](https://fragment.s1qwy.ru/statistic). |

---

## <img src="https://img.shields.io/badge/-Features-black?style=flat-square" valign="middle">

- **Async-only** — `FragmentClient` with full async/await support.
- **Two Operating Modes** — Full mode (with cookies) and No-Cookie Mode (No KYC required).
- **Purchases** — Stars (50–10M), Premium (3/6/12 months), TON Ads.
- **Giveaways** — Stars and Premium for channels (up to 24k winners).
- **Bids** — `place_bid(item_type=1|3|5, slug, bid)` — instant buy if bid = buy-now price.
- **Marketplace** — Search usernames, numbers, gifts with filters and pagination.
- **Wallet** — V4R2 and V5R1 (W5) support.
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
- Fragment cookies (optional, only for full functionality)

---

## <img src="https://img.shields.io/badge/-Operating_Modes-black?style=flat-square" valign="middle">

The library now supports two operating modes depending on your privacy needs and workflow:

### 1. No KYC / No-Cookie Mode
Perfect for automated systems that do not want to manage Fragment cookies or pass KYC verifications. By initializing the client without cookies, operations utilize the hosted `fragment-api.tech` REST API to securely obtain unsigned transaction payloads, sign them locally with your seed, and broadcast them to the network.
*Note: EVM payment methods are not supported in No-Cookie mode (TON and USDT on TON only).*

**Supported No-Cookie Methods:**
- `purchase_stars`
- `purchase_premium`
- `topup_ton`
- `giveaway_stars`
- `giveaway_premium`
- All `batch_*` variants of the above

### 2. Full Mode
Pass your Fragment session cookies (`stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`) to access the entirety of Fragment's API, including marketplace operations, EVM payments, NFT management, and My Assets.

---

## <img src="https://img.shields.io/badge/-Quick_Start-black?style=flat-square" valign="middle">

### No KYC Mode Example
```python
import asyncio
from FragmentAPI import FragmentClient

async def main():
    # Initialize WITHOUT cookies
    async with FragmentClient(
        seed="24 words...",
        wallet_version="V5R1"
    ) as client:
        
        # Wallet info
        wallet = await client.get_wallet()
        print(f"Balance: {wallet.balance_ton} TON, {wallet.balance_usdt} USDT")
        
        # Purchase stars without a Fragment account!
        result = await client.purchase_stars("@durov", 100)
        print(f"TX: {result.transaction_id}")
        
        # Execute batch operations
        batch = await client.batch_purchase_premium([
            {"username": "@durov", "months": 3},
            {"username": "@telegram", "months": 6}
        ])
        print(f"Succeeded: {batch.succeeded}/{batch.total}")

asyncio.run(main())
```

### Full Mode Example
```python
import asyncio
from FragmentAPI import FragmentClient
from FragmentAPI.types.results import EvmPaymentResult

async def main():
    # Initialize WITH cookies for full functionality
    async with FragmentClient(
        seed="24 words...",
        cookies={"stel_ssid": "...", "stel_token": "...", "stel_dt": "...", "stel_ton_token": "..."},
        wallet_version="V5R1",
    ) as client:
        
        # EVM payment (returns invoice)
        result = await client.purchase_stars("@durov", 50, payment_method="usdc_base")
        if isinstance(result, EvmPaymentResult):
            inv = result.invoice
            print(f"Send {inv.invoice_amount} {inv.token_symbol} to {inv.invoice_address}")
            print(f"Chain: {inv.invoice_chain_name}")
        
        # Place bid (type 1=username, 3=number, 5=gift)
        await client.place_bid(1, "username", bid=150)
        
        # Search marketplace
        items = await client.search_usernames("gold", filter="sale")

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
    
    async with FragmentClient(seed="24 words...", cookies=cookies) as client:
        profile = await client.get_profile()
        print(f"Logged in as: {profile.name}")

asyncio.run(main())
```

---

## <img src="https://img.shields.io/badge/-Anonymous_Telemetry-black?style=flat-square" valign="middle">

The library sends anonymous usage statistics to help understand which features are used and what errors users encounter.

**Collected:**
- Library version, wallet version (V4R2/V5R1)
- Method name, status (ok/error), duration
- Error class name, scrubbed error message (first 200 chars)

**NEVER Collected:**
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
  <a href="https://t.me/fragment_api_py">Telegram</a> •
  <a href="https://fragment.s1qwy.ru/statistic">Live Stats</a>
</p>