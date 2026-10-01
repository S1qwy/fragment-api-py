"""EVM invoice extraction through an existing Fragment session."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

from curl_cffi import requests

from FragmentAPI.exceptions import FragmentAPIError
from FragmentAPI.types.constants import (
    DEFAULT_TIMEOUT,
    EVM_CHAIN_IDS,
    EVM_CHAIN_NAMES,
    FRAGMENT_BASE_URL,
)
from FragmentAPI.types.models import EvmInvoice
from FragmentAPI.utils.auth import embedded_object
from FragmentAPI.utils.http import FragmentTransport
from FragmentAPI.utils.proxy import build_curl_proxy_args
from FragmentAPI.utils.validation import normalize_payment_method


def _build_invoice_url(
    page_path: str,
    recipient: str,
    quantity: int | None = None,
    months: int | None = None,
    amount: int | None = None,
    winners: int | None = None,
) -> str:
    """Build an encoded Fragment invoice URL."""
    values: dict[str, Any] = {
        "recipient": recipient,
        "quantity": quantity,
        "months": months,
        "amount": amount,
        "winners": winners,
    }
    query = urlencode({key: value for key, value in values.items() if value is not None})
    return f"{FRAGMENT_BASE_URL}/{page_path.lstrip('/')}?{query}"


async def _fetch(
    session: requests.AsyncSession,
    invoice_url: str,
    payment_method: str,
) -> EvmInvoice:
    """Read an EVM invoice without adding native-TON messages."""
    text = await FragmentTransport(session).get_text(invoice_url)
    initial = embedded_object(text, "ajInit(")
    state = initial.get("state", {})
    required = ("invoiceReqId", "invoiceAddress", "invoiceToken", "invoiceChainId", "invoiceAmount")
    if not isinstance(state, dict) or any(state.get(key) is None for key in required):
        raise FragmentAPIError("Fragment did not return complete EVM invoice data.")
    method = normalize_payment_method(payment_method)
    symbol, chain = method.split("_", 1)
    chain_id = int(state["invoiceChainId"])
    if EVM_CHAIN_IDS.get(chain) != chain_id:
        raise FragmentAPIError("Invoice network differs from the selected payment method.")
    raw_hex = str(state["invoiceAmount"])
    raw_amount = int(raw_hex, 16)
    decimals = int(state.get("invoiceTokenDecimals", 6))
    if raw_amount < 0 or not 0 <= decimals <= 36:
        raise FragmentAPIError("Invalid EVM invoice amount or precision.")
    match = re.search(r"hash=([a-fA-F0-9]+)", str(initial.get("apiUrl", "")))
    return EvmInvoice(
        req_id=str(state["invoiceReqId"]),
        invoice_address=str(state["invoiceAddress"]),
        invoice_token=str(state["invoiceToken"]),
        invoice_chain_id=chain_id,
        invoice_chain_name=EVM_CHAIN_NAMES.get(chain_id, str(chain_id)),
        invoice_amount_hex=raw_hex,
        invoice_amount_raw=raw_amount,
        invoice_amount=float(Decimal(raw_amount) / (10 ** decimals)),
        token_symbol=symbol.upper(),
        token_decimals=decimals,
        expires_at=int(state.get("invoiceExpiresAt", 0)),
        payment_method=method,
        api_hash=match.group(1) if match else "",
        page_url=invoice_url,
    )


async def fetch_evm_invoice(
    cookies: dict[str, Any],
    page_path: str,
    recipient: str,
    payment_method: str,
    quantity: int | None = None,
    months: int | None = None,
    amount: int | None = None,
    winners: int | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    *,
    session: requests.AsyncSession | None = None,
    proxy: str | None = None,
) -> EvmInvoice:
    """Return an unsigned EVM invoice using the caller's session when provided."""
    url = _build_invoice_url(page_path, recipient, quantity, months, amount, winners)
    if session is not None:
        return await _fetch(session, url, payment_method)
    async with requests.AsyncSession(
        cookies=cookies, timeout=timeout, impersonate="chrome",
        **build_curl_proxy_args(proxy),
    ) as owned:
        return await _fetch(owned, url, payment_method)