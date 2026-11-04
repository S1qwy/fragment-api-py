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

## Release 14.3.0

Fragment restored `/my/profile`. `get_profile()` now reads the Telegram username, account details, `identity_verified` and `wallet_verified` from that page. Account and wallet badges are parsed separately.

Monetization withdrawals can require KYC. `init_stars_withdrawal`, `confirm_stars_withdrawal`, `init_ads_withdrawal` and `confirm_ads_withdrawal` raise `KycRequiredError` when Fragment requests verification. Complete verification on Fragment and retry explicitly. The SDK never completes KYC automatically.

Purchase and giveaway operations remain available without KYC. No blanket profile check is added to payments. The unified `purchase` API and external TRON invoices from 14.2.0 are retained.

## Previous release 14.2.0

USDT on TRON uses `payment_method="usdt_tron"` and returns `ExternalPaymentResult` with an `ExternalInvoice`. TRON payments are external: the SDK does not sign or broadcast TRC-20 transfers.

### API migration

Use `purchase("stars", username, amount)`, `purchase("premium", username, months=3)`, or `purchase("ton", username, amount)`. Batch purchases use `purchase([...])` and retain one combined TON submission. The separate `purchase_stars`, `purchase_premium`, `topup_gram`, `topup_ton`, and `batch_purchase` methods are removed.

Function-style `FragmentAPI.methods` adapters, `list_sessions`, `ConfigError`, `VerificationError`, and old `EvmInvoice` / `EvmPaymentResult` names are removed. Use `FragmentClient`, `get_sessions`, `ConfigurationError`, `FragmentAPIError`, and the `External*` classes. Payment method aliases `gram` and `usdt_gram` are removed; use `ton` and `usdt_ton`.


Shared authentication has been removed. Fragment requests now use your own cookie session, with explicit authentication using your own wallet when needed.

| Area | What changed |
|:--|:--|
| Authentication | The built-in public auth seed, automatic shared-wallet proof, and shared-mode options are removed |
| Sessions | Fragment HTTP operations require user-owned cookies; missing cookies fail before any request |
| Batches | All batches return `BatchResult`; the shared-mode result type is removed |
| Profile | `get_profile()` reads the restored `/my/profile` route and verification badges |
| Account fields | Name, username, photo, wallet address/label, identity and wallet verification |
| API errors | Revenue withdrawals raise `KycRequiredError` on a server verification request; other errors use `FragmentAPIError` |
| Giveaways | Stars recipient search sends only `query`, matching the current Fragment interface |
| Marketplace | Wallet owners and history support the current `gram.org/address/` explorer links |

Remove `shared_auth_seed` and `wallet_auth` constructor arguments and stop using `nokyc_mode` or `NoKycBatchResult`. Supply `cookies` directly, load them from session storage, or call `FragmentClient.authenticate()` with your own wallet before constructing the client. No built-in wallet is used for authentication or payment.

`ProfileInfo.identity_verified` and `wallet_verified` are restored in 14.3.0 with the profile page.

Live checks on November 2, 2026 returned request IDs and unsigned native-TON transactions for Stars, Premium, both giveaway types, and Ads top-ups without a verification challenge in the tested session. No payments were submitted. Withdrawals and asset mutations require valid operation links or assets and were not exercised by that check.

> [!IMPORTANT]
> Version 14 includes breaking changes. Batches combine all invoices into one wallet submission
> and reject preparation/capacity failures before sending. TON preparation requires a real payer
> identity. Fulfillment remains per invoice.
> Read the [migration notes](https://github.com/S1qwy/fragment-api-py/wiki/Home#migrating-to-1400) before upgrading.

## Choose your workflow

| Workflow | Configuration | Result |
|:--|:--|:--|
| Account browsing | Your Fragment cookies | Marketplace and user-owned account data |
| External TON signing | Your cookies and a complete sender account or offline-derived payer account | `PreparedTransaction` |
| Automatic TON payment | Your cookies, payer seed and blockchain API key | Broadcast receipt with explicit confirmation state |
| EVM payment | Your cookies and a supported EVM payment method | An invoice for external payment |

All Fragment HTTP operations require a user-owned cookie session. Native automatic payments additionally require a wallet-connected session.

Constructing a client without cookies is supported for offline validation and wallet utilities. It does not trigger authentication. Explicit login and cookie refresh use only the seed supplied by the caller.

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
| Buy Stars or Premium | [Stars](https://github.com/S1qwy/fragment-api-py/blob/main/examples/purchase_stars.py) · [Premium](https://github.com/S1qwy/fragment-api-py/blob/main/examples/purchase_premium.py) |
| Prepare an external payment | [External signing](https://github.com/S1qwy/fragment-api-py/blob/main/examples/external_signing.py) |
| Search gifts and attributes | [Marketplace search](https://github.com/S1qwy/fragment-api-py/blob/main/examples/search_marketplace.py) |
| Handle payment outcomes | [Error handling](https://github.com/S1qwy/fragment-api-py/blob/main/examples/error_handling.py) |

**[Browse the complete example guide](https://github.com/S1qwy/fragment-api-py/wiki/Examples)**

## Batches, fees, and recovery

`purchase(items)` prepares all invoices and submits their combined messages
in one wallet transaction. A batch that exceeds wallet capacity is rejected
before broadcasting; it is never silently split. In preparation mode,
`result.transaction` contains the combined payload for external signing.

Native TON purchases include a separate **1.5%** service fee
(`FEE_BASIS_POINTS = 150`), sent to `FEE_ADDRESS` in
`FragmentAPI/types/constants.py`. This is additional to network fees and separate
from voluntary support. Inspect `payment_nanoton`, `fee_nanoton`,
`gas_reserve_nanoton`, and `required_nanoton` before signing. The percentage fee
does not apply to USDT or external EVM payments.

Automatic payments durably record the signed BOC before broadcast. Use
`list_payments()`, `get_payment(operation_id)`, and
`reconcile_payment(operation_id)` to recover after cancellation or restart
without repeating a blockchain payment. The default journal and wallet locks
are stored under `~/.fragment-api`; deployments must preserve that directory.

See [payment batches and recovery](https://github.com/S1qwy/fragment-api-py/wiki/Payment-Batches-and-Recovery) for result semantics,
confirmation limits, operator resolution, and coordination across processes/hosts.

## Payment networks

| Method | Network | Asset | SDK behavior |
|:--|:--|:--|:--|
| `ton` | TON | TON | Prepare or broadcast |
| `usdt_ton` | TON | USDT | Prepare or broadcast |
| `usdt_tron` | TRON | USDT | External invoice |
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
- Local clients/processes sharing a payer use OS wallet locks and a durable journal.
  Multi-host deployments must configure shared payment storage and distributed locks.
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
  <a href="https://opensource.org/licenses/MIT">MIT License</a>
</p>
