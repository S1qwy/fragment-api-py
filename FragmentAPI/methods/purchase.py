"""
Unified purchase engine for Fragment.

Handles single and batched purchases for Stars, Premium, and Ads GRAM/TON.
Automatically chunks multiple purchases into batched on-chain TON transactions
based on wallet version limits (V4R2: 4, V5R1: 255).
Supports both GRAM on-chain and EVM invoice payment flows.
"""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

from curl_cffi import requests

from FragmentAPI.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    PaidMessageLimitError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
    WalletError,
)
from FragmentAPI.types.constants import (
    ADS_TOPUP_PAGE,
    BATCH_PAYMENT_METHODS,
    DEVICE_FINGERPRINT,
    EVM_PAYMENT_METHODS,
    GRAM_PAYMENT_METHODS,
    GRAM_TOPUP_MAX,
    GRAM_TOPUP_MIN,
    MIN_GRAM_BALANCE,
    PREMIUM_GIFT_PAGE,
    PREMIUM_MONTHS_VALID,
    PURCHASE_TYPES,
    STARS_PAGE,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
    VALID_PAYMENT_METHODS,
    WALLET_MAX_MESSAGES,
)
from FragmentAPI.types.results import (
    BatchItemResult,
    BatchResult,
    EvmPaymentResult,
    PurchaseItem,
    PurchaseResult,
)
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_fragment_api,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_batch_transaction,
    execute_transaction,
    fetch_wallet_info,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

logger = logging.getLogger("FragmentAPI")

_TYPE_PAGE_MAP: dict[str, str] = {
    "stars": STARS_PAGE,
    "premium": PREMIUM_GIFT_PAGE,
    "gram": ADS_TOPUP_PAGE,
    "ton": ADS_TOPUP_PAGE,
}

_TYPE_SEARCH_METHOD: dict[str, str] = {
    "stars": "searchStarsRecipient",
    "premium": "searchPremiumGiftRecipient",
    "gram": "searchAdsTopupRecipient",
    "ton": "searchAdsTopupRecipient",
}

_TYPE_INIT_METHOD: dict[str, str] = {
    "stars": "initBuyStarsRequest",
    "premium": "initGiftPremiumRequest",
    "gram": "initAdsTopupRequest",
    "ton": "initAdsTopupRequest",
}

_TYPE_LINK_METHOD: dict[str, str] = {
    "stars": "getBuyStarsLink",
    "premium": "getGiftPremiumLink",
    "gram": "getAdsTopupLink",
    "ton": "getAdsTopupLink",
}

_TYPE_CONFIRM_REFERER: dict[str, str] = {
    "stars": "stars/buy",
    "premium": "premium/gift",
    "gram": "ads/topup",
    "ton": "ads/topup",
}

_TYPE_EVM_PATH: dict[str, str] = {
    "stars": "/stars/buy",
    "premium": "/premium/gift",
}


def _normalize_payment_method(method: str) -> str:
    """Normalize payment method alias: gram -> ton."""
    if method == "gram":
        return "ton"
    return method


def _validate_single_item(item_type: str, username: str, amount: int | None, months: int | None) -> None:
    """Validate parameters for an individual purchase item."""
    if item_type not in PURCHASE_TYPES:
        raise ConfigurationError(
            f"Invalid purchase type '{item_type}'. Must be one of: {', '.join(sorted(PURCHASE_TYPES))}."
        )

    if not username or not str(username).strip():
        raise ConfigurationError("Recipient username is required.")

    if item_type == "premium":
        if months not in PREMIUM_MONTHS_VALID:
            raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    elif item_type == "stars":
        if not isinstance(amount, int) or not (STARS_PURCHASE_MIN <= amount <= STARS_PURCHASE_MAX):
            raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    elif item_type in ("gram", "ton"):
        if not isinstance(amount, int) or not (GRAM_TOPUP_MIN <= amount <= GRAM_TOPUP_MAX):
            raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)


async def _resolve_recipient(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    username: str,
    months: int | None = None,
) -> str:
    """Resolve Fragment recipient identifier via search API."""
    search_method = _TYPE_SEARCH_METHOD[item_type]
    payload: dict[str, Any] = {"method": search_method, "query": username}

    if item_type == "stars":
        payload["quantity"] = ""
    elif item_type == "premium":
        payload["months"] = months or 3

    if item_type in ("gram", "ton"):
        await post_fragment_api(
            session, fragment_hash, headers,
            {"method": "updateAdsTopupState", "mode": "new"},
        )

    result = await post_fragment_api(session, fragment_hash, headers, payload)
    recipient = (result.get("found") or {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))
    return recipient


