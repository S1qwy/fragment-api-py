'''
Batch purchase method — sends multiple Stars / Premium / Ads top-up
purchases as bundled TON transactions with inline messages.

TON wallets support multiple outgoing messages per transaction:
  - V4R2: up to 4 messages
  - V5R1: up to 255 messages

Each Fragment purchase typically produces 1 outgoing message.
This module collects all transaction payloads from Fragment,
groups their messages into chunks that fit the wallet limit,
and broadcasts each chunk as a single on-chain transaction.

After each chunk is confirmed the associated req_ids are sent
back to Fragment via confirmReq so the purchases are finalized.

Only TON-native payment methods ("ton", "usdt_ton") are supported
because EVM payments cannot be batched on the TON chain.
'''

from __future__ import annotations

import json
from typing import (
    Any,
    TYPE_CHECKING,
)

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    ADS_TOPUP_PAGE,
    BATCH_PAYMENT_METHODS,
    DEVICE_FINGERPRINT,
    PREMIUM_GIFT_PAGE,
    STARS_PAGE,
    WALLET_MAX_MESSAGES,
)
from FragmentAPI.types.results import (
    BatchItemResult,
    BatchResult,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_batch_transaction,
    fetch_wallet_info,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


_TYPE_PAGE_MAP: dict[str, str] = {
    "stars": STARS_PAGE,
    "premium": PREMIUM_GIFT_PAGE,
    "ton": ADS_TOPUP_PAGE,
}

_TYPE_SEARCH_METHOD: dict[str, str] = {
    "stars": "searchStarsRecipient",
    "premium": "searchPremiumGiftRecipient",
    "ton": "searchAdsTopupRecipient",
}

_TYPE_INIT_METHOD: dict[str, str] = {
    "stars": "initBuyStarsRequest",
    "premium": "initGiftPremiumRequest",
    "ton": "initAdsTopupRequest",
}

_TYPE_LINK_METHOD: dict[str, str] = {
    "stars": "getBuyStarsLink",
    "premium": "getGiftPremiumLink",
    "ton": "getAdsTopupLink",
}

_TYPE_CONFIRM_REFERER: dict[str, str] = {
    "stars": "stars/buy",
    "premium": "premium/gift",
    "ton": "ads/topup",
}


def _validate_item(item: dict[str, Any], index: int) -> None:
    '''Validate a single batch item dict and raise ConfigError on problems.'''
    item_type = item.get("type")
    if item_type not in ("stars", "premium", "ton"):
        raise ConfigError(
            f"Batch item #{index}: invalid type '{item_type}'. "
            f"Must be 'stars', 'premium', or 'ton'."
        )

    username = item.get("username")
    if not username or not str(username).strip():
        raise ConfigError(
            f"Batch item #{index}: 'username' is required."
        )

    if item_type == "premium":
        months = item.get("months")
        if months not in (3, 6, 12):
            raise ConfigError(
                f"Batch item #{index}: invalid months={months}. "
                f"Must be 3, 6, or 12."
            )
    else:
        amount = item.get("amount")
        if not isinstance(amount, int) or amount < 1:
            raise ConfigError(
                f"Batch item #{index}: invalid amount={amount}. "
                f"Must be a positive integer."
            )
        if item_type == "stars" and not (50 <= amount <= 10_000_000):
            raise ConfigError(
                f"Batch item #{index}: stars amount must be 50..10 000 000."
            )
        if item_type == "ton" and not (1 <= amount <= 1_000_000_000):
            raise ConfigError(
                f"Batch item #{index}: TON amount must be 1..1 000 000 000."
            )


async def _resolve_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    username: str,
    item: dict[str, Any],
) -> str:
    '''
    Resolve a Fragment recipient ID for a given purchase type.

    Calls the appropriate searchXxxRecipient method and returns
    the opaque recipient string that Fragment uses internally.
    '''
    search_method = _TYPE_SEARCH_METHOD[item_type]

    payload: dict[str, Any] = {
        "method": search_method,
        "query": username,
    }
    if item_type == "stars":
        payload["quantity"] = ""
    elif item_type == "premium":
        payload["months"] = item.get("months", 3)

    if item_type == "ton":
        await post_FragmentAPI(
            session,
            fragment_hash,
            headers,
            {
                "method": "updateAdsTopupState",
                "mode": "new",
            },
        )

    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        payload,
    )

    recipient = (result.get("found") or {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            UserNotFoundError.NOT_FOUND.format(username=username),
        )
    return recipient


async def _init_request(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    recipient: str,
    item: dict[str, Any],
    payment_method: str,
) -> str:
    '''
    Call the appropriate initXxxRequest method on Fragment
    and return the req_id needed for the transaction link.
    '''
    init_method = _TYPE_INIT_METHOD[item_type]

    payload: dict[str, Any] = {
        "method": init_method,
        "recipient": recipient,
    }

    if item_type == "stars":
        payload["quantity"] = str(item["amount"])
        payload["payment_method"] = payment_method
    elif item_type == "premium":
        payload["months"] = str(item["months"])
        payload["payment_method"] = payment_method
    elif item_type == "ton":
        payload["amount"] = item["amount"]

    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        payload,
    )

    if result.get("error"):
        raise FragmentAPIError(result["error"])

    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            FragmentAPIError.NO_REQUEST_ID.format(
                context=f"batch {item_type}",
            )
        )
    return req_id


