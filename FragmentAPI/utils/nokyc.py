"""
No-KYC mode utilities using MarketApp API.

Provides Fragment operations (Stars, Premium, Giveaways, Ads topup, Ads recharge)
without requiring Fragment cookies or KYC verification.
Uses MarketApp API (marketapp-api library) for transaction building
and optionally executes transactions via configured TON wallet.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from MarketappAPI import MarketappClient
from MarketappAPI.types.models import (
    BuyPremiumBody,
    BuyPremiumGiveawayBody,
    BuyStarsBody,
    BuyStarsGiveawayBody,
    AdsTopupBody,
    TelegramTopupBody,
    SearchRecipientBody,
    StarsPriceBody,
)

from FragmentAPI.exceptions import (
    AlreadySubscribedError,
    ConfigurationError,
    FragmentError,
    MarketAppAPIError,
    UserNotFoundError,
)
from FragmentAPI.types.constants import (
    DEFAULT_MARKETAPP_TOKEN,
    NOKYC_PAYMENT_METHODS,
    PREMIUM_MONTHS_VALID,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
    GRAM_TOPUP_MIN,
    GRAM_TOPUP_MAX,
)
from FragmentAPI.types.models import (
    AdsRechargeResult,
    GiveawayPremiumResult,
    GiveawayStarsResult,
    NoKycBatchResult,
    BatchItemResult,
    PreparedTransaction,
    PreparedTransactionMessage,
    PremiumPriceOption,
    PremiumPrices,
    PurchaseItem,
    PurchaseResult,
    RecipientInfo,
    StarsPrice,
    TransactionResult,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

logger = logging.getLogger("FragmentAPI")


def _build_marketapp_client(client: "FragmentClient") -> MarketappClient:
    """Create a MarketappClient instance from FragmentClient configuration."""
    return MarketappClient(
        api_token=client.marketapp_token,
        seed=client.seed,
        api_key=client.api_key,
        api_provider=client.api_provider,
        wallet_version=client.wallet_version,
        timeout=client.timeout,
    )


def _extract_photo_url(photo_raw: str | None) -> str | None:
    """Extract clean URL from raw photo string or img tag."""
    if not photo_raw:
        return None
    photo_str = str(photo_raw).strip()
    if photo_str.startswith("http://") or photo_str.startswith("https://"):
        return photo_str
    match = re.search(r'src=["\']([^"\']+)["\']', photo_str)
    return match.group(1) if match else photo_str


def _send_tx_to_prepared(
    send_tx: Any,
    item_kind: str,
    target: str,
    amount: int,
) -> PreparedTransaction:
    """Convert MarketApp SendTxSchema to PreparedTransaction."""
    tx_data = send_tx.transaction
    messages = []
    for msg in tx_data.messages:
        messages.append(PreparedTransactionMessage(
            address=msg.address,
            amount=msg.amount,
            payload=msg.payload if hasattr(msg, "payload") else None,
            state_init=msg.stateInit if hasattr(msg, "stateInit") else None,
        ))

    raw_dict = send_tx.model_dump() if hasattr(send_tx, "model_dump") else {}

    return PreparedTransaction(
        req_id="",
        item_kind=item_kind,
        target=target,
        amount=amount,
        valid_until=tx_data.validUntil if hasattr(tx_data, "validUntil") else 0,
        messages=messages,
        raw=raw_dict,
    )


def _tx_result_from_marketapp(result: Any) -> TransactionResult:
    """Convert MarketApp TransactionResult to FragmentAPI TransactionResult."""
    return TransactionResult(
        tx_hash=getattr(result, "tx_hash", ""),
        boc=getattr(result, "boc", None),
        seqno_before=getattr(result, "seqno_before", None),
        seqno_after=getattr(result, "seqno_after", None),
        balance_before=getattr(result, "balance_before", None),
        balance_after=getattr(result, "balance_after", None),
        confirmed=getattr(result, "confirmed", False),
    )


async def nokyc_get_stars_price(client: "FragmentClient", quantity: int) -> StarsPrice:
    """Get Stars price via MarketApp API."""
    try:
        mc = _build_marketapp_client(client)
        body = StarsPriceBody(quantity=quantity)
        resp = await mc.get_stars_prices(body)

        # MarketApp StarsPriceResponse has .gram, .ton, .usd
        gram_val = getattr(resp, "gram", None) or getattr(resp, "ton", 0.0)
        usd_val = getattr(resp, "usd", None) or 0.0

        return StarsPrice(
            stars=quantity,
            gram_price=str(gram_val),
            usd_price=str(usd_val),
        )
    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.API_CALL_FAILED.format(method="get_stars_prices", error=exc)
        ) from exc


async def nokyc_get_premium_prices(client: "FragmentClient") -> PremiumPrices:
    """Get Premium prices via MarketApp API."""
    try:
        mc = _build_marketapp_client(client)
        resp = await mc.get_premium_price()

        options = []
        months_map = [
            (3, getattr(resp, "months3", None)),
            (6, getattr(resp, "months6", None)),
            (12, getattr(resp, "months12", None)),
        ]

        for months, price_resp in months_map:
            if price_resp is not None:
                gram_val = getattr(price_resp, "gram", None) or getattr(price_resp, "ton", 0.0)
                usd_val = getattr(price_resp, "usd", None) or 0.0
                options.append(PremiumPriceOption(
                    months=months,
                    label=f"{months} months",
                    gram_price=str(gram_val),
                    usd_price=str(usd_val),
                ))

        return PremiumPrices(options=options, gram_rate=0.0)
    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.API_CALL_FAILED.format(method="get_premium_price", error=exc)
        ) from exc


async def nokyc_search_recipient(
    client: "FragmentClient",
    username: str,
    method_name: str,
) -> RecipientInfo:
    """Search for recipient via MarketApp API."""
    try:
        mc = _build_marketapp_client(client)
        body = SearchRecipientBody(username=username)

        method_map = {
            "stars": mc.search_stars_recipient,
            "premium": mc.search_premium_recipient,
            "stars_giveaway": mc.search_stars_giveaway_recipient,
            "premium_giveaway": mc.search_premium_giveaway_recipient,
            "topup_gram": mc.search_telegram_topup_recipient,
        }

        search_fn = method_map.get(method_name)
        if not search_fn:
            raise ConfigurationError(f"Unknown recipient search method: {method_name}")

        resp = await search_fn(body)

        if not resp:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        raw_photo = getattr(resp, "photo", None)

        return RecipientInfo(
            recipient=username,
            name=getattr(resp, "name", username),
            photo_url=_extract_photo_url(raw_photo),
            myself=False,
        )
    except (FragmentError, UserNotFoundError, AlreadySubscribedError):
        raise
    except Exception as exc:
        exc_str = str(exc).lower()
        if "already" in exc_str or "subscribed" in exc_str:
            raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE) from exc
        if "not found" in exc_str or "404" in exc_str:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username)) from exc

        raise MarketAppAPIError(
            MarketAppAPIError.API_CALL_FAILED.format(
                method=f"search_{method_name}_recipient", error=exc,
            )
        ) from exc


async def nokyc_purchase_stars(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> PurchaseResult | PreparedTransaction:
    """Purchase Stars via MarketApp API (No-KYC mode)."""
    if not isinstance(amount, int) or not (STARS_PURCHASE_MIN <= amount <= STARS_PURCHASE_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)

    try:
        mc = _build_marketapp_client(client)
        body = BuyStarsBody(
            username=username,
            quantity=amount,
        )

        auto_pay = client.has_wallet
        result = await mc.buy_stars(body, auto_pay=auto_pay)

        if auto_pay:
            tx = _tx_result_from_marketapp(result)
            return PurchaseResult(
                transaction_id=tx.tx_hash,
                type="stars",
                username=username,
                amount=amount,
                payment_method="gram",
            )
        else:
            return _send_tx_to_prepared(result, "stars", username, amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.TRANSACTION_BUILD_FAILED.format(error=exc)
        ) from exc


async def nokyc_purchase_premium(
    client: "FragmentClient",
    username: str,
    months: int,
    show_sender: bool = True,
) -> PurchaseResult | PreparedTransaction:
    """Purchase Premium via MarketApp API (No-KYC mode)."""
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)

    try:
        mc = _build_marketapp_client(client)
        body = BuyPremiumBody(
            username=username,
            months=months,
        )

        auto_pay = client.has_wallet
        result = await mc.buy_premium(body, auto_pay=auto_pay)

        if auto_pay:
            tx = _tx_result_from_marketapp(result)
            return PurchaseResult(
                transaction_id=tx.tx_hash,
                type="premium",
                username=username,
                amount=months,
                payment_method="gram",
            )
        else:
            return _send_tx_to_prepared(result, "premium", username, months)

    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.TRANSACTION_BUILD_FAILED.format(error=exc)
        ) from exc


async def nokyc_topup_gram(
    client: "FragmentClient",
    username: str,
    amount: int,
    show_sender: bool = True,
) -> PurchaseResult | PreparedTransaction:
    """Top up GRAM to Telegram Ads via MarketApp API (No-KYC mode)."""
    if not isinstance(amount, int) or not (GRAM_TOPUP_MIN <= amount <= GRAM_TOPUP_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    try:
        mc = _build_marketapp_client(client)
        body = TelegramTopupBody(
            username=username,
            amount=amount,
        )

        auto_pay = client.has_wallet
        result = await mc.telegram_topup(body, auto_pay=auto_pay)

        if auto_pay:
            tx = _tx_result_from_marketapp(result)
            return PurchaseResult(
                transaction_id=tx.tx_hash,
                type="gram",
                username=username,
                amount=amount,
                payment_method="gram",
            )
        else:
            return _send_tx_to_prepared(result, "gram", username, amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.TRANSACTION_BUILD_FAILED.format(error=exc)
        ) from exc


async def nokyc_recharge_ads(
    client: "FragmentClient",
    account_id: str,
    amount: int,
) -> AdsRechargeResult | PreparedTransaction:
    """Recharge Telegram Ads account via MarketApp API (No-KYC mode)."""
    if not isinstance(amount, int) or amount < 1:
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    try:
        mc = _build_marketapp_client(client)
        link = account_id if account_id.startswith("http") else f"https://fragment.com/ads/pay?account={account_id}"
        body = AdsTopupBody(
            fragment_link=link,
            amount=amount,
        )

        auto_pay = client.has_wallet
        result = await mc.ads_topup(body, auto_pay=auto_pay)

        if auto_pay:
            tx = _tx_result_from_marketapp(result)
            return AdsRechargeResult(
                transaction_id=tx.tx_hash,
                account_id=account_id,
                amount=amount,
            )
        else:
            return _send_tx_to_prepared(result, "ads_recharge", account_id, amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.TRANSACTION_BUILD_FAILED.format(error=exc)
        ) from exc


async def nokyc_giveaway_stars(
    client: "FragmentClient",
    channel: str,
    winners: int,
    amount: int,
) -> GiveawayStarsResult | PreparedTransaction:
    """Run Stars giveaway via MarketApp API (No-KYC mode)."""
    try:
        mc = _build_marketapp_client(client)
        body = BuyStarsGiveawayBody(
            username=channel,
            quantity=winners,
            stars=amount,
        )

        auto_pay = client.has_wallet
        result = await mc.buy_stars_giveaway(body, auto_pay=auto_pay)

        if auto_pay:
            tx = _tx_result_from_marketapp(result)
            return GiveawayStarsResult(
                transaction_id=tx.tx_hash,
                channel=channel,
                winners=winners,
                amount=amount,
                payment_method="gram",
            )
        else:
            return _send_tx_to_prepared(result, "giveaway_stars", channel, amount)

    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.TRANSACTION_BUILD_FAILED.format(error=exc)
        ) from exc


async def nokyc_giveaway_premium(
    client: "FragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
) -> GiveawayPremiumResult | PreparedTransaction:
    """Run Premium giveaway via MarketApp API (No-KYC mode)."""
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)

    try:
        mc = _build_marketapp_client(client)
        body = BuyPremiumGiveawayBody(
            username=channel,
            quantity=winners,
            months=months,
        )

        auto_pay = client.has_wallet
        result = await mc.buy_premium_giveaway(body, auto_pay=auto_pay)

        if auto_pay:
            tx = _tx_result_from_marketapp(result)
            return GiveawayPremiumResult(
                transaction_id=tx.tx_hash,
                channel=channel,
                winners=winners,
                amount=months,
                payment_method="gram",
            )
        else:
            return _send_tx_to_prepared(result, "giveaway_premium", channel, months)

    except FragmentError:
        raise
    except Exception as exc:
        raise MarketAppAPIError(
            MarketAppAPIError.TRANSACTION_BUILD_FAILED.format(error=exc)
        ) from exc


async def nokyc_batch_purchase(
    client: "FragmentClient",
    items: list[dict[str, Any] | PurchaseItem],
) -> NoKycBatchResult:
    """Execute batch purchase in No-KYC mode."""
    result_items: list[BatchItemResult] = []
    prepared: list[PreparedTransaction] = []
    succeeded = 0
    failed = 0

    for raw_item in items:
        if isinstance(raw_item, PurchaseItem):
            item = raw_item.model_dump()
        elif isinstance(raw_item, dict):
            item = dict(raw_item)
        else:
            failed += 1
            result_items.append(BatchItemResult(
                type="unknown", username="", amount=0,
                ok=False, error=f"Invalid item format: {type(raw_item)}",
            ))
            continue

        item_type = item.get("type", "")
        username = str(item.get("username", "")).strip()
        amount = item.get("amount")
        months = item.get("months")
        show_sender = item.get("show_sender", True)
        display_amount = months if item_type == "premium" else (amount or 0)

        try:
            if item_type == "stars":
                result = await nokyc_purchase_stars(client, username, amount, show_sender)
            elif item_type == "premium":
                result = await nokyc_purchase_premium(client, username, months, show_sender)
            elif item_type in ("gram", "ton"):
                result = await nokyc_topup_gram(client, username, amount, show_sender)
            else:
                raise ConfigurationError(f"Unsupported purchase type for No-KYC mode: {item_type}")

            if isinstance(result, PurchaseResult):
                succeeded += 1
                result_items.append(BatchItemResult(
                    type=item_type, username=username, amount=display_amount,
                    ok=True, result={
                        "transaction_id": result.transaction_id,
                        "type": item_type,
                        "username": username,
                        "amount": display_amount,
                        "payment_method": "gram",
                    },
                ))
            elif isinstance(result, PreparedTransaction):
                succeeded += 1
                prepared.append(result)
                result_items.append(BatchItemResult(
                    type=item_type, username=username, amount=display_amount,
                    ok=True, result={"prepared": True},
                ))

        except Exception as exc:
            failed += 1
            result_items.append(BatchItemResult(
                type=item_type, username=username, amount=display_amount,
                ok=False, error=str(exc),
            ))

    return NoKycBatchResult(
        total=len(items),
        succeeded=succeeded,
        failed=failed,
        items=result_items,
        prepared_transactions=prepared,
    )