'''
EVM payment invoice parser for Fragment.

Extracts invoice parameters from the /stars/buy, /premium/gift, etc.
pages when an EVM payment method is selected.
'''

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from FragmentAPI.exceptions import (
    FragmentAPIError,
    FragmentPageError,
    ParseError,
)
from FragmentAPI.types.constants import (
    DEFAULT_TIMEOUT,
    EVM_CHAIN_NAMES,
    EVM_TOKEN_DECIMALS,
    EVM_TOKEN_SYMBOLS,
    FRAGMENT_BASE_URL,
)
from FragmentAPI.types.results import EvmInvoice
from FragmentAPI.utils.http import build_headers

AJ_INIT_RE = re.compile(r"ajInit\((\{.*?\})\);", re.DOTALL)


def _parse_aj_init(html: str) -> dict[str, Any]:
    '''Extract the ajInit JSON payload from a Fragment page.'''
    match = AJ_INIT_RE.search(html)
    if not match:
        raise ParseError(
            ParseError.UNPARSEABLE.format(
                context="evm invoice page",
                exc="ajInit block not found",
            )
        )
    try:
        return json.loads(match.group(1))
    except Exception as exc:
        raise ParseError(
            ParseError.UNPARSEABLE.format(
                context="evm invoice ajInit JSON",
                exc=exc,
            )
        ) from exc


def _hex_to_int(hex_str: str) -> int:
    '''Convert a 0x-prefixed hex string to int.'''
    s = hex_str.strip()
    if s.lower().startswith("0x"):
        s = s[2:]
    return int(s, 16) if s else 0


def _build_invoice_url(
    page_path: str,
    recipient: str,
    quantity: int | None = None,
    months: int | None = None,
    amount: int | None = None,
    winners: int | None = None,
) -> str:
    '''Build the Fragment invoice page URL with query parameters.'''
    params: list[str] = [f"recipient={recipient}"]
    if quantity is not None:
        params.append(f"quantity={quantity}")
    if months is not None:
        params.append(f"months={months}")
    if amount is not None:
        params.append(f"amount={amount}")
    if winners is not None:
        params.append(f"winners={winners}")
    query = "&".join(params)
    return f"{FRAGMENT_BASE_URL}{page_path}?{query}"


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
) -> EvmInvoice:
    '''
    Fetch a Fragment payment page and extract EVM invoice data.

    Fragment redirects to an invoice page after the initial
    getBuyStarsLink / getGiftPremiumLink / etc. call returns
    {"ok": true, "evm": true} for EVM payment methods.
    '''
    invoice_url = _build_invoice_url(
        page_path=page_path,
        recipient=recipient,
        quantity=quantity,
        months=months,
        amount=amount,
        winners=winners,
    )

    headers = build_headers(invoice_url)
    full_headers = {
        "accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "accept-language": "en-US,en;q=0.9",
        "user-agent": headers["user-agent"],
    }

    async with httpx.AsyncClient(
        cookies=cookies,
        timeout=timeout,
        follow_redirects=True,
    ) as session:
        response = await session.get(
            invoice_url,
            headers=full_headers,
        )

    if response.status_code != 200:
        raise FragmentPageError(
            FragmentPageError.BAD_STATUS.format(
                status=response.status_code,
                url=invoice_url,
            )
        )

    aj_data = _parse_aj_init(response.text)
    state = aj_data.get("state", {})

    api_url = aj_data.get("apiUrl", "")
    api_hash_match = re.search(r"hash=([a-f0-9]+)", api_url)
    api_hash = api_hash_match.group(1) if api_hash_match else ""

    req_id = state.get("invoiceReqId")
    invoice_address = state.get("invoiceAddress")
    invoice_token = state.get("invoiceToken")
    invoice_chain_id = state.get("invoiceChainId")
    invoice_amount_hex = state.get("invoiceAmount", "0x0")
    expires_at = state.get("invoiceExpiresAt", 0)

    if not all([req_id, invoice_address, invoice_token, invoice_chain_id]):
        raise FragmentAPIError(
            "Invoice data missing from Fragment response. "
            "EVM payment may not be supported for this item."
        )

    token_key = invoice_token.lower()
    token_decimals = EVM_TOKEN_DECIMALS.get(token_key, 6)
    token_symbol = EVM_TOKEN_SYMBOLS.get(
        token_key,
        payment_method.split("_")[0].upper(),
    )
    chain_name = EVM_CHAIN_NAMES.get(
        invoice_chain_id,
        f"chain_{invoice_chain_id}",
    )

    invoice_amount_raw = _hex_to_int(invoice_amount_hex)
    invoice_amount = invoice_amount_raw / (10 ** token_decimals)

    return EvmInvoice(
        req_id=req_id,
        invoice_address=invoice_address,
        invoice_token=invoice_token,
        invoice_chain_id=invoice_chain_id,
        invoice_chain_name=chain_name,
        invoice_amount_hex=invoice_amount_hex,
        invoice_amount=invoice_amount,
        invoice_amount_raw=invoice_amount_raw,
        token_symbol=token_symbol,
        token_decimals=token_decimals,
        expires_at=expires_at,
        payment_method=payment_method,
        api_hash=api_hash,
        page_url=invoice_url,
    )