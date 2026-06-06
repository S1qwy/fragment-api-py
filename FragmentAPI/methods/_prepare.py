from __future__ import annotations

import json
from typing import (
    Any,
    TYPE_CHECKING,
)

import httpx

from FragmentAPI.exceptions import FragmentAPIError
from FragmentAPI.types.constants import DEVICE_FINGERPRINT
from FragmentAPI.types.results import (
    PreparedTransaction,
    PreparedTransactionMessage,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)
from FragmentAPI.utils.rest_api import (
    extract_prepared_data,
    rest_api_post,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


def _build_account(sender_wallet_address: str) -> dict[str, Any]:
    '''Build a minimal account payload for Fragment getXxxLink calls.'''
    return {
        "address": sender_wallet_address,
        "chain": "-239",
        "walletStateInit": "",
        "publicKey": "",
    }


async def fetch_unsigned_transaction(
    client: "FragmentClient",
    page_url: str,
    link_method: str,
    link_payload_extra: dict[str, Any],
    sender_wallet_address: str,
) -> dict[str, Any]:
    '''Call a Fragment getXxxLink method with a custom sender address.'''
    cookies = client._require_cookies()
    headers = build_headers(page_url)
    account = _build_account(sender_wallet_address)

    async with httpx.AsyncClient(
        cookies=cookies,
        timeout=client.timeout,
    ) as session:
        fragment_hash = await fetch_fragment_hash(
            cookies,
            headers,
            page_url,
            client.timeout,
        )

        link_payload = {
            "method": link_method,
            "account": json.dumps(account),
            "device": DEVICE_FINGERPRINT,
            "transaction": 1,
            **link_payload_extra,
        }
        transaction = await post_FragmentAPI(
            session,
            fragment_hash,
            headers,
            link_payload,
        )

    return transaction


def transaction_to_prepared(
    raw: dict[str, Any],
    req_id: str,
    item_kind: str,
    target: str,
    amount: int,
    sender_address: str,
    confirm_referer: str,
) -> PreparedTransaction:
    '''Convert raw Fragment transaction payload to a PreparedTransaction.'''
    inner = raw.get("transaction") or {}
    
    valid_until = inner.get("valid_until") or inner.get("validUntil") or 0
    valid_until = int(valid_until)
    
    raw_messages = inner.get("messages") or []

    messages: list[PreparedTransactionMessage] = []
    for msg in raw_messages:
        messages.append(
            PreparedTransactionMessage(
                address=str(msg.get("address", "")),
                amount=str(msg.get("amount", "0")),
                payload=msg.get("payload"),
                state_init=msg.get("stateInit") or msg.get("state_init"),
            )
        )

    return PreparedTransaction(
        req_id=req_id,
        item_kind=item_kind,
        target=target,
        amount=amount,
        valid_until=valid_until,
        messages=messages,
        raw=raw,
        sender_address=sender_address,
        confirm_referer=confirm_referer,
    )


def rest_data_to_prepared(
    rest_data: dict[str, Any],
    item_kind: str,
    target: str,
    amount: int,
    sender_address: str,
) -> PreparedTransaction:
    '''Convert fragment-api.tech prepared payload to PreparedTransaction.'''
    inner = rest_data.get("transaction") or {}
    
    # Ищем сообщения и valid_until внутри объекта transaction, а также снаружи для совместимости
    raw_messages = inner.get("messages") or rest_data.get("messages") or []
    valid_until = inner.get("valid_until") or inner.get("validUntil") or rest_data.get("valid_until") or rest_data.get("validUntil") or 0
    valid_until = int(valid_until)

    messages: list[PreparedTransactionMessage] = []
    for msg in raw_messages:
        messages.append(
            PreparedTransactionMessage(
                address=str(msg.get("address", "")),
                amount=str(msg.get("amount", "0")),
                payload=msg.get("payload"),
                state_init=msg.get("state_init") or msg.get("stateInit"),
            )
        )

    req_id = rest_data.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            "fragment-api.tech prepared response missing req_id."
        )

    confirm_referer = rest_data.get("confirm_referer") or ""

    return PreparedTransaction(
        req_id=str(req_id),
        item_kind=item_kind,
        target=target,
        amount=amount,
        valid_until=valid_until,
        messages=messages,
        raw=rest_data,
        sender_address=sender_address,
        confirm_referer=confirm_referer,
    )


async def prepare_via_rest_api(
    *,
    endpoint: str,
    payload: dict[str, Any],
    item_kind: str,
    target: str,
    amount: int,
    sender_wallet_address: str,
    timeout: float,
) -> PreparedTransaction:
    '''Request an unsigned transaction from fragment-api.tech.'''
    body = {
        **payload,
        "sender_address": sender_wallet_address,
    }
    response = await rest_api_post(endpoint, body, timeout=timeout)
    data = extract_prepared_data(response)
    return rest_data_to_prepared(
        rest_data=data,
        item_kind=item_kind,
        target=target,
        amount=amount,
        sender_address=sender_wallet_address,
    )


def prepared_to_transaction_data(prepared: PreparedTransaction) -> dict[str, Any]:
    '''Convert PreparedTransaction back to a transaction dict for wallet execution.'''
    messages = []
    for msg in prepared.messages:
        m: dict[str, Any] = {
            "address": msg.address,
            "amount": msg.amount,
        }
        if msg.payload:
            m["payload"] = msg.payload
        if msg.state_init:
            m["stateInit"] = msg.state_init
        messages.append(m)

    return {
        "transaction": {
            "valid_until": prepared.valid_until,
            "messages": messages,
        },
    }