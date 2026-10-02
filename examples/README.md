# Example Workspace

**Fragment API Python · 13.0.0**

[Documentation](https://github.com/S1qwy/fragment-api-py/wiki) · [Example guide](https://github.com/S1qwy/fragment-api-py/wiki/Examples) · [Repository](https://github.com/S1qwy/fragment-api-py)

---

## Before you start

These are executable examples, not a payment queue or a production transaction processor.

Run scripts from the repository root. Each script accepts an optional action name and exposes its available actions through `--help`.

For example, `python examples/prices.py --help` lists price actions. `python examples/prices.py custom` requests a custom Stars quote.

Install the project with `pip install -e .`. Interactive QR rendering additionally requires the `qr` extra; Redis storage requires the `redis` extra.

> [!IMPORTANT]
> Actions that broadcast payments or change account state require `--execute`.
> This is an example-level safeguard, not a restriction built into FragmentClient.

## Configuration

Configuration comes from environment variables. The examples do not automatically load `.env` files.

| Variable | Purpose |
|:--|:--|
| `FRAGMENT_COOKIES` | JSON object or Cookie header string for a user-owned Fragment session |
| `TON_SEED` | Valid payer mnemonic; also usable for offline account derivation |
| `TON_API_KEY` | Blockchain provider key |
| `TON_API_PROVIDER` | `tonapi` or `toncenter`; defaults to `tonapi` |
| `TON_WALLET_VERSION` | Defaults to `V5R1` |
| `TON_SENDER_ACCOUNT` | Complete TON Connect account as JSON for external signing |
| `FRAGMENT_SHARED_AUTH_SEED` | Optional restricted authentication seed override |
| `FRAGMENT_PROXY` | Optional HTTP or SOCKS proxy URL |
| `FRAGMENT_TARGET` | Recipient username |
| `FRAGMENT_SECOND_TARGET` | Second batch recipient |
| `FRAGMENT_CHANNEL` | Giveaway channel |
| `FRAGMENT_NUMBER` | User-owned anonymous number |
| `FRAGMENT_SLUG` | Asset identifier |
| `FRAGMENT_ITEM_TYPE` | `1`, `3`, or `5`; defaults to `1` |
| `FRAGMENT_CATEGORY` | `usernames`, `numbers`, or `gifts` |
| `FRAGMENT_TON_AMOUNT` | Explicit integer bid, offer, or listing amount |
| `FRAGMENT_ACCOUNT_ID` | Ads or Gateway account identifier |
| `FRAGMENT_QUERY` | Marketplace search text |
| `FRAGMENT_COLLECTION` | Gift collection slug |
| `FRAGMENT_ATTRIBUTE` | `Model`, `Backdrop`, or `Symbol` |
| `FRAGMENT_ATTRIBUTE_VALUE` | Exact value returned by gift filters |
| `FRAGMENT_ASSIGN_TO` | Assignment destination identifier |
| `FRAGMENT_SESSION_DIR` | File storage directory |
| `FRAGMENT_SESSION_ID` | Storage session identifier |
| `FRAGMENT_TERMINATE_SESSION_ID` | Exact Fragment session to terminate |
| `TELEGRAM_PHONE` | Phone number for interactive Telegram authentication |
| `REDIS_URL` | Redis connection URL |
| `FRAGMENT_PREPARED_FILE` | Unsigned transaction export path |
| `FRAGMENT_REQ_ID` | Original invoice request identifier |
| `TON_SIGNED_BOC` | Signed, already broadcast BOC |
| `FRAGMENT_CONFIRM_REFERER` | Original invoice page path |
| `FRAGMENT_TRANSACTION` | Withdrawal transaction identifier |
| `FRAGMENT_WITHDRAWAL_DATA` | Original Stars withdrawal state |
| `FRAGMENT_CONFIRM_HASH` | Reviewed withdrawal approval challenge |

`TON_SENDER_ACCOUNT` must contain `address`, `chain`, `publicKey`, and `walletStateInit`. The supported chain is mainnet, `-239`.

## Execution modes

| Mode | Behavior |
|:--|:--|
| Read | Does not configure a payer seed or provider key |
| Wallet | Configures payer credentials for balance inspection |
| Prepare | Configures a sender account but deliberately omits the provider key |
| Pay | Requires `--execute`, a payer seed, and a provider key |

The read mode can still create an unpaid invoice when an invoice action is selected.

Without cookies, the client uses restricted wallet authentication. It does not gain access to private account features.

## Important behavior

- `PreparedTransaction` means nothing was broadcast.
- An EVM invoice must be paid externally.
- A broadcast identifier does not establish fulfillment.
- Check `confirmed` and `confirmation_error`.
- Stop after an unknown broadcast outcome and reconcile before sending another payment.
- A batch processes invoices individually; it is not one transaction for all recipients.
- Wallet locks belong to one client instance. They do not coordinate separate processes.
- File storage contains credentials in plaintext. Protect its directory.
- The shared authentication mnemonic is not a safe place to hold funds.
- Preserve the original Fragment session when confirming an externally signed invoice.

## File map

| Area | Files |
|:--|:--|
| Setup and authentication | `basic_setup.py`, `authentication.py`, `wallet_auth.py`, `session_storage.py` |
| Payments | `purchase_stars.py`, `purchase_premium.py`, `batch_purchase.py`, `giveaways.py` |
| External payments | `external_signing.py`, `evm_payment_automation.py` |
| Ads and Gateway | `topup_grams.py`, `gateway_and_ads.py` |
| Marketplace | `search_marketplace.py`, `item_details.py`, `prices.py` |
| Account operations | `wallet_and_profile.py`, `transaction_history.py`, `marketplace_bids_and_auctions.py` |
| Transfers and numbers | `nft_transfers_and_withdrawals.py`, `anonymous_numbers.py` |
| Integration | `raw_api_calls.py`, `error_handling.py`, `backward_compatibility.py`, `logging_setup.py` |

`_common.py` provides configuration, action selection, execution guards, and result summaries. It is not intended to be run directly.