async def _init_request(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    recipient: str,
    amount: int | None,
    months: int | None,
    payment_method: str,
) -> str:
    """Initialize request with Fragment and return req_id."""
    init_method = _TYPE_INIT_METHOD[item_type]
    api_payment = _normalize_payment_method(payment_method)

    payload: dict[str, Any] = {"method": init_method, "recipient": recipient}

    if item_type == "stars":
        payload["quantity"] = str(amount)
        payload["payment_method"] = api_payment
    elif item_type == "premium":
        await post_fragment_api(
            session, fragment_hash, headers,
            {
                "method": "updatePremiumState",
                "mode": "new",
                "lv": "false",
                "dh": str(int(time.time())),
            },
        )
        payload["months"] = str(months)
        payload["payment_method"] = api_payment
    elif item_type in ("gram", "ton"):
        payload["amount"] = amount

    result = await post_fragment_api(session, fragment_hash, headers, payload)
    if result.get("error"):
        error_msg = result["error"]
        if "minimum" in error_msg.lower():
            raise PaidMessageLimitError(
                PaidMessageLimitError.MINIMUM_REQUIRED.format(error=error_msg)
            )
        raise FragmentAPIError(error_msg)

    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            FragmentAPIError.NO_REQUEST_ID.format(context=f"{item_type} purchase")
        )
    return req_id


async def _get_transaction_link(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    req_id: str,
    account: dict[str, Any],
    show_sender: bool,
) -> dict[str, Any]:
    """Fetch raw transaction payload from Fragment."""
    link_method = _TYPE_LINK_METHOD[item_type]
    payload: dict[str, Any] = {
        "method": link_method,
        "account": json.dumps(account),
        "device": DEVICE_FINGERPRINT,
        "transaction": 1,
        "id": req_id,
        "show_sender": int(show_sender),
    }

    transaction = await post_fragment_api(session, fragment_hash, headers, payload)
    if transaction.get("need_verify"):
        raise VerificationError(VerificationError.KYC_REQUIRED)
    if transaction.get("error"):
        raise FragmentAPIError(str(transaction["error"]))

    return transaction


