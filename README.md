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

> [!CAUTION]
> **Security incident affecting `fragment-api-py==14.4.2`.** This unauthorized PyPI release contained code that could transfer funds from a configured wallet. The release was removed from PyPI. If you installed it, stop jobs that use it and rebuild affected environments from trusted artifacts. See [issue #8](https://github.com/S1qwy/fragment-api-py/issues/8).
>
> **Never connect your primary wallet to automation.** Use a separate wallet and fund it only with what you need for the next operations and can afford to lose.

## Built for explicit workflows

**fragment-api-py** is an unofficial asynchronous Python SDK for Fragment.com.

Browse the marketplace, resolve recipients, prepare transactions for external signing, or configure a payer wallet for automatic broadcasting. Work with typed results instead of treating every accepted request as a completed purchase.

<table>
<tr>
<td width="33%" valign="top">

### Purchase

Telegram Stars, Premium gifts, channel giveaways, Ads account recharges, and Gateway credits.

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

## Gram Earnings top-ups removed

Fragment removed Telegram account balance top-ups. The SDK removes `purchase("ton", ...)`, Gram top-up batch items, and `get_ads_topup_recipient()`. Stars, Premium, Ads account recharge and Gateway retain their own workflows. Past top-up records remain available through `get_topup_history()`.

## BNB Smart Chain payments

Use `payment_method="usdt_bsc"` to create an external USDT invoice on BNB Smart Chain. The invoice exposes the raw amount and token precision for payment from an external wallet.

## Revenue withdrawal links

Revenue withdrawal links now have a three-stage API for `/stars/withdraw` and `/ads/withdraw`:

```python
info = await client.inspect_withdrawal(url)  # GET only
request = await client.prepare_withdrawal(url)  # server initialization, state-changing
# Review request.destination and request.confirm_message in your application.
if request.confirmation_required:
    result = await client.confirm_withdrawal(request)  # explicit submission
```

`WithdrawalInfo` includes the link kind, mode, destination and optional amount/currency/source fields when exposed as form values. Missing metadata is `None`; units are never inferred. `kyc_required=None` means the page did not state a requirement, not that KYC is unnecessary. `prepare_withdrawal()` can still raise `KycRequiredError` based on the server response.

Preparation calls the server's initialization endpoint. Fragment can return a result without a confirmation challenge, so preparation must be treated as state-changing. Inspect `request.server_response` and do not automatically repeat it. Confirmation requires the returned challenge and the original destination account. A challenge is submitted at most once per client instance, including after a network error; this guard is not a durable cross-process journal. After an uncertain result, inspect the original withdrawal in Telegram/Fragment before retrying.

Use the same user-owned cookies throughout. Configure a payer seed or `sender_account` to select the withdrawal destination; a blockchain API key is not needed for these HTTP calls. This flow does not sign a TON payment or obtain withdrawal links from Telegram. Generate a valid link in Telegram first. Real reward withdrawals were not performed during development.

Link tokens, opaque state and confirmation hashes are hidden from model `repr`, but serialization still contains them: keep exported requests private. Invalid hosts/routes, duplicate or empty transaction parameters and expired/mismatched link state are rejected. NFT withdrawal links retain their existing separate methods.

## Upgrading

See the [migration guide](https://github.com/S1qwy/fragment-api-py/wiki/Migrations) for breaking changes and previous API transitions.

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

Install from GitHub using a pinned release commit. This is the recommended source.

```sh
python -m pip install "fragment-api-py @ git+https://github.com/S1qwy/fragment-api-py.git@04a0601b6cc7f11af0291683ddd773b2d96eb689"
```

With uv:

```sh
uv add "fragment-api-py @ git+https://github.com/S1qwy/fragment-api-py.git@04a0601b6cc7f11af0291683ddd773b2d96eb689"
```

[PyPI](https://pypi.org/project/fragment-api-py/14.4.1/) is also available. Pin the known release with `python -m pip install "fragment-api-py==14.4.1"`.

Optional integrations:

| Extra | Name |
|:--|:--|
| Redis storage | `redis` |
| Terminal QR rendering | `qr` |
| Development tools | `dev` |

To install an extra, replace `fragment-api-py` before `@` with its extras form, such as `fragment-api-py[redis]`.

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
| `usdt_bsc` | BNB Smart Chain | USDT | External invoice |
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