async def _fetch_transaction_link(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    req_id: str,
    account: dict[str, Any],
    show_sender: bool,
) -> dict[str, Any]:
    '''
    Call the appropriate getXxxLink method on Fragment
    and return the raw transaction dict containing messages.
    '''
    link_method = _TYPE_LINK_METHOD[item_type]

    payload: dict[str, Any] = {
        "method": link_method,
        "account": json.dumps(account),
        "device": DEVICE_FINGERPRINT,
        "transaction": 1,
        "id": req_id,
    }
    if item_type in ("stars", "premium", "ton"):
        payload["show_sender"] = int(show_sender)

    transaction = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        payload,
    )

    if transaction.get("need_verify"):
        raise VerificationError(VerificationError.KYC_REQUIRED)

    if transaction.get("error"):
        raise FragmentAPIError(str(transaction["error"]))

    return transaction


def _extract_messages(
    transaction: dict[str, Any],
) -> list[dict[str, Any]]:
    '''
    Extract the list of outgoing messages from a Fragment
    transaction payload dict. Returns an empty list if the
    payload has no messages section.
    '''
    inner = transaction.get("transaction") or {}
    return inner.get("messages") or []


async def batch_purchase(
    client: "FragmentClient",
    items: list[dict[str, Any]],
    payment_method: str = "ton",
) -> BatchResult:
    '''
    Execute multiple Stars / Premium / Ads top-up purchases
    as batched TON transactions with inline messages.

    Each item dict must contain:
      - type: "stars" | "premium" | "ton"
      - username: str
      - amount: int           (for type "stars" or "ton")
      - months: int           (for type "premium", one of 3/6/12)
      - show_sender: bool     (optional, default True)

    The method groups all outgoing messages into chunks
    that fit the wallet version message limit (4 for V4R2,
    255 for V5R1). Each chunk is broadcast as a single
    on-chain transaction and confirmed once by seqno+balance.

    Only "ton" and "usdt_ton" payment methods are supported.
    EVM payments cannot be batched.

    Args:
        client: FragmentClient instance with cookies and seed.
        items: List of purchase item dicts.
        payment_method: "ton" or "usdt_ton".

    Returns:
        BatchResult with per-item outcomes and chunk statistics.
    '''
    if payment_method not in BATCH_PAYMENT_METHODS:
        raise ConfigError(
            f"Batch purchases only support TON payment methods "
            f"({', '.join(sorted(BATCH_PAYMENT_METHODS))}). "
            f"Got: '{payment_method}'."
        )

    if not items:
        return BatchResult(
            total=0,
            succeeded=0,
            failed=0,
            chunks_sent=0,
            items=[],
        )

    item_index = 0
    for raw_item in items:
        _validate_item(raw_item, item_index)
        item_index += 1

    cookies = client._require_cookies()
    max_messages = WALLET_MAX_MESSAGES.get(client.wallet_version, 4)

    try:
        account = await build_account_info(client)
        wallet_info = await fetch_wallet_info(client)
    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc

    prepared: list[dict[str, Any]] = []

    try:
        page_urls_needed: set[str] = set()
        idx = 0
        while idx < len(items):
            page_urls_needed.add(
                _TYPE_PAGE_MAP[items[idx]["type"]]
            )
            idx += 1

        headers_cache: dict[str, dict[str, str]] = {}
        for page_url in page_urls_needed:
            headers_cache[page_url] = build_headers(page_url)

        fragment_hash = await fetch_fragment_hash(
            cookies,
            headers_cache.get(STARS_PAGE, build_headers(STARS_PAGE)),
            STARS_PAGE,
            client.timeout,
        )

        async with httpx.AsyncClient(
            cookies=cookies,
            timeout=client.timeout,
        ) as session:
            item_idx = 0
            while item_idx < len(items):
                item = items[item_idx]
                item_type = item["type"]
                username = str(item["username"]).strip()
                show_sender = item.get("show_sender", True)

                page_url = _TYPE_PAGE_MAP[item_type]
                headers = headers_cache[page_url]

                try:
                    recipient = await _resolve_recipient(
                        session,
                        fragment_hash,
                        headers,
                        item_type,
                        username,
                        item,
                    )

                    req_id = await _init_request(
                        session,
                        fragment_hash,
                        headers,
                        item_type,
                        recipient,
                        item,
                        payment_method,
                    )

                    transaction = await _fetch_transaction_link(
                        session,
                        fragment_hash,
                        headers,
                        item_type,
                        req_id,
                        account,
                        show_sender,
                    )

                    messages = _extract_messages(transaction)
                    if not messages:
                        prepared.append({
                            "item_idx": item_idx,
                            "item": item,
                            "ok": False,
                            "error": "Fragment returned empty transaction messages.",
                            "messages": [],
                            "req_id": req_id,
                        })
                    else:
                        prepared.append({
                            "item_idx": item_idx,
                            "item": item,
                            "ok": True,
                            "error": None,
                            "messages": messages,
                            "req_id": req_id,
                        })

                except FragmentBaseError as exc:
                    prepared.append({
                        "item_idx": item_idx,
                        "item": item,
                        "ok": False,
                        "error": str(exc),
                        "messages": [],
                        "req_id": None,
                    })
                except Exception as exc:
                    prepared.append({
                        "item_idx": item_idx,
                        "item": item,
                        "ok": False,
                        "error": str(exc),
                        "messages": [],
                        "req_id": None,
                    })

                item_idx += 1

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc

    all_messages: list[dict[str, Any]] = []
    message_to_prepared_idx: list[int] = []

    prep_idx = 0
    while prep_idx < len(prepared):
        entry = prepared[prep_idx]
        if entry["ok"] and entry["messages"]:
            msg_idx = 0
            while msg_idx < len(entry["messages"]):
                all_messages.append(entry["messages"][msg_idx])
                message_to_prepared_idx.append(prep_idx)
                msg_idx += 1
        prep_idx += 1

    total_ton_needed = 0
    msg_scan_idx = 0
    while msg_scan_idx < len(all_messages):
        total_ton_needed += int(all_messages[msg_scan_idx].get("amount", 0))
        msg_scan_idx += 1
    total_ton_needed_float = total_ton_needed / 1_000_000_000

    from FragmentAPI.exceptions import WalletError
    from FragmentAPI.types.constants import MIN_TON_BALANCE

    required_with_gas = total_ton_needed_float + MIN_TON_BALANCE
    if wallet_info.balance_ton < required_with_gas:
        raise WalletError(
            WalletError.LOW_BALANCE.format(
                balance=wallet_info.balance_ton,
                required=required_with_gas,
                gas=MIN_TON_BALANCE,
                currency="TON",
            )
        )

    chunks: list[list[int]] = []
    chunk_start = 0
    while chunk_start < len(all_messages):
        chunk_end = min(chunk_start + max_messages, len(all_messages))
        chunk_indices = []
        ci = chunk_start
        while ci < chunk_end:
            chunk_indices.append(ci)
            ci += 1
        chunks.append(chunk_indices)
        chunk_start = chunk_end

    chunk_results: list[dict[str, Any]] = []
    chunk_num = 0
    while chunk_num < len(chunks):
        chunk_msg_indices = chunks[chunk_num]

        chunk_messages: list[dict[str, Any]] = []
        ci2 = 0
        while ci2 < len(chunk_msg_indices):
            chunk_messages.append(all_messages[chunk_msg_indices[ci2]])
            ci2 += 1

        transaction_data: dict[str, Any] = {
            "transaction": {
                "messages": chunk_messages,
            },
        }

        try:
            tx_result = await execute_batch_transaction(
                client,
                transaction_data,
            )
            chunk_results.append({
                "chunk_num": chunk_num,
                "ok": True,
                "tx_result": tx_result,
                "msg_indices": chunk_msg_indices,
            })

            confirm_idx = 0
            while confirm_idx < len(chunk_msg_indices):
                global_msg_idx = chunk_msg_indices[confirm_idx]
                prep_entry_idx = message_to_prepared_idx[global_msg_idx]
                prep_entry = prepared[prep_entry_idx]
                req_id = prep_entry.get("req_id")
                if req_id and tx_result.boc:
                    referer = _TYPE_CONFIRM_REFERER.get(
                        prep_entry["item"]["type"],
                        "stars/buy",
                    )
                    try:
                        await client.confirm_request(
                            req_id,
                            tx_result.boc,
                            referer=referer,
                        )
                    except Exception:
                        pass
                confirm_idx += 1

        except Exception as exc:
            chunk_results.append({
                "chunk_num": chunk_num,
                "ok": False,
                "error": str(exc),
                "msg_indices": chunk_msg_indices,
            })

        chunk_num += 1

    successful_prep_indices: set[int] = set()
    failed_prep_indices: set[int] = set()

    cr_idx = 0
    while cr_idx < len(chunk_results):
        cr = chunk_results[cr_idx]
        mi_idx = 0
        while mi_idx < len(cr["msg_indices"]):
            global_mi = cr["msg_indices"][mi_idx]
            pi = message_to_prepared_idx[global_mi]
            if cr["ok"]:
                successful_prep_indices.add(pi)
            else:
                failed_prep_indices.add(pi)
            mi_idx += 1
        cr_idx += 1

    result_items: list[BatchItemResult] = []
    final_idx = 0
    while final_idx < len(prepared):
        entry = prepared[final_idx]
        item = entry["item"]
        item_type = item["type"]
        username = str(item["username"]).strip()

        if item_type == "premium":
            display_amount = item.get("months", 0)
        else:
            display_amount = item.get("amount", 0)

        owning_chunk = -1
        scan_cr = 0
        while scan_cr < len(chunk_results):
            scan_mi = 0
            while scan_mi < len(chunk_results[scan_cr]["msg_indices"]):
                if message_to_prepared_idx[
                    chunk_results[scan_cr]["msg_indices"][scan_mi]
                ] == final_idx:
                    owning_chunk = chunk_results[scan_cr]["chunk_num"]
                    break
                scan_mi += 1
            if owning_chunk >= 0:
                break
            scan_cr += 1

        if not entry["ok"]:
            result_items.append(
                BatchItemResult(
                    type=item_type,
                    username=username,
                    amount=display_amount,
                    ok=False,
                    error=entry["error"],
                    chunk_index=max(owning_chunk, 0),
                )
            )
        elif final_idx in successful_prep_indices:
            tx_hash = ""
            scan_cr2 = 0
            while scan_cr2 < len(chunk_results):
                if chunk_results[scan_cr2]["ok"]:
                    scan_mi2 = 0
                    while scan_mi2 < len(chunk_results[scan_cr2]["msg_indices"]):
                        if message_to_prepared_idx[
                            chunk_results[scan_cr2]["msg_indices"][scan_mi2]
                        ] == final_idx:
                            tx_hash = chunk_results[scan_cr2]["tx_result"].tx_hash
                            break
                        scan_mi2 += 1
                if tx_hash:
                    break
                scan_cr2 += 1

            result_items.append(
                BatchItemResult(
                    type=item_type,
                    username=username,
                    amount=display_amount,
                    ok=True,
                    result={
                        "transaction_id": tx_hash,
                        "type": item_type,
                        "username": username,
                        "amount": display_amount,
                        "payment_method": payment_method,
                    },
                    chunk_index=max(owning_chunk, 0),
                )
            )
        else:
            chunk_error = ""
            scan_cr3 = 0
            while scan_cr3 < len(chunk_results):
                if not chunk_results[scan_cr3]["ok"]:
                    scan_mi3 = 0
                    while scan_mi3 < len(chunk_results[scan_cr3]["msg_indices"]):
                        if message_to_prepared_idx[
                            chunk_results[scan_cr3]["msg_indices"][scan_mi3]
                        ] == final_idx:
                            chunk_error = chunk_results[scan_cr3].get("error", "")
                            break
                        scan_mi3 += 1
                if chunk_error:
                    break
                scan_cr3 += 1

            result_items.append(
                BatchItemResult(
                    type=item_type,
                    username=username,
                    amount=display_amount,
                    ok=False,
                    error=chunk_error or "Transaction chunk failed.",
                    chunk_index=max(owning_chunk, 0),
                )
            )

        final_idx += 1

    succeeded_count = 0
    ri_idx = 0
    while ri_idx < len(result_items):
        if result_items[ri_idx].ok:
            succeeded_count += 1
        ri_idx += 1

    chunks_sent_ok = 0
    cs_idx = 0
    while cs_idx < len(chunk_results):
        if chunk_results[cs_idx]["ok"]:
            chunks_sent_ok += 1
        cs_idx += 1

    return BatchResult(
        total=len(items),
        succeeded=succeeded_count,
        failed=len(items) - succeeded_count,
        chunks_sent=chunks_sent_ok,
        items=result_items,
    )