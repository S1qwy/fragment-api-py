<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="112" alt="Fragment">
</p>

<h1 align="center">Fragment API Python</h1>

<p align="center">
  <strong>One async client. Explicit payment states. A complete Fragment workspace.</strong>
</p>

<p align="center">
  Stars · Premium · Gifts · Usernames · Numbers · Ads · Gateway
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py?style=flat-square&color=0098EA&label=PyPI" alt="PyPI version"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/badge/Python-3.10%2B-182C44?style=flat-square" alt="Python 3.10 and newer"></a>
  <a href="https://github.com/S1qwy/fragment-api-py/wiki"><img src="https://img.shields.io/badge/Documentation-Wiki-0098EA?style=flat-square" alt="Documentation"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-182C44?style=flat-square" alt="MIT license"></a>
</p>

<p align="center">
  <a href="https://github.com/S1qwy/fragment-api-py/wiki"><strong>Read the documentation</strong></a>
  &nbsp; / &nbsp;
  <a href="https://github.com/S1qwy/fragment-api-py/tree/main/examples"><strong>Explore examples</strong></a>
  &nbsp; / &nbsp;
  <a href="https://github.com/S1qwy/fragment-api-py/issues"><strong>Report an issue</strong></a>
</p>

---

## Built for explicit workflows

**fragment-api-py** is an unofficial asynchronous Python SDK for Fragment.com.

Browse the marketplace, resolve recipients, prepare transactions for external signing, or configure a payer wallet for automatic broadcasting. Work with typed results instead of treating every accepted request as a completed purchase.

<table>
<tr>
<td width="33%" valign="top">

### Purchase

Telegram Stars, Premium gifts, channel giveaways, Ads top-ups, and Gateway credits.

</td>
<td width="33%" valign="top">

### Discover

Search usernames, collectible numbers, and gifts. Inspect attributes, prices, ownership, and auction history.

</td>
<td width="33%" valign="top">

### Manage

Operate user-owned assets, listings, offers, assignments, withdrawals, and sessions.

</td>
</tr>
</table>

## Release 13.0.0

A new authentication and transaction architecture.

| Area | What changed |
|:--|:--|
| Authentication | Restricted wallet-proof sessions replace the MarketApp integration |
| Transport | A reusable client-owned HTTP session with cached API hashes |
| Payments | Distinct unsigned preparation, broadcast, and fulfillment states |
| Wallets | V4R2, V5R1, HighloadV2, and HighloadV3R1 configuration |
| Batches | Ordered invoice processing with per-item outcomes |
| Storage | Atomic file replacement, collision-resistant filenames, and explicit Redis cleanup |
| Parsing | Table-fragment handling, decimal preservation, responsive statuses, and merged gift filters |
| Validation | Strict integer inputs, original giveaway package limits, and capability guards |

