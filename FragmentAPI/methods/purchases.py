"""Invoice preparation, single-message purchase batches, and fulfillment receipts."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from urllib.parse import urlsplit

from FragmentAPI.exceptions import (
    ConfigurationError, FragmentAPIError, ParseError,
    TransactionError, UserNotFoundError,
)
from FragmentAPI.types import constants as C
from FragmentAPI.types import models as M
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.validation import (
    decimal_units, integer, months as validate_months,
    normalize_payment_method, recipient as normalize_recipient, stars_giveaway,
)
from FragmentAPI.methods.batches import BatchMixin
from FragmentAPI.utils.wallet import build_account_info, execute_prepared, prepare_transaction

_FLOWS = {
    "stars": (
        C.STARS_BUY_PAGE, "searchStarsRecipient", "updateStarsBuyState",
        "initBuyStarsRequest", "getBuyStarsLink",
    ),
    "premium": (
        C.PREMIUM_GIFT_PAGE, "searchPremiumGiftRecipient", "updatePremiumState",
        "initGiftPremiumRequest", "getGiftPremiumLink",
    ),
    "ton": (
        C.ADS_TOPUP_PAGE, "searchAdsTopupRecipient", "updateAdsTopupState",
        "initAdsTopupRequest", "getAdsTopupLink",
    ),
    "giveaway_stars": (
        C.STARS_GIVEAWAY_PAGE, "searchStarsGiveawayRecipient", "updateStarsGiveawayState",
        "initGiveawayStarsRequest", "getGiveawayStarsLink",
    ),
    "giveaway_premium": (
        C.PREMIUM_GIVEAWAY_PAGE, "searchPremiumGiveawayRecipient", "updatePremiumGiveawayState",
        "initGiveawayPremiumRequest", "getGiveawayPremiumLink",
    ),
    "ads_recharge": (
        C.ADS_PAY_PAGE, None, "updateAdsState",
        "initAdsRechargeRequest", "getAdsRechargeLink",
    ),
    "gateway": (
        C.GATEWAY_PAGE, None, "updateGatewayState",
        "initGatewayRechargeRequest", "getGatewayRechargeLink",
    ),
}



class PurchaseMixin(BatchMixin):
    """Purchase implementation shared by the public Fragment client."""

    async def _confirm(
        self,
        transaction: dict[str, Any],
        receipt: M.TransactionResult,
        account: dict[str, Any],
        req_id: str,
        page_url: str,
        state_method: str | None,
    ) -> M.TransactionResult:
        """Report the signed BOC and poll only explicit successful completion."""
        if not receipt.boc:
            receipt.confirmation_error = "The wallet result did not contain a signed BOC."
            return receipt
        try:
            method = str(transaction.get("confirm_method") or "confirmReq")
            parameters = transaction.get("confirm_params") or {"id": req_id}
            if not isinstance(parameters, dict):
                raise ParseError("Invalid confirmation parameters.")
            await self._api(
                method,
                {
                    **parameters,
                    "account": json.dumps(account),
                    "device": C.DEVICE_FINGERPRINT,
                    "boc": receipt.boc,
                },
                page_url,
            )
            if state_method is None:
                return receipt
            deadline = time.monotonic() + self.confirmation_timeout
            mode = "new"
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                response = await asyncio.wait_for(
                    self._api(
                        state_method,
                        {"id": req_id, "mode": mode, "lv": "false", "dh": str(time.time_ns())},
                        page_url,
                    ),
                    timeout=max(0.001, remaining),
                )
                mode = str(response.get("mode", mode))
                if mode == "done" and response.get("need_update") is False:
                    response_id = str(response.get("req_id") or response.get("id") or "")
                    if response_id != req_id:
                        receipt.confirmation_error = "Fragment returned page completion without matching this invoice id."
                        return receipt
                    receipt.confirmed = True
                    receipt.status = "confirmed"
                    return receipt
                await asyncio.sleep(min(C.CONFIRMATION_INTERVAL, max(0, deadline - time.monotonic())))
            receipt.confirmation_error = "Fragment fulfillment confirmation timed out."
        except Exception as exc:
            receipt.confirmation_error = str(exc)
        finally:
            await asyncio.shield(self._save_confirmation(req_id, receipt))
        return receipt

    async def _purchase_flow(
        self, kind: str, target: str, amount: int, *,
        payment_method: str = "ton", show_sender: bool = True,
        winners: int | None = None,
    ) -> tuple[M.TransactionResult, str] | M.PreparedTransaction | M.EvmPaymentResult:
        """Serialize Fragment's session state through preparation and confirmation."""
        async with self._flow_lock:
            result = await self._prepare_purchase(
                kind, target, amount, payment_method=payment_method,
                show_sender=show_sender, winners=winners,
            )
            if isinstance(result, M.EvmPaymentResult):
                return result
            prepared, context = result
            if not self.has_wallet:
                return prepared
            if not self.wallet_auth:
                self._require_ton_token()
            receipt = await execute_prepared(self, prepared, confirmations=[context])
            receipt = await self._confirm(
                context.transaction, receipt, context.account, context.req_id,
                context.page_url, context.state_method,
            )
            return receipt, context.req_id

    async def _prepare_purchase(
        self,
        kind: str,
        target: str,
        amount: int,
        *,
        payment_method: str = "ton",
        show_sender: bool = True,
        winners: int | None = None,
    ) -> tuple[M.PreparedTransaction, M.PaymentConfirmation] | M.EvmPaymentResult:
        """Prepare an invoice and retain its confirmation context without broadcasting."""
        method = normalize_payment_method(payment_method)
        page, search_method, state_method, init_method, link_method = _FLOWS[kind]
        if kind in {"ton", "ads_recharge", "gateway"} and method != "ton":
            raise ConfigurationError("This operation supports native TON only.")
        if not isinstance(show_sender, bool):
            raise ConfigurationError("show_sender must be a boolean.")
        account = await build_account_info(self) if method not in C.EVM_PAYMENT_METHODS else None
        await self._api(
            state_method,
            {"mode": "new", "lv": "false", "dh": str(time.time_ns())},
            page,
        )
        resolved: M.RecipientInfo | None = None
        search_extra: dict[str, Any] = {}
        if kind == "stars":
            search_extra["quantity"] = ""
        elif kind in {"premium", "giveaway_premium"}:
            search_extra["months"] = amount
        if winners is not None:
            search_extra["quantity"] = winners
        if kind == "giveaway_stars":
            search_extra["stars"] = amount
        if search_method:
            resolved = await self._recipient(
                search_method, target, page, **search_extra
            )
            if resolved is None:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=target)
                )
        data: dict[str, Any] = (
            {"recipient": resolved.recipient}
            if resolved else {"account": target}
        )
        if kind == "stars":
            data["quantity"] = amount
        elif kind == "premium":
            data["months"] = amount
        elif kind == "giveaway_stars":
            data.update(quantity=winners, stars=amount)
            await self._api(
                "updateStarsGiveawayPrices",
                {"quantity": winners, "stars": amount}, page,
            )
        elif kind == "giveaway_premium":
            data.update(quantity=winners, months=amount)
            await self._api(
                "updatePremiumGiveawayPrices", {"quantity": winners}, page
            )
        elif kind == "gateway":
            data["credits"] = amount
        else:
            data["amount"] = amount
        if kind not in {"ton", "ads_recharge", "gateway"}:
            data["payment_method"] = method
        initialized = await self._api(init_method, data, page)
        req_id = str(initialized.get("req_id") or "")
        if not req_id:
            raise FragmentAPIError(
                FragmentAPIError.NO_REQUEST_ID.format(context=kind)
            )

        if method in C.EVM_PAYMENT_METHODS:
            invoice = await fetch_evm_invoice(
                self.cookies, urlsplit(page).path,
                resolved.recipient if resolved else target,
                method,
                quantity=amount if kind == "stars" else winners if kind == "giveaway_stars" else None,
                months=amount if kind in {"premium", "giveaway_premium"} else None,
                amount=amount if kind == "giveaway_stars" else None,
                winners=winners if kind == "giveaway_premium" else None,
                timeout=self.timeout,
                session=self._session,
            )
            return M.EvmPaymentResult(
                item_kind=kind, target=target, amount=amount,
                payment_method=method, invoice=invoice,
            )

        transaction = await self._api(
            link_method,
            {
                "account": json.dumps(account),
                "device": C.DEVICE_FINGERPRINT,
                "transaction": 1,
                "id": req_id,
                "show_sender": int(show_sender),
            },
            page,
        )
        if transaction.get("evm"):
            raise TransactionError(
                "Fragment changed the selected TON payment flow to EVM."
            )

        principal: int | None = None
        usdt_units: int | None = None
        if method == "ton":
            raw_price = initialized.get("amount")
            if raw_price is None and kind in {"ton", "ads_recharge"}:
                raw_price = amount
            if raw_price is not None:
                principal = decimal_units(raw_price, 9)
        else:
            usdt_units = decimal_units(initialized.get("amount"), 6)

        prepared = prepare_transaction(
            transaction,
            payment_method=method,
            payment_nanoton=principal,
            wallet_version=self.wallet_version,
            item_kind=kind,
            target=target,
            amount=amount,
            req_id=req_id,
            sender_address=account["address"],
            confirm_referer=urlsplit(page).path.lstrip("/"),
            gas_reserve_nanoton=self.gas_reserve_nanoton,
        )
        prepared.required_usdt_units = usdt_units
        return prepared, M.PaymentConfirmation(
            transaction=transaction, account=account, req_id=req_id,
            page_url=page, state_method=state_method,
        )

    async def purchase_stars(
        self, username: str, amount: int,
        show_sender: bool = True, payment_method: str = "gram",
    ) -> M.PurchaseResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Purchase Stars with a fee only on native TON principal."""
        integer(amount, C.STARS_PURCHASE_MIN, C.STARS_PURCHASE_MAX, ConfigurationError.INVALID_STARS_AMOUNT)
        return await self._single_purchase("stars", username, amount, show_sender, payment_method)

    async def purchase_premium(
        self, username: str, months: int,
        show_sender: bool = True, payment_method: str = "gram",
    ) -> M.PurchaseResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Gift Premium."""
        validate_months(months)
        return await self._single_purchase("premium", username, months, show_sender, payment_method)

    async def topup_gram(
        self, username: str, amount: int, show_sender: bool = True,
    ) -> M.PurchaseResult | M.PreparedTransaction:
        """Top up a recipient's Ads balance."""
        integer(amount, C.GRAM_TOPUP_MIN, C.GRAM_TOPUP_MAX, ConfigurationError.INVALID_GRAM_AMOUNT)
        return await self._single_purchase("ton", username, amount, show_sender, "ton")

    async def topup_ton(
        self, username: str, amount: int, show_sender: bool = True,
    ) -> M.PurchaseResult | M.PreparedTransaction:
        """Alias for native Ads top-up."""
        return await self.topup_gram(username, amount, show_sender)

    async def _single_purchase(
        self, kind: str, username: str, amount: int,
        show_sender: bool, payment_method: str,
    ) -> M.PurchaseResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Normalize one purchase receipt."""
        username = normalize_recipient(username)
        result = await self._purchase_flow(
            kind, username, amount,
            payment_method=payment_method, show_sender=show_sender,
        )
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        return M.PurchaseResult(
            transaction_id=receipt.tx_hash,
            type=kind,
            username=username,
            amount=amount,
            payment_method=normalize_payment_method(payment_method),
            operation_id=receipt.operation_id, confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
            req_id=req_id,
            confirmation_error=receipt.confirmation_error,
        )

    async def purchase(
        self,
        items_or_type: list[Any] | dict[str, Any] | M.PurchaseItem | str,
        username: str | None = None,
        amount: int | None = None,
        months: int | None = None,
        show_sender: bool = True,
        payment_method: str = "gram",
    ) -> M.PurchaseResult | M.PreparedTransaction | M.EvmPaymentResult | M.BatchResult:
        """Dispatch a single purchase or a batch sent in one wallet message."""
        if isinstance(items_or_type, list):
            return await self.batch_purchase(items_or_type, payment_method)
        if isinstance(items_or_type, M.PurchaseItem):
            item = items_or_type.model_dump()
        elif isinstance(items_or_type, dict):
            item = dict(items_or_type)
        elif isinstance(items_or_type, str):
            item = {
                "type": items_or_type, "username": username,
                "amount": amount, "months": months, "show_sender": show_sender,
            }
        else:
            raise ConfigurationError("Unsupported purchase input.")
        kind = item.get("type")
        target = item.get("username")
        sender = item.get("show_sender", True)
        if kind == "stars":
            return await self.purchase_stars(target, item.get("amount"), sender, payment_method)
        if kind == "premium":
            return await self.purchase_premium(target, item.get("months"), sender, payment_method)
        if kind in {"gram", "ton"}:
            if normalize_payment_method(payment_method) != "ton":
                raise ConfigurationError("Ads top-up requires native TON.")
            return await self.topup_gram(target, item.get("amount"), sender)
        raise ConfigurationError(f"Unsupported purchase type: {kind!r}")

    async def giveaway_stars(
        self, channel: str, winners: int, amount: int,
        payment_method: str = "gram",
    ) -> M.GiveawayStarsResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Run an original-limit total-package Stars giveaway."""
        stars_giveaway(amount, winners)
        return await self._giveaway(
            "giveaway_stars", channel, winners, amount, payment_method
        )

    async def giveaway_premium(
        self, channel: str, winners: int, months: int = 3,
        payment_method: str = "gram",
    ) -> M.GiveawayPremiumResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Run a Premium giveaway."""
        integer(winners, 1, 24_000, ConfigurationError.INVALID_WINNERS_PREMIUM)
        validate_months(months)
        return await self._giveaway(
            "giveaway_premium", channel, winners, months, payment_method
        )

    async def _giveaway(
        self, kind: str, channel: str, winners: int, amount: int, payment_method: str,
    ) -> M.GiveawayStarsResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Normalize giveaway receipts."""
        channel = normalize_recipient(channel)
        result = await self._purchase_flow(
            kind, channel, amount, winners=winners, payment_method=payment_method
        )
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        model = M.GiveawayStarsResult if kind == "giveaway_stars" else M.GiveawayPremiumResult
        return model(
            transaction_id=receipt.tx_hash, channel=channel,
            winners=winners, amount=amount,
            payment_method=normalize_payment_method(payment_method),
            operation_id=receipt.operation_id, confirmed=receipt.confirmed, fee_nanoton=receipt.fee_nanoton,
            req_id=req_id, confirmation_error=receipt.confirmation_error,
        )

    async def recharge_ads(self, account_id: str, amount: int) -> M.AdsRechargeResult | M.PreparedTransaction:
        """Recharge a specified Ads account."""
        integer(amount, 1, C.GRAM_TOPUP_MAX, ConfigurationError.INVALID_GRAM_AMOUNT)
        result = await self._purchase_flow("ads_recharge", account_id, amount)
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        return M.AdsRechargeResult(
            transaction_id=receipt.tx_hash, account_id=account_id, amount=amount,
            req_id=req_id, operation_id=receipt.operation_id, confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
            confirmation_error=receipt.confirmation_error,
        )

    async def recharge_gateway(self, account_id: str, credits: int) -> M.GatewayRechargeResult | M.PreparedTransaction:
        """Recharge a Gateway account."""
        integer(credits, 1, 10 ** 12, ConfigurationError.INVALID_CREDITS_AMOUNT)
        result = await self._purchase_flow("gateway", account_id, credits)
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        return M.GatewayRechargeResult(
            transaction_id=receipt.tx_hash, account_id=account_id, credits=credits,
            req_id=req_id, operation_id=receipt.operation_id, confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
            confirmation_error=receipt.confirmation_error,
        )

    async def get_gateway_price(self, account_id: str, credits: int) -> M.GatewayPriceInfo:
        """Quote Gateway credits."""
        integer(credits, 1, 10 ** 12, ConfigurationError.INVALID_CREDITS_AMOUNT)
        result = await self._api(
            "updateGatewayPrices", {"account": account_id, "credits": credits}, C.GATEWAY_PAGE
        )
        if result.get("price") is None:
            raise ParseError("Gateway quote did not contain a price.")
        return M.GatewayPriceInfo(
            credits=credits, gram_price=str(result["price"]),
            usd_price=str(result["usd_price"]) if result.get("usd_price") is not None else None,
        )