async def _execute_batch_flow(
    client: "FragmentClient",
    items: list[dict[str, Any]],
    payment_method: str,
) -> BatchResult:
    """Internal runner for multi-item batched purchases."""
    api_payment = _normalize_payment_method(payment_method)
    normalized_batch = {_normalize_payment_method(m) for m in BATCH_PAYMENT_METHODS}

    if api_payment not in normalized_batch:
        raise ConfigurationError(
            f"Batch purchases only support GRAM payment methods "
            f"({', '.join(sorted(BATCH_PAYMENT_METHODS))}). Got: '{payment_method}'."
        )

    if not items:
        return BatchResult(total=0, succeeded=0, failed=0, chunks_sent=0, items=[])

    client._require_wallet()

    for idx, raw_item in enumerate(items):
        t = raw_item.get("type", "")
        u = raw_item.get("username", "")
        a = raw_item.get("amount")
        m = raw_item.get("months")
        _validate_single_item(t, u, a, m)

    cookies = client._require_cookies()
    max_messages = WALLET_MAX_MESSAGES.get(client.wallet_version, 4)

    try:
        account = await build_account_info(client)
        wallet_info = await fetch_wallet_info(client)
    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc

    prepared: list[dict[str, Any]] = []

    try:
        page_urls_needed = {_TYPE_PAGE_MAP[item["type"]] for item in items}
        headers_cache = {url: build_headers(url) for url in page_urls_needed}

        fragment_hash = await fetch_fragment_hash(
            cookies,
            headers_cache.get(STARS_PAGE, build_headers(STARS_PAGE)),
            STARS_PAGE,
            client.timeout,
        )

        async with requests.AsyncSession(
            cookies=cookies, timeout=client.timeout, impersonate="chrome120",
        ) as session:
            for item_idx, item in enumerate(items):
                item_type = item["type"]
                username = str(item["username"]).strip()
                show_sender = item.get("show_sender", True)
                page_url = _TYPE_PAGE_MAP[item_type]
                headers = headers_cache[page_url]

                try:
                    recipient = await _resolve_recipient(
                        session, fragment_hash, headers, item_type, username, item.get("months"),
                    )
                    req_id = await _init_request(
                        session, fragment_hash, headers, item_type, recipient,
                        item.get("amount"), item.get("months"), payment_method,
                    )
                    transaction = await _get_transaction_link(
                        session, fragment_hash, headers, item_type, req_id, account, show_sender,
                    )

                    inner = transaction.get("transaction") or {}
                    messages = inner.get("messages") or []

                    if not messages:
                        prepared.append({
                            "item_idx": item_idx, "item": item, "ok": False,
                            "error": "Fragment returned empty transaction messages.",
                            "messages": [], "req_id": req_id,
                        })
                    else:
                        prepared.append({
                            "item_idx": item_idx, "item": item, "ok": True,
                            "error": None, "messages": messages, "req_id": req_id,
                        })

                except FragmentError as exc:
                    prepared.append({
                        "item_idx": item_idx, "item": item, "ok": False,
                        "error": str(exc), "messages": [], "req_id": None,
                    })
                except Exception as exc:
                    prepared.append({
                        "item_idx": item_idx, "item": item, "ok": False,
                        "error": str(exc), "messages": [], "req_id": None,
                    })

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc

    all_messages: list[dict[str, Any]] = []
    message_to_prepared_idx: list[int] = []

    for prep_idx, entry in enumerate(prepared):
        if entry["ok"] and entry["messages"]:
            for msg in entry["messages"]:
                all_messages.append(msg)
                message_to_prepared_idx.append(prep_idx)

    total_nanograms = sum(int(msg.get("amount", 0)) for msg in all_messages)
    total_gram_needed = total_nanograms / 1_000_000_000

    required_with_gas = total_gram_needed + MIN_GRAM_BALANCE
    if wallet_info.gram_balance < required_with_gas:
        raise WalletError(
            WalletError.LOW_GRAM_BALANCE.format(
                balance=wallet_info.gram_balance,
                required=required_with_gas,
                gas=MIN_GRAM_BALANCE,
            )
        )

    chunks: list[list[int]] = []
    for chunk_start in range(0, len(all_messages), max_messages):
        chunk_end = min(chunk_start + max_messages, len(all_messages))
        chunks.append(list(range(chunk_start, chunk_end)))

    chunk_results: list[dict[str, Any]] = []
    for chunk_num, chunk_msg_indices in enumerate(chunks):
        chunk_messages = [all_messages[i] for i in chunk_msg_indices]
        transaction_data = {"transaction": {"messages": chunk_messages}}

        try:
            tx_result = await execute_batch_transaction(client, transaction_data)
            chunk_results.append({
                "chunk_num": chunk_num, "ok": True,
                "tx_result": tx_result, "msg_indices": chunk_msg_indices,
            })

            for global_msg_idx in chunk_msg_indices:
                prep_entry = prepared[message_to_prepared_idx[global_msg_idx]]
                req_id = prep_entry.get("req_id")
                if req_id and tx_result.boc:
                    referer = _TYPE_CONFIRM_REFERER.get(prep_entry["item"]["type"], "stars/buy")
                    try:
                        await client.confirm_request(req_id, tx_result.boc, referer=referer)
                    except Exception:
                        pass

        except Exception as exc:
            chunk_results.append({
                "chunk_num": chunk_num, "ok": False,
                "error": str(exc), "msg_indices": chunk_msg_indices,
            })

    successful_prep_indices: set[int] = set()
    for cr in chunk_results:
        for mi in cr["msg_indices"]:
            pi = message_to_prepared_idx[mi]
            if cr["ok"]:
                successful_prep_indices.add(pi)

    result_items: list[BatchItemResult] = []
    for final_idx, entry in enumerate(prepared):
        item = entry["item"]
        item_type = item["type"]
        username = str(item["username"]).strip()
        display_amount = item.get("months", 0) if item_type == "premium" else item.get("amount", 0)

        owning_chunk = -1
        for cr in chunk_results:
            for mi in cr["msg_indices"]:
                if message_to_prepared_idx[mi] == final_idx:
                    owning_chunk = cr["chunk_num"]
                    break
            if owning_chunk >= 0:
                break

        if not entry["ok"]:
            result_items.append(BatchItemResult(
                type=item_type, username=username, amount=display_amount,
                ok=False, error=entry["error"], chunk_index=max(owning_chunk, 0),
            ))
        elif final_idx in successful_prep_indices:
            tx_hash = ""
            for cr in chunk_results:
                if cr["ok"]:
                    for mi in cr["msg_indices"]:
                        if message_to_prepared_idx[mi] == final_idx:
                            tx_hash = cr["tx_result"].tx_hash
                            break
                if tx_hash:
                    break
            result_items.append(BatchItemResult(
                type=item_type, username=username, amount=display_amount, ok=True,
                result={
                    "transaction_id": tx_hash, "type": item_type,
                    "username": username, "amount": display_amount,
                    "payment_method": payment_method,
                },
                chunk_index=max(owning_chunk, 0),
            ))
        else:
            chunk_error = ""
            for cr in chunk_results:
                if not cr["ok"]:
                    for mi in cr["msg_indices"]:
                        if message_to_prepared_idx[mi] == final_idx:
                            chunk_error = cr.get("error", "")
                            break
                if chunk_error:
                    break
            result_items.append(BatchItemResult(
                type=item_type, username=username, amount=display_amount,
                ok=False, error=chunk_error or "Transaction chunk failed.",
                chunk_index=max(owning_chunk, 0),
            ))

    succeeded_count = sum(1 for ri in result_items if ri.ok)
    chunks_sent_ok = sum(1 for cr in chunk_results if cr["ok"])

    logger.info(
        "Batch purchase complete: %d/%d succeeded, %d chunks sent",
        succeeded_count, len(items), chunks_sent_ok,
    )

    return BatchResult(
        total=len(items),
        succeeded=succeeded_count,
        failed=len(items) - succeeded_count,
        chunks_sent=chunks_sent_ok,
        items=result_items,
    )


