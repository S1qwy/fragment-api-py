"""Prepare every invoice before sending one combined wallet message."""

from __future__ import annotations

from FragmentAPI.exceptions import BroadcastUncertainError, ConfigurationError
from FragmentAPI.types import constants as C
from FragmentAPI.types import models as M
from FragmentAPI.utils.validation import (
    integer, months, normalize_payment_method, recipient,
)
from FragmentAPI.utils.wallet import combine_prepared, execute_prepared


class BatchMixin:
    """A batch has one broadcast, without claiming atomic downstream fulfillment."""

    async def batch_purchase(
        self, items: list[dict | M.PurchaseItem], payment_method: str = "gram",
    ) -> M.BatchResult:
        """Validate and prepare all invoices, then send exactly one wallet message.

        No automatic splitting: a capacity, validation, or preparation failure
        sends nothing. Each invoice is confirmed independently after broadcast.
        """
        method = normalize_payment_method(payment_method)
        if method not in {"ton", "usdt_ton"}:
            raise ConfigurationError("Batch purchases support TON and USDT-TON.")
        if not isinstance(items, list) or not items:
            raise ConfigurationError("A batch must be a nonempty list of purchase items.")
        normalized: list[tuple[str, str, int, bool]] = []
        for raw in items:
            item = raw.model_dump() if isinstance(raw, M.PurchaseItem) else raw
            if not isinstance(item, dict):
                raise ConfigurationError("Every batch item must be a purchase object.")
            kind = item.get("type")
            target = recipient(item.get("username"))
            show = item.get("show_sender", True)
            if not isinstance(show, bool):
                raise ConfigurationError("show_sender must be a boolean.")
            if kind == "premium":
                value = months(item.get("months"))
            elif kind == "stars":
                value = integer(item.get("amount"), C.STARS_PURCHASE_MIN, C.STARS_PURCHASE_MAX, ConfigurationError.INVALID_STARS_AMOUNT)
            elif kind in {"ton", "gram"} and method == "ton":
                kind = "ton"
                value = integer(item.get("amount"), C.GRAM_TOPUP_MIN, C.GRAM_TOPUP_MAX, ConfigurationError.INVALID_GRAM_AMOUNT)
            else:
                raise ConfigurationError(f"Unsupported batch item type/payment combination: {kind!r}.")
            normalized.append((kind, target, value, show))

        async with self._flow_lock:
            invoices: list[M.PreparedTransaction] = []
            contexts: list[M.PaymentConfirmation] = []
            for kind, target, value, show in normalized:
                result = await self._prepare_purchase(
                    kind, target, value, payment_method=method, show_sender=show,
                )
                if not isinstance(result, tuple):
                    raise ConfigurationError("A TON batch cannot include an EVM invoice.")
                invoice, context = result
                invoices.append(invoice)
                contexts.append(context)
            combined = combine_prepared(invoices, self.wallet_version)
            model = M.NoKycBatchResult if self.wallet_auth else M.BatchResult
            if not self.has_wallet:
                return model(
                    total=len(items), succeeded=len(items), failed=0, chunks_sent=0,
                    transaction=combined, prepared_transactions=invoices,
                    items=[M.BatchItemResult(
                        type=kind, username=target, amount=value, ok=True,
                        result=invoice, status="prepared", chunk_index=0,
                    ) for (kind, target, value, _), invoice in zip(normalized, invoices)],
                )
            if not self.wallet_auth:
                self._require_ton_token()
            try:
                receipt = await execute_prepared(self, combined, confirmations=contexts)
            except BroadcastUncertainError as exc:
                if not exc.attempted:
                    raise
                record = await self.payment_storage.get(exc.operation_id) if exc.operation_id else None
                return model(
                    total=len(items), succeeded=0, failed=len(items), chunks_sent=0,
                    transaction=combined, operation_id=exc.operation_id,
                    receipt=record.receipt if record else None,
                    items=[M.BatchItemResult(
                        type=kind, username=target, amount=value, ok=False,
                        error=str(exc), status="unknown", chunk_index=0,
                    ) for kind, target, value, _ in normalized],
                )
            outcomes: list[M.BatchItemResult] = []
            for (kind, target, value, _), invoice, context in zip(normalized, invoices, contexts):
                item_receipt = receipt.model_copy(deep=True)
                item_receipt.payment_nanoton = invoice.payment_nanoton
                item_receipt.fee_nanoton = invoice.fee_nanoton
                item_receipt = await self._confirm(
                    context.transaction, item_receipt, context.account,
                    context.req_id, context.page_url, context.state_method,
                )
                outcomes.append(M.BatchItemResult(
                    type=kind, username=target, amount=value, ok=True, chunk_index=0,
                    status="confirmed" if item_receipt.confirmed else "broadcast",
                    result=M.PurchaseResult(
                        transaction_id=receipt.tx_hash, type=kind, username=target,
                        amount=value, payment_method=method, req_id=context.req_id,
                        confirmed=item_receipt.confirmed, fee_nanoton=invoice.fee_nanoton,
                        confirmation_error=item_receipt.confirmation_error,
                        operation_id=receipt.operation_id,
                    ),
                ))
            record = await self.payment_storage.get(receipt.operation_id)
            return model(
                total=len(items), succeeded=len(items), failed=0, chunks_sent=1,
                transaction=combined, receipt=record.receipt if record else receipt,
                operation_id=receipt.operation_id, items=outcomes,
            )
