"""
Unified purchase method for Stars, Premium, and GRAM (Ads) top-up.

Provides a single purchase() entry point that dispatches to the appropriate
Fragment API flow based on item type. Also provides backward-compatible
purchase_stars(), purchase_premium(), topup_gram(), and topup_ton() wrappers.
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
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    ADS_TOPUP_PAGE,
    DEVICE_FINGERPRINT,
    EVM_PAYMENT_METHODS,
    GRAM_PAYMENT_METHODS,
    GRAM_TOPUP_MAX,
    GRAM_TOPUP_MIN,
    PREMIUM_GIFT_PAGE,
    PREMIUM_MONTHS_VALID,
    PURCHASE_TYPES,
    STARS_PAGE,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
    VALID_PAYMENT_METHODS,
)
from FragmentAPI.types.results import (
    AdsTopupResult,
    EvmPaymentResult,
    PremiumResult,
    PurchaseItem,
    PurchaseResult,
    StarsResult,
)
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_fragment_api,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
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
    """Normalize payment method: gram <-> ton aliases."""
    if method == "gram":
        return "ton"
    if method == "usdt_gram":
        return "usdt_ton"
    return method


def _validate_purchase_item(item_type: str, amount: int | None, months: int | None) -> None:
    """Validate purchase parameters for a single item.

    Args:
        item_type: One of "stars", "premium", "gram", "ton".
        amount: Stars count or GRAM amount (for stars/gram/ton types).
        months: Premium duration (for premium type).

    Raises:
        ConfigurationError: If parameters are invalid.
    """
    if item_type == "premium":
        if months not in PREMIUM_MONTHS_VALID:
            raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    elif item_type == "stars":
        if not isinstance(amount, int) or not (STARS_PURCHASE_MIN <= amount <= STARS_PURCHASE_MAX):
            raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    elif item_type in ("gram", "ton"):
        if not isinstance(amount, int) or not (GRAM_TOPUP_MIN <= amount <= GRAM_TOPUP_MAX):
            raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)
    else:
        raise ConfigurationError(f"Invalid purchase type '{item_type}'. Must be one of: {', '.join(sorted(PURCHASE_TYPES))}.")


async def _resolve_recipient(
    session: requests.AsyncSession,
    fragment_hash: str,
    headers: dict[str, str],
    item_type: str,
    username: str,
    months: int | None = None,
) -> str:
    """Resolve a Fragment recipient ID for a given purchase type."""
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
    logger.debug("Resolved recipient for %s/%s", item_type, username)
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
    """Call the appropriate initXxxRequest method and return req_id."""
    init_method = _TYPE_INIT_METHOD[item_type]
    api_payment = _normalize_payment_method(payment_method)

    payload: dict[str, Any] = {"method": init_method, "recipient": recipient}

    if item_type == "stars":
        payload["quantity"] = str(amount)
        payload["payment_method"] = api_payment
    elif item_type == "premium":
        if item_type == "premium":
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
        raise FragmentAPIError(result["error"])

    req_id = result.get("req_id")
    if not req_id:
        raise FragmentAPIError(
            FragmentAPIError.NO_REQUEST_ID.format(context=f"{item_type} purchase")
        )
    logger.debug("Init request complete for %s, req_id=%s", item_type, req_id)
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
    """Call the appropriate getXxxLink method and return transaction payload."""
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


async def purchase(
    client: "FragmentClient",
    item_type: str,
    username: str,
    amount: int | None = None,
    months: int | None = None,
    show_sender: bool = True,
    payment_method: str = "gram",
) -> PurchaseResult | EvmPaymentResult:
    """Execute a single purchase operation on Fragment.

    Unified entry point for Stars, Premium, and GRAM (Ads) top-up purchases.
    Dispatches to the appropriate Fragment API flow based on item_type.

    Args:
        client: Authenticated FragmentClient instance.
        item_type: "stars", "premium", "gram", or "ton".
        username: Telegram username of the recipient.
        amount: Stars count or GRAM amount (required for stars/gram/ton).
        months: Premium duration in months (required for premium, one of 3/6/12).
        show_sender: Whether to show sender name in the gift notification.
        payment_method: Payment method ("gram", "ton", "usdt_gram", "usdt_ton", or EVM methods).

    Returns:
        PurchaseResult for TON-based payments, EvmPaymentResult for EVM payments.

    Raises:
        ConfigurationError: If parameters are invalid.
        UserNotFoundError: If the recipient is not found on Fragment.
        VerificationError: If KYC is required.
        FragmentAPIError: If Fragment API returns an error.
    """
    _validate_purchase_item(item_type, amount, months)

    api_payment = _normalize_payment_method(payment_method)

    if api_payment not in {_normalize_payment_method(m) for m in VALID_PAYMENT_METHODS}:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(VALID_PAYMENT_METHODS)),
            )
        )

    if item_type in ("gram", "ton") and api_payment not in {"ton", "usdt_ton"}:
        raise ConfigurationError(
            "Ads top-up only supports GRAM/TON payment methods."
        )

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

            raise FragmentAPIError(f"Unsupported payment flow for {item_type}/{payment_method}")

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def purchase_stars(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: str = "gram",
) -> PurchaseResult | EvmPaymentResult:
    """Send Telegram Stars to a user.

    Convenience wrapper around purchase() for backward compatibility.

    Args:
        client: Authenticated FragmentClient instance.
        username: Telegram username of the recipient.
        amount: Number of Stars to send (50 to 10,000,000).
        show_sender: Show sender name in the gift notification.
        payment_method: Payment method string.

    Returns:
        PurchaseResult or EvmPaymentResult.
    """
    return await purchase(
        client, "stars", username,
        amount=amount, show_sender=show_sender, payment_method=payment_method,
    )


async def purchase_premium(
    client: "FragmentClient",
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: str = "gram",
) -> PurchaseResult | EvmPaymentResult:
    """Gift Telegram Premium to a user.

    Convenience wrapper around purchase() for backward compatibility.

    Args:
        client: Authenticated FragmentClient instance.
        username: Telegram username of the recipient.
        months: Premium duration (3, 6, or 12 months).
        show_sender: Show sender name in the gift notification.
        payment_method: Payment method string.

    Returns:
        PurchaseResult or EvmPaymentResult.
    """
    return await purchase(
        client, "premium", username,
        months=months, show_sender=show_sender, payment_method=payment_method,
    )


async def topup_gram(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> PurchaseResult:
    """Top up GRAM to a recipient's Telegram Ads balance.

    Convenience wrapper around purchase() for GRAM top-up.

    Args:
        client: Authenticated FragmentClient instance.
        username: Telegram username of the Ads account.
        amount: GRAM amount to top up (1 to 1,000,000,000).
        show_sender: Show sender name.

    Returns:
        PurchaseResult with transaction details.
    """
    result = await purchase(
        client, "gram", username,
        amount=amount, show_sender=show_sender, payment_method="gram",
    )
    return result


async def topup_ton(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> PurchaseResult:
    """Top up GRAM (formerly TON) to a recipient's Telegram Ads balance.

    Backward-compatible alias for topup_gram().
    """
    return await topup_gram(client, username, amount, show_sender)