async def _execute_single_flow(
    client: "FragmentClient",
    item_type: str,
    username: str,
    amount: int | None,
    months: int | None,
    show_sender: bool,
    payment_method: str,
) -> PurchaseResult | EvmPaymentResult:
    """Internal runner for a single purchase item."""
    _validate_single_item(item_type, username, amount, months)

    api_payment = _normalize_payment_method(payment_method)

    if api_payment not in {_normalize_payment_method(m) for m in VALID_PAYMENT_METHODS}:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(VALID_PAYMENT_METHODS)),
            )
        )

    if item_type in ("gram", "ton") and api_payment not in {"ton", "usdt_ton"}:
        raise ConfigurationError("Ads top-up only supports GRAM/TON payment methods.")

    is_evm = api_payment in {_normalize_payment_method(m) for m in EVM_PAYMENT_METHODS}
    is_gram = api_payment in {_normalize_payment_method(m) for m in GRAM_PAYMENT_METHODS}

    if is_gram:
        client._require_wallet()

    try:
        page_url = _TYPE_PAGE_MAP[item_type]
        headers = build_headers(page_url)

        async with requests.AsyncSession(
            cookies=client.cookies,
            timeout=client.timeout,
            impersonate="chrome120",
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies, headers, page_url, client.timeout,
            )

            recipient = await _resolve_recipient(
                session, fragment_hash, headers, item_type, username, months,
            )

            req_id = await _init_request(
                session, fragment_hash, headers, item_type, recipient,
                amount, months, payment_method,
            )

            if is_gram:
                account = await build_account_info(client)
                transaction = await _get_transaction_link(
                    session, fragment_hash, headers, item_type,
                    req_id, account, show_sender,
                )

                if transaction.get("evm"):
                    is_evm = True
                else:
                    tx_result = await execute_transaction(client, transaction)

                    if tx_result.boc and req_id:
                        try:
                            await client.confirm_request(
                                req_id, tx_result.boc,
                                referer=_TYPE_CONFIRM_REFERER[item_type],
                            )
                        except Exception:
                            pass

                    display_amount = months if item_type == "premium" else amount
                    return PurchaseResult(
                        transaction_id=tx_result.tx_hash,
                        type=item_type,
                        username=username,
                        amount=display_amount or 0,
                        payment_method=payment_method,
                    )

            if is_evm and item_type in _TYPE_EVM_PATH:
                evm_kwargs: dict[str, Any] = {"recipient": recipient, "payment_method": api_payment}
                if item_type == "stars":
                    evm_kwargs["quantity"] = amount
                elif item_type == "premium":
                    evm_kwargs["months"] = months

                invoice = await fetch_evm_invoice(
                    cookies=client.cookies,
                    page_path=_TYPE_EVM_PATH[item_type],
                    timeout=client.timeout,
                    **evm_kwargs,
                )
                return EvmPaymentResult(
                    item_kind=item_type,
                    target=username,
                    amount=months if item_type == "premium" else (amount or 0),
                    payment_method=payment_method,
                    invoice=invoice,
                )

            if is_evm:
                raise ConfigurationError(
                    ConfigurationError.UNSUPPORTED_METHOD.format(item_type=item_type)
                )

            raise FragmentAPIError(f"Unsupported payment flow for {item_type}/{payment_method}")


    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def purchase(
    client: "FragmentClient",
    items_or_type: list[dict[str, Any] | PurchaseItem] | dict[str, Any] | PurchaseItem | str,
    username: str | None = None,
    amount: int | None = None,
    months: int | None = None,
    show_sender: bool = True,
    payment_method: str = "gram",
) -> PurchaseResult | BatchResult | EvmPaymentResult:
    """Execute a single purchase or batch purchase on Fragment.

    Supports two invocation formats:

    1. Batch format (list of dicts or PurchaseItems):
       await client.purchase([
           {"type": "stars", "username": "user1", "amount": 100},
           {"type": "premium", "username": "user2", "months": 3},
       ], payment_method="gram") -> Returns BatchResult

    2. Single item format:
       await client.purchase("stars", username="user1", amount=100) -> Returns PurchaseResult | EvmPaymentResult
       await client.purchase({"type": "stars", "username": "user1", "amount": 100})

    Args:
        client: Authenticated FragmentClient instance.
        items_or_type: List of purchase dicts/items, a single dict/item, or item_type string.
        username: Telegram username (when items_or_type is a type string).
        amount: Stars count or Ads GRAM amount.
        months: Premium duration in months (3, 6, 12).
        show_sender: Whether to show sender name in notification.
        payment_method: "gram", "ton", "usdt_gram", "usdt_ton", or EVM payment method string.

    Returns:
        BatchResult for list inputs, PurchaseResult / EvmPaymentResult for single inputs.
    """
    if isinstance(items_or_type, list):
        parsed_items: list[dict[str, Any]] = []
        for raw in items_or_type:
            if isinstance(raw, PurchaseItem):
                parsed_items.append({
                    "type": raw.type,
                    "username": raw.username,
                    "amount": raw.amount,
                    "months": raw.months,
                    "show_sender": raw.show_sender,
                })
            elif isinstance(raw, dict):
                parsed_items.append(dict(raw))
            else:
                raise ConfigurationError(f"Invalid batch item format: {type(raw)}")
        return await _execute_batch_flow(client, parsed_items, payment_method)

    if isinstance(items_or_type, PurchaseItem):
        return await _execute_single_flow(
            client=client,
            item_type=items_or_type.type,
            username=items_or_type.username,
            amount=items_or_type.amount,
            months=items_or_type.months,
            show_sender=items_or_type.show_sender,
            payment_method=payment_method,
        )

    if isinstance(items_or_type, dict):
        return await _execute_single_flow(
            client=client,
            item_type=items_or_type.get("type", ""),
            username=items_or_type.get("username", ""),
            amount=items_or_type.get("amount"),
            months=items_or_type.get("months"),
            show_sender=items_or_type.get("show_sender", True),
            payment_method=payment_method,
        )

    if isinstance(items_or_type, str):
        if not username:
            raise ConfigurationError("Username is required for single purchase invocation.")
        return await _execute_single_flow(
            client=client,
            item_type=items_or_type,
            username=username,
            amount=amount,
            months=months,
            show_sender=show_sender,
            payment_method=payment_method,
        )

    raise ConfigurationError(f"Unsupported items argument type: {type(items_or_type)}")


