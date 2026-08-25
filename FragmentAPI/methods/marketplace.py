"""
Marketplace and utility methods — offers, auction management, subscriptions, gateway.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from FragmentAPI.exceptions import (
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    UnexpectedError,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    FRAGMENT_BASE_URL,
    GATEWAY_PAGE,
    ITEM_TYPE_URL_PREFIX,
    VALID_ITEM_TYPES,
)
from FragmentAPI.types.models import (
    AdsWithdrawalConfirmResult,
    AdsWithdrawalInitResult,
    GatewayPriceInfo,
    GatewayRechargeResult,
    AdsRechargeResult,
    OfferResult,
    SubscriptionResult,
    TransactionResult,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

logger = logging.getLogger("FragmentAPI")


def _item_page_url(item_type: int, slug: str) -> str:
    """Build the Fragment page URL for an item."""
    prefix = ITEM_TYPE_URL_PREFIX.get(item_type, "username")
    return f"{FRAGMENT_BASE_URL}/{prefix}/{slug}"


async def make_offer(
    client: "FragmentClient",
    item_type: int,
    slug: str,
    amount: int,
) -> OfferResult:
    """Make an offer to buy an unlisted username, number, or gift."""
    if item_type not in VALID_ITEM_TYPES:
        raise ConfigurationError(ConfigurationError.INVALID_ITEM_TYPE.format(item_type=item_type))
    if not isinstance(amount, int) or amount < 1:
        raise ConfigurationError(ConfigurationError.INVALID_OFFER_AMOUNT)

    client._require_wallet()

    try:
        page_url = _item_page_url(item_type, slug)

        init_res = await client.call(
            "initOfferRequest",
            {"type": str(item_type), "username": slug},
            page_url=page_url,
        )
        if init_res.get("error"):
            raise FragmentAPIError(init_res["error"])
        req_id = init_res.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="make offer"))

        account = await build_account_info(client)
        transaction = await client.call(
            "getOfferLink",
            {
                "account": json.dumps(account),
                "device": DEVICE_FINGERPRINT,
                "transaction": "1",
                "id": req_id,
                "amount": str(amount),
            },
            page_url=page_url,
        )
        if transaction.get("error"):
            raise FragmentAPIError(str(transaction["error"]))

        tx_result = await execute_transaction(client, transaction)

        return OfferResult(
            transaction_id=tx_result.tx_hash,
            item_type=item_type,
            slug=slug,
            amount=amount,
            req_id=req_id,
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def cancel_auction(
    client: "FragmentClient",
    item_type: int,
    slug: str,
) -> TransactionResult:
    """Cancel an active auction if no bids have been placed."""
    if item_type not in VALID_ITEM_TYPES:
        raise ConfigurationError(ConfigurationError.INVALID_ITEM_TYPE.format(item_type=item_type))

    client._require_wallet()

    try:
        page_url = _item_page_url(item_type, slug)
        account = await build_account_info(client)

        transaction = await client.call(
            "getCancelAuctionLink",
            {
                "account": json.dumps(account),
                "device": DEVICE_FINGERPRINT,
                "transaction": "1",
                "type": str(item_type),
                "username": slug,
            },
            page_url=page_url,
        )
        if transaction.get("error"):
            raise FragmentAPIError(str(transaction["error"]))

        return await execute_transaction(client, transaction)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def subscribe_to_item(
    client: "FragmentClient",
    item_type: int,
    slug: str,
) -> SubscriptionResult:
    """Subscribe to auction updates for an item (Telegram notifications)."""
    if item_type not in VALID_ITEM_TYPES:
        raise ConfigurationError(ConfigurationError.INVALID_ITEM_TYPE.format(item_type=item_type))

    try:
        page_url = _item_page_url(item_type, slug)
        result = await client.call(
            "subscribe",
            {"type": str(item_type), "username": slug},
            page_url=page_url,
        )
        if result.get("error"):
            raise FragmentAPIError(result["error"])
        return SubscriptionResult(ok=True, subscribed=True, item_type=item_type, slug=slug)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def unsubscribe_from_item(
    client: "FragmentClient",
    item_type: int,
    slug: str,
) -> SubscriptionResult:
    """Unsubscribe from auction updates for an item."""
    if item_type not in VALID_ITEM_TYPES:
        raise ConfigurationError(ConfigurationError.INVALID_ITEM_TYPE.format(item_type=item_type))

    try:
        page_url = _item_page_url(item_type, slug)
        result = await client.call(
            "unsubscribe",
            {"type": str(item_type), "username": slug},
            page_url=page_url,
        )
        if result.get("error"):
            raise FragmentAPIError(result["error"])
        return SubscriptionResult(ok=True, subscribed=False, item_type=item_type, slug=slug)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def init_ads_withdrawal(
    client: "FragmentClient",
    transaction_id: str,
) -> AdsWithdrawalInitResult:
    """Initialize Ads revenue withdrawal to wallet."""
    client._require_ton_token()
    client._require_wallet()

    try:
        wallet_info = await client.get_wallet()
        result = await client.call(
            "initAdsRevenueWithdrawalRequest",
            {
                "transaction": transaction_id,
                "wallet_address": wallet_info.address,
            },
        )
        if result.get("error"):
            return AdsWithdrawalInitResult(ok=False, error=result["error"])

        return AdsWithdrawalInitResult(
            ok=result.get("ok", False),
            confirm_message=result.get("confirm_message"),
            confirm_button=result.get("confirm_button"),
            confirm_hash=result.get("confirm_hash"),
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def confirm_ads_withdrawal(
    client: "FragmentClient",
    transaction_id: str,
    confirm_hash: str,
) -> AdsWithdrawalConfirmResult:
    """Confirm Ads revenue withdrawal after user approval."""
    client._require_ton_token()
    client._require_wallet()

    try:
        wallet_info = await client.get_wallet()
        result = await client.call(
            "initAdsRevenueWithdrawalRequest",
            {
                "transaction": transaction_id,
                "wallet_address": wallet_info.address,
                "confirm_hash": confirm_hash,
            },
        )
        if result.get("error"):
            return AdsWithdrawalConfirmResult(ok=False, mode="error", error=result["error"])

        return AdsWithdrawalConfirmResult(
            ok=result.get("ok", False),
            need_update=result.get("need_update", False),
            mode=result.get("mode", "unknown"),
            html=result.get("html"),
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def get_gateway_price(
    client: "FragmentClient",
    account_id: str,
    credits: int,
) -> GatewayPriceInfo:
    """Get price info for Telegram Gateway credits."""
    try:
        result = await client.call(
            "updateGatewayPrices",
            {"account": account_id, "credits": str(credits)},
            page_url=GATEWAY_PAGE,
        )

        gram_price = result.get("price", "0")
        usd_price = result.get("usd_price")

        return GatewayPriceInfo(credits=credits, gram_price=str(gram_price), usd_price=usd_price)

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def recharge_gateway(
    client: "FragmentClient",
    account_id: str,
    credits: int,
) -> GatewayRechargeResult:
    """Recharge Telegram Gateway credits via TON payment."""
    if not isinstance(credits, int) or credits < 1:
        raise ConfigurationError(ConfigurationError.INVALID_CREDITS_AMOUNT)

    client._require_wallet()

    try:
        init_res = await client.call(
            "initGatewayRechargeRequest",
            {"account": account_id, "credits": str(credits)},
            page_url=GATEWAY_PAGE,
        )
        if init_res.get("error"):
            raise FragmentAPIError(init_res["error"])
        req_id = init_res.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Gateway recharge"))

        account = await build_account_info(client)
        transaction = await client.call(
            "getGatewayRechargeLink",
            {
                "account": json.dumps(account),
                "device": DEVICE_FINGERPRINT,
                "transaction": "1",
                "id": req_id,
            },
            page_url=GATEWAY_PAGE,
        )
        if transaction.get("error"):
            raise FragmentAPIError(str(transaction["error"]))

        tx_result = await execute_transaction(client, transaction)

        if tx_result.boc and req_id:
            try:
                await client.confirm_request(req_id, tx_result.boc, referer="gateway")
            except Exception:
                pass

        return GatewayRechargeResult(
            transaction_id=tx_result.tx_hash,
            account_id=account_id,
            credits=credits,
            req_id=req_id,
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def recharge_ads(
    client: "FragmentClient",
    account_id: str,
    amount: int,
) -> AdsRechargeResult:
    """Recharge Telegram Ads account via TON payment."""
    if not isinstance(amount, int) or amount < 1:
        raise ConfigurationError(ConfigurationError.INVALID_GRAM_AMOUNT)

    client._require_wallet()

    try:
        page_url = f"{FRAGMENT_BASE_URL}/ads/pay"

        init_res = await client.call(
            "initAdsRechargeRequest",
            {"account": account_id, "amount": str(amount)},
            page_url=page_url,
        )
        if init_res.get("error"):
            raise FragmentAPIError(init_res["error"])

        req_id = init_res.get("req_id")
        if not req_id:
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Ads recharge"))

        account = await build_account_info(client)
        transaction = await client.call(
            "getAdsRechargeLink",
            {
                "account": json.dumps(account),
                "device": DEVICE_FINGERPRINT,
                "transaction": "1",
                "id": req_id,
            },
            page_url=page_url,
        )
        if transaction.get("error"):
            raise FragmentAPIError(str(transaction["error"]))

        tx_result = await execute_transaction(client, transaction)

        if tx_result.boc and req_id:
            try:
                await client.confirm_request(req_id, tx_result.boc, referer="ads")
            except Exception:
                pass

        return AdsRechargeResult(
            transaction_id=tx_result.tx_hash,
            account_id=account_id,
            amount=amount,
            req_id=req_id,
        )

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc