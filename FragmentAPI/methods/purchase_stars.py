'''
Telegram Stars purchase method — async only with confirmReq and EVM support.
'''

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
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


async def purchase_stars(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: str = "ton",
) -> StarsResult | EvmPaymentResult:
    '''
    Send Telegram Stars to a user.

    Args:
        client: Authenticated FragmentClient instance.
        username: Recipient Telegram username.
        amount: Number of Stars — 50 to 10_000_000.
        show_sender: Show your name as the gift sender.
        payment_method: One of "ton", "usdt_ton", "usdt_eth", "usdt_pol",
            "usdc_eth", "usdc_base", "usdc_pol".

    Returns:
        StarsResult (for TON-based methods) or EvmPaymentResult
        (for EVM methods — caller must complete payment manually).
    '''
    if not isinstance(amount, int) or not (50 <= amount <= 10_000_000):
        raise ConfigError(ConfigError.INVALID_STARS_AMOUNT)
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ConfigError(ConfigError.INVALID_PAYMENT_METHOD)

    try:
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
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=username),
                )

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

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc