"""Batch accounting and orchestration without blockchain/Fragment traffic."""

import time
from unittest.mock import AsyncMock

import pytest

from FragmentAPI import FragmentClient, PaymentConfirmation, PurchaseResult, TransactionResult
from FragmentAPI.exceptions import ConfigurationError, TransactionError
from FragmentAPI.storage.payments import SQLitePaymentStorage
from FragmentAPI.types.constants import FEE_ADDRESS, FEE_BASIS_POINTS
from FragmentAPI.utils.wallet import combine_prepared, prepare_transaction


def invoice(index: int, method: str = "ton", count: int = 1):
    prepared = prepare_transaction(
        {"transaction": {
            "validUntil": int(time.time()) + 300 - index,
            "messages": [{"address": FEE_ADDRESS, "amount": "1000000000"} for _ in range(count)],
        }}, payment_method=method, payment_nanoton=1_000_000_000 if method == "ton" else None,
        wallet_version="V5R1", item_kind="stars", target=f"target{index}", amount=100,
        req_id=f"request{index}", sender_address=FEE_ADDRESS,
    )
    if method == "usdt_ton":
        prepared.required_usdt_units = index * 1_000_000
    return prepared


def context(prepared):
    return PaymentConfirmation(
        transaction=prepared.raw, account={"address": FEE_ADDRESS},
        req_id=prepared.req_id, page_url="https://fragment.com/stars/buy",
        state_method="updateStarsBuyState",
    )


def test_combined_fee_capacity_and_single_reserve():
    invoices = [invoice(index) for index in range(1, 4)]
    combined = combine_prepared(invoices, "V4R2")
    assert len(combined.messages) == 4
    assert combined.fee_nanoton == sum(item.fee_nanoton for item in invoices)
    assert combined.fee_nanoton == 3_000_000_000 * FEE_BASIS_POINTS // 10_000
    assert combined.gas_reserve_nanoton == invoices[0].gas_reserve_nanoton
    assert combined.required_nanoton == sum(int(message.amount) for message in combined.messages) + combined.gas_reserve_nanoton
    assert combined.valid_until == min(item.valid_until for item in invoices)
    assert all(len(item.messages) == 2 for item in invoices)


def test_batch_over_capacity_is_rejected_without_splitting():
    with pytest.raises(TransactionError, match="Nothing was broadcast"):
        combine_prepared([invoice(index) for index in range(1, 5)], "V4R2")


def test_batch_sums_exact_usdt_without_fee():
    combined = combine_prepared([invoice(1, "usdt_ton"), invoice(2, "usdt_ton")], "V4R2")
    assert len(combined.messages) == 2
    assert combined.required_usdt_units == 3_000_000
    assert combined.fee_nanoton == 0


@pytest.mark.parametrize("change", ["sender", "method", "expiration", "duplicate", "units"])
def test_incompatible_or_expired_invoices_are_rejected(change):
    a, b = invoice(1), invoice(2)
    if change == "sender":
        b.sender_address = "different"
    elif change == "method":
        b.payment_method = "usdt_ton"
    elif change == "expiration":
        b.valid_until = int(time.time()) - 1
    elif change == "duplicate":
        b.req_id = a.req_id
    else:
        a.payment_method = b.payment_method = "usdt_ton"
    with pytest.raises(TransactionError):
        combine_prepared([a, b], "V4R2")


@pytest.mark.parametrize("bad", [[], [None], [{"type": "stars", "username": "target", "amount": True}]])
async def test_invalid_batch_never_prepares_or_sends(bad):
    client = FragmentClient()
    client._prepare_purchase = AsyncMock()
    with pytest.raises(ConfigurationError):
        await client.batch_purchase(bad)
    client._prepare_purchase.assert_not_awaited()


async def test_prepare_returns_one_external_signing_transaction():
    client = FragmentClient()
    invoices = [invoice(1), invoice(2)]
    client._prepare_purchase = AsyncMock(side_effect=[(item, context(item)) for item in invoices])
    result = await client.batch_purchase([
        {"type": "stars", "username": "target1", "amount": 100},
        {"type": "stars", "username": "target2", "amount": 100},
    ])
    assert result.chunks_sent == 0
    assert len(result.transaction.messages) == 3
    assert result.prepared_transactions == invoices
    assert all(item.status == "prepared" and item.chunk_index == 0 for item in result.items)


async def test_batch_broadcasts_once_and_confirms_every_invoice(monkeypatch, tmp_path):
    from FragmentAPI.methods import batches
    client = FragmentClient(payment_storage=SQLitePaymentStorage(tmp_path / "payments.db"))
    client.seed, client.api_key = "test-payer", "test-key"
    invoices = [invoice(1), invoice(2)]
    client._prepare_purchase = AsyncMock(side_effect=[(item, context(item)) for item in invoices])
    receipt = TransactionResult(tx_hash="one-hash", boc="signed", status="broadcast", operation_id="operation")
    send = AsyncMock(return_value=receipt)
    monkeypatch.setattr(batches, "execute_prepared", send)
    client._confirm = AsyncMock(side_effect=lambda transaction, receipt, *args: receipt)
    result = await client.batch_purchase([
        {"type": "stars", "username": "target1", "amount": 100},
        {"type": "stars", "username": "target2", "amount": 100},
    ])
    send.assert_awaited_once()
    assert len(send.await_args.args[1].messages) == 3
    assert len(send.await_args.kwargs["confirmations"]) == 2
    assert client._confirm.await_count == 2
    assert result.chunks_sent == 1
    assert all(isinstance(item.result, PurchaseResult) and item.result.transaction_id == "one-hash" for item in result.items)


async def test_preparation_failure_never_sends(monkeypatch):
    from FragmentAPI.methods import batches
    client = FragmentClient()
    client.seed, client.api_key = "test-payer", "test-key"
    first = invoice(1)
    client._prepare_purchase = AsyncMock(side_effect=[(first, context(first)), TransactionError("bad invoice")])
    send = AsyncMock()
    monkeypatch.setattr(batches, "execute_prepared", send)
    with pytest.raises(TransactionError, match="bad invoice"):
        await client.batch_purchase([
            {"type": "stars", "username": "target1", "amount": 100},
            {"type": "stars", "username": "target2", "amount": 100},
        ])
    send.assert_not_awaited()
