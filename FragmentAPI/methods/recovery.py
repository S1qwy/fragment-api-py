"""Recovery reads and reports existing payments; it never broadcasts a new one."""

from __future__ import annotations

from typing import Literal

from FragmentAPI.exceptions import BroadcastUncertainError, ConfigurationError
from FragmentAPI.types import models as M


class PaymentRecoveryMixin:
    """Inspect durable intent and resume confirmation with the original session."""

    async def get_payment(self, operation_id: str) -> M.PaymentRecord | None:
        """Return a journal entry, including a recoverable signed BOC."""
        return await self.payment_storage.get(operation_id)

    async def list_payments(self, sender_address: str | None = None) -> list[M.PaymentRecord]:
        """List local payment records; do not expose their BOCs in public logs."""
        return await self.payment_storage.list(sender_address)

    async def _save_confirmation(self, req_id: str, receipt: M.TransactionResult) -> None:
        if not receipt.operation_id:
            return
        record = await self.payment_storage.get(receipt.operation_id)
        if record is None:
            raise ConfigurationError("Payment journal entry is missing.")
        for context in record.confirmations:
            if context.req_id == req_id:
                context.receipt = receipt
        if record.confirmations and all(context.receipt and context.receipt.confirmed for context in record.confirmations):
            record.state = "confirmed"
            record.error = None
            record.receipt.confirmed = True
            record.receipt.status = "confirmed"
        elif record.state not in {"sending", "unknown", "settled", "not_broadcast"}:
            record.state = "broadcast"
        if record.receipt is not None:
            record.receipt.confirmation_error = receipt.confirmation_error
        await self.payment_storage.save(record)

    async def resolve_payment(
        self, operation_id: str, *, outcome: Literal["settled", "not_broadcast"], evidence: str,
    ) -> M.PaymentRecord:
        """Record an operator's independently verified chain result and unblock the payer.

        settled means the wallet message was processed, not that Fragment
        fulfilled every invoice. not_broadcast requires evidence that it cannot
        still execute (for example expiration AND absence on-chain). This method
        does not verify evidence or broadcast; keep the explorer reference/hash
        in the journal for audit. The original operation cannot be paid again.
        """
        if outcome not in {"settled", "not_broadcast"} or not isinstance(evidence, str) or not evidence.strip():
            raise ConfigurationError("A supported chain outcome and nonempty evidence are required.")
        initial = await self.payment_storage.get(operation_id)
        if initial is None:
            raise ConfigurationError("Payment journal entry is missing.")
        async with self._wallet_lock, self.wallet_lock_factory(initial.sender_address):
            record = await self.payment_storage.get(operation_id)
            if record.state == "confirmed":
                raise ConfigurationError("A fulfilled payment cannot be reclassified.")
            record.state = outcome
            record.resolution_evidence = evidence.strip()
            if outcome == "settled" and record.receipt is not None:
                record.receipt.status = "broadcast"
            await self.payment_storage.save(record)
            return record

    async def reconcile_payment(self, operation_id: str) -> M.PaymentRecord:
        """Report the recorded BOC and poll scoped invoice state, without paying again.

        Use the original Fragment cookies. An uncorrelated page state cannot
        resolve an uncertain broadcast; inspect its recorded message on-chain.
        """
        async with self._flow_lock:
            record = await self.payment_storage.get(operation_id)
            if record is None or record.receipt is None:
                raise ConfigurationError("No recoverable payment exists for this operation id.")
            if record.state in {"confirmed", "not_broadcast"}:
                return record
            async with self._wallet_lock, self.wallet_lock_factory(record.sender_address):
                for context in record.confirmations:
                    if context.receipt and context.receipt.confirmed:
                        continue
                    receipt = record.receipt.model_copy(deep=True)
                    await self._confirm(
                        context.transaction, receipt, context.account,
                        context.req_id, context.page_url, context.state_method,
                    )
                record = await self.payment_storage.get(operation_id)
                if record.state in {"sending", "unknown"}:
                    raise BroadcastUncertainError(
                        "No invoice-scoped fulfillment evidence was returned; inspect the recorded message on-chain.",
                        operation_id=operation_id,
                    )
                return record