> [!IMPORTANT]
> Version 13 includes breaking changes. MarketApp parameters and exports are removed.
> Batch purchases no longer represent a single transaction across multiple invoices.
> Read the [migration notes](https://github.com/S1qwy/fragment-api-py/wiki/Home#migrating-to-1300) before upgrading.

## Choose your workflow

| Workflow | Configuration | Result |
|:--|:--|:--|
| Account browsing | Your Fragment cookies | Marketplace and user-owned account data |
| Restricted session | No cookies; wallet authentication | Allowed public and purchase workflows |
| External TON signing | A complete sender account or an offline-derived payer account, without automatic payment credentials | `PreparedTransaction` |
| Automatic TON payment | Payer seed and blockchain API key | Broadcast receipt with explicit confirmation state |
| EVM payment | Supported EVM payment method | An invoice for external payment |

Account operations require a user-owned cookie session. Native automatic payments in cookie mode additionally require a wallet-connected session.

Restricted wallet authentication does not bypass Fragment verification requirements. The shared authentication wallet is separate from the configured payer.

## Installation

**Python 3.10 or newer**

Install from [PyPI](https://pypi.org/project/fragment-api-py/) with `pip install fragment-api-py`.

Optional integrations:

| Extra | Installation |
|:--|:--|
| Redis storage | `pip install "fragment-api-py[redis]"` |
| Terminal QR rendering | `pip install "fragment-api-py[qr]"` |
| Development tools | `pip install "fragment-api-py[dev]"` |

Automatic TON payments require a valid mnemonic and a provider key from [Tonconsole](https://tonconsole.com/) or [Toncenter](https://toncenter.com/).

## Start with an example

The repository keeps executable examples in one place rather than duplicating code throughout the documentation.

| Your goal | Start here |
|:--|:--|
| Configure the client | [Basic setup](https://github.com/S1qwy/fragment-api-py/blob/main/examples/basic_setup.py) |
| Authenticate a full account | [Authentication](https://github.com/S1qwy/fragment-api-py/blob/main/examples/authentication.py) |
| Understand restricted mode | [Wallet authentication](https://github.com/S1qwy/fragment-api-py/blob/main/examples/wallet_auth.py) |
| Buy Stars or Premium | [Stars](https://github.com/S1qwy/fragment-api-py/blob/main/examples/purchase_stars.py) · [Premium](https://github.com/S1qwy/fragment-api-py/blob/main/examples/purchase_premium.py) |
| Prepare an external payment | [External signing](https://github.com/S1qwy/fragment-api-py/blob/main/examples/external_signing.py) |
| Search gifts and attributes | [Marketplace search](https://github.com/S1qwy/fragment-api-py/blob/main/examples/search_marketplace.py) |
| Handle payment outcomes | [Error handling](https://github.com/S1qwy/fragment-api-py/blob/main/examples/error_handling.py) |

**[Browse the complete example guide](https://github.com/S1qwy/fragment-api-py/wiki/Examples)**

## Payment networks

| Method | Network | Asset | SDK behavior |
|:--|:--|:--|:--|
| `ton`, `gram` | TON | TON | Prepare or broadcast |
| `usdt_ton`, `usdt_gram` | TON | USDT | Prepare or broadcast |
| `usdt_eth` | Ethereum | USDT | External invoice |
| `usdt_pol` | Polygon | USDT | External invoice |
| `usdc_eth` | Ethereum | USDC | External invoice |
| `usdc_base` | Base | USDC | External invoice |
| `usdc_pol` | Polygon | USDC | External invoice |

Availability is subject to Fragment's response and operation-specific restrictions. Ads and Gateway recharge flows use native TON.

## Know what happened

| State | Meaning |
|:--|:--|
| Prepared | An unsigned transaction exists; nothing has been broadcast |
| Broadcast | The wallet call returned; fulfillment has not necessarily completed |
| Confirmed | The purchase flow observed Fragment's completion signal |
| Unknown | The broadcast outcome could not be established; reconciliation is required |

> [!WARNING]
> Do not automatically repeat a payment after an uncertain broadcast or a fulfillment timeout.
> Reconcile the original request first.

## Documentation

<table>
<tr>
<td width="50%" valign="top">

**Integration**

[Client and authentication](https://github.com/S1qwy/fragment-api-py/wiki/Client-and-Authentication)  
[Purchases and giveaways](https://github.com/S1qwy/fragment-api-py/wiki/Purchases-and-Giveaways)  
[Data models](https://github.com/S1qwy/fragment-api-py/wiki/Data-Models)  
[Exceptions and limits](https://github.com/S1qwy/fragment-api-py/wiki/Exceptions-and-Limits)

</td>
<td width="50%" valign="top">

**Marketplace and operations**

[Marketplace and search](https://github.com/S1qwy/fragment-api-py/wiki/Marketplace-and-Search)  
[Asset management](https://github.com/S1qwy/fragment-api-py/wiki/Asset-Management)  
[Executable examples](https://github.com/S1qwy/fragment-api-py/wiki/Examples)  
[Issue tracker](https://github.com/S1qwy/fragment-api-py/issues)

</td>
</tr>
</table>

## Operational notes

- Reuse a client and close it with an asynchronous context manager or `aclose()`.
- Keep payer credentials, session cookies, and login codes out of source control and logs.
- Use your own sender account for external signing.
- Never deposit funds into the shared authentication wallet.
- Coordinate access when multiple clients or processes use the same payer.
- Fragment HTML and private endpoints can change independently of this package.
- This project is not affiliated with or endorsed by Fragment, Telegram, or TON.

## Support the project

Development, maintenance, and issue reports are welcome.

<p>
  <a href="https://app.tonkeeper.com/transfer/UQAcsdD09x9dzj7Jc-MznN-SLUxPPMmwKQxsC2Ax_F03TBAH">
    <img src="https://img.shields.io/badge/Support_with_TON-0098EA?style=for-the-badge&logo=ton&logoColor=white" alt="Support with TON">
  </a>
</p>

**TON address**

`UQAcsdD09x9dzj7Jc-MznN-SLUxPPMmwKQxsC2Ax_F03TBAH`

---

<p align="center">
  <a href="https://github.com/S1qwy/fragment-api-py">GitHub</a>
  &nbsp; / &nbsp;
  <a href="https://github.com/S1qwy/fragment-api-py/wiki">Documentation</a>
  &nbsp; / &nbsp;
  <a href="https://t.me/fragment_api_lib">Telegram</a>
  &nbsp; / &nbsp;
  <a href="https://opensource.org/licenses/MIT">MIT License</a>
</p>