async def batch_purchase(
    client: "FragmentClient",
    items: list[dict[str, Any] | PurchaseItem],
    payment_method: str = "gram",
) -> BatchResult:
    """Execute multiple purchases as batched on-chain TON transactions.

    Convenience wrapper around purchase() when passing a list of items.
    """
    result = await purchase(client, items_or_type=items, payment_method=payment_method)
    if isinstance(result, BatchResult):
        return result
    return BatchResult(total=1, succeeded=1, failed=0, chunks_sent=1, items=[])


async def purchase_stars(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: str = "gram",
) -> PurchaseResult | EvmPaymentResult:
    """Send Telegram Stars to a user. Convenience wrapper around purchase()."""
    result = await purchase(
        client, "stars", username=username,
        amount=amount, show_sender=show_sender, payment_method=payment_method,
    )
    return result


async def purchase_premium(
    client: "FragmentClient",
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: str = "gram",
) -> PurchaseResult | EvmPaymentResult:
    """Gift Telegram Premium to a user. Convenience wrapper around purchase()."""
    result = await purchase(
        client, "premium", username=username,
        months=months, show_sender=show_sender, payment_method=payment_method,
    )
    return result


async def topup_gram(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> PurchaseResult:
    """Top up GRAM to a recipient's Telegram Ads balance. Convenience wrapper around purchase()."""
    result = await purchase(
        client, "gram", username=username,
        amount=amount, show_sender=show_sender, payment_method="gram",
    )
    return result


async def topup_ton(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> PurchaseResult:
    """Top up GRAM (ex TON) to Telegram Ads balance. Backward-compatible alias for topup_gram()."""
    return await topup_gram(client, username, amount, show_sender)