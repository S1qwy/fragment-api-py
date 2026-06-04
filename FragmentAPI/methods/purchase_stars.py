from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.methods._prepare import (
    prepare_via_rest_api,
    prepared_to_transaction_data,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    EVM_PAYMENT_METHODS,
    STARS_PAGE,
    TON_PAYMENT_METHODS,
    VALID_PAYMENT_METHODS,
)
from FragmentAPI.types.results import (
    EvmPaymentResult,
    StarsResult,
)
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
    fetch_wallet_info,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


async def _resolve_stars_recipient(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict,
    username: str,
) -> str:
    '''Resolve a Stars recipient ID via Fragment API.'''
    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "searchStarsRecipient",
            "query": username,
            "quantity": "",
        },
    )
    recipient = (result.get("found") or {}).get("recipient")
    if not recipient:
        raise UserNotFoundError(
            UserNotFoundError.NOT_FOUND.format(username=username),
        )
    return recipient


async def _init_buy_stars(
    session: httpx.AsyncClient,
    fragment_hash: str,
    headers: dict,
    recipient: str,
    amount: int,
    payment_method: str,
) -> str:
    '''Run initBuyStarsRequest and return Fragment req_id.'''
    result = await post_FragmentAPI(
        session,
        fragment_hash,
        headers,
        {
            "method": "initBuyStarsRequest",
            "recipient": recipient,
            "quantity": str(amount),
            "payment_method": payment_method,
        },
    )
    if result.get("error"):
        raise FragmentAPIError(result["error"])

    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            FragmentAPIError.NO_REQUEST_ID.format(
                context="Stars purchase",
            )
        )
    return req_id


async def _purchase_stars_with_cookies(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool,
    payment_method: str,
) -> StarsResult | EvmPaymentResult:
    '''Full Stars purchase flow using cookies + seed.'''
    headers = build_headers(STARS_PAGE)

    async with httpx.AsyncClient(
        cookies=client.cookies,
        timeout=client.timeout,
    ) as session:
        fragment_hash = await fetch_fragment_hash(
            client.cookies,
            headers,
            STARS_PAGE,
            client.timeout,
        )

        recipient = await _resolve_stars_recipient(
            session,
            fragment_hash,
            headers,
            username,
        )
        req_id = await _init_buy_stars(
            session,
            fragment_hash,
            headers,
            recipient,
            amount,
            payment_method,
        )

        account = await build_account_info(client)
        transaction = await post_FragmentAPI(
            session,
            fragment_hash,
            headers,
            {
                "method": "getBuyStarsLink",
                "account": json.dumps(account),
                "device": DEVICE_FINGERPRINT,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
            },
        )
        if transaction.get("need_verify"):
            raise VerificationError(VerificationError.KYC_REQUIRED)

    if payment_method in EVM_PAYMENT_METHODS or transaction.get("evm"):
        invoice = await fetch_evm_invoice(
            cookies=client.cookies,
            page_path="/stars/buy",
            recipient=recipient,
            payment_method=payment_method,
            quantity=amount,
            timeout=client.timeout,
        )
        return EvmPaymentResult(
            item_kind="stars",
            target=username,
            amount=amount,
            payment_method=payment_method,
            invoice=invoice,
        )

    if payment_method not in TON_PAYMENT_METHODS:
        raise FragmentAPIError(
            f"Unsupported payment_method flow: {payment_method}"
        )

    tx_result = await execute_transaction(client, transaction)

    if tx_result.boc and req_id:
        try:
            await client.confirm_request(
                req_id,
                tx_result.boc,
                referer="stars/buy",
            )
        except Exception:
            pass

    return StarsResult(
        transaction_id=tx_result.tx_hash,
        username=username,
        amount=amount,
        payment_method=payment_method,
    )


async def _purchase_stars_no_cookies(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool,
    payment_method: str,
) -> StarsResult:
    '''Stars purchase flow without cookies via REST API.'''
    wallet_info = await fetch_wallet_info(client)
    sender_address = wallet_info.address

    prepared = await prepare_via_rest_api(
        endpoint="/api/v1/stars/buy",
        payload={
            "username": username,
            "amount": amount,
            "show_sender": show_sender,
            "payment_method": payment_method,
        },
        item_kind="stars",
        target=username,
        amount=amount,
        sender_wallet_address=sender_address,
        timeout=client.timeout,
    )

    tx_data = prepared_to_transaction_data(prepared)
    tx_result = await execute_transaction(client, tx_data)

    if tx_result.boc and prepared.req_id:
        try:
            await client.confirm_request(
                prepared.req_id,
                tx_result.boc,
                referer=prepared.confirm_referer or "stars/buy",
            )
        except Exception:
            pass

    return StarsResult(
        transaction_id=tx_result.tx_hash,
        username=username,
        amount=amount,
        payment_method=payment_method,
    )


async def purchase_stars(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: str = "ton",
) -> StarsResult | EvmPaymentResult:
    '''Send Telegram Stars to a user. Works with or without cookies.'''
    if not isinstance(amount, int) or not (50 <= amount <= 10_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_AMOUNT)
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ConfigError(ConfigError.INVALID_PAYMENT_METHOD)

    try:
        if client.has_cookies:
            return await _purchase_stars_with_cookies(
                client, username, amount, show_sender, payment_method,
            )
        else:
            if payment_method not in TON_PAYMENT_METHODS:
                raise ConfigError(
                    "No-cookie mode supports only TON payment methods.",
                )
            return await _purchase_stars_no_cookies(
                client, username, amount, show_sender, payment_method,
            )
    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc