"""Exercise durable broadcast boundaries, cancellation, and invoice correlation."""

import asyncio
import subprocess
import sys
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from FragmentAPI import FragmentClient, PaymentRecord
from FragmentAPI.exceptions import BroadcastUncertainError, ConfigurationError, SessionStorageError
from FragmentAPI.storage.payments import SQLitePaymentStorage
from FragmentAPI.tests.test_batches import context, invoice
from FragmentAPI.utils import wallet as wallets
from FragmentAPI.utils.locking import file_wallet_lock


@pytest.fixture
def setup_payment(monkeypatch, tmp_path):
    prepared = invoice(1)
    client = FragmentClient(payment_storage=SQLitePaymentStorage(tmp_path / "payments.db"))
    client.seed, client.api_key = "test-payer", "key"
    signed = SimpleNamespace(normalized_hash="hash", as_b64="signed-boc", as_hex="signed-hex")
    wallet = SimpleNamespace(
        address=SimpleNamespace(to_str=lambda **kwargs: wallets._raw_address(prepared.sender_address)),
        build_external_message=AsyncMock(return_value=signed),
    )
    ton = SimpleNamespace(get_info=AsyncMock(return_value=SimpleNamespace(balance=10**12)), send_message=AsyncMock())

    @asynccontextmanager
    async def provider():
        yield ton

    monkeypatch.setattr(wallets, "_make_ton_client", lambda client: provider())
    monkeypatch.setattr(wallets, "build_account_info", AsyncMock(return_value={"address": prepared.sender_address}))
    monkeypatch.setitem(wallets.WALLET_CLASSES, client.wallet_version, SimpleNamespace(from_mnemonic=lambda **kwargs: (wallet, None, None, None)))
    return client, prepared, wallet, ton


async def test_journal_has_signed_message_before_network_and_blocks_replay(setup_payment):
    client, prepared, wallet, ton = setup_payment

    async def send(value):
        entries = await client.list_payments()
        assert len(entries) == 1
        assert entries[0].state == "sending"
        assert entries[0].receipt.boc == "signed-boc"
        assert value == "signed-hex"

    ton.send_message.side_effect = send
    receipt = await wallets.execute_prepared(client, prepared, confirmations=[context(prepared)])
    record = await client.get_payment(receipt.operation_id)
    assert record.state == "broadcast"
    assert record.receipt.tx_hash == "hash"
    assert len(record.confirmations) == 1
    with pytest.raises(BroadcastUncertainError) as caught:
        await wallets.execute_prepared(client, prepared)
    assert caught.value.operation_id == receipt.operation_id
    ton.send_message.assert_awaited_once()


async def test_network_failure_keeps_boc_and_blocks_other_invoices(setup_payment):
    client, prepared, wallet, ton = setup_payment
    ton.send_message.side_effect = TimeoutError("connection lost")
    with pytest.raises(BroadcastUncertainError) as caught:
        await wallets.execute_prepared(client, prepared)
    record = await client.get_payment(caught.value.operation_id)
    assert record.state == "unknown" and record.receipt.boc == "signed-boc"
    with pytest.raises(BroadcastUncertainError):
        await wallets.execute_prepared(client, invoice(2))
    ton.send_message.assert_awaited_once()


async def test_cancel_during_send_is_durable_and_propagates(setup_payment):
    client, prepared, wallet, ton = setup_payment
    sending = asyncio.Event()

    async def send(value):
        sending.set()
        await asyncio.Event().wait()

    ton.send_message.side_effect = send
    task = asyncio.create_task(wallets.execute_prepared(client, prepared))
    await asyncio.wait_for(sending.wait(), 5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    records = await client.list_payments()
    assert records[0].state == "unknown"
    assert records[0].receipt.boc == "signed-boc"


async def test_journal_outage_prevents_broadcast(setup_payment):
    client, prepared, wallet, ton = setup_payment
    client.payment_storage.save = AsyncMock(side_effect=SessionStorageError("disk full"))
    with pytest.raises(SessionStorageError):
        await wallets.execute_prepared(client, prepared)
    ton.send_message.assert_not_awaited()


async def test_signing_failure_is_not_misreported_as_broadcast(setup_payment):
    client, prepared, wallet, ton = setup_payment
    wallet.build_external_message.side_effect = ConfigurationError("invalid payload")
    with pytest.raises(ConfigurationError):
        await wallets.execute_prepared(client, prepared)
    assert await client.list_payments() == []
    ton.send_message.assert_not_awaited()


async def test_unknown_recovery_never_rebroadcasts(setup_payment):
    client, prepared, wallet, ton = setup_payment
    ton.send_message.side_effect = TimeoutError()
    with pytest.raises(BroadcastUncertainError) as caught:
        await wallets.execute_prepared(client, prepared, confirmations=[context(prepared)])
    client._api = AsyncMock(side_effect=[{"ok": True}, {"mode": "done", "need_update": False}])
    with pytest.raises(BroadcastUncertainError):
        await client.reconcile_payment(caught.value.operation_id)
    ton.send_message.assert_awaited_once()


async def test_invoice_scoped_recovery_marks_fulfilled_without_paying_again(setup_payment):
    client, prepared, wallet, ton = setup_payment
    ton.send_message.side_effect = TimeoutError()
    with pytest.raises(BroadcastUncertainError) as caught:
        await wallets.execute_prepared(client, prepared, confirmations=[context(prepared)])
    client._api = AsyncMock(side_effect=[{"ok": True}, {"mode": "done", "need_update": False, "req_id": prepared.req_id}])
    recovered = await client.reconcile_payment(caught.value.operation_id)
    assert recovered.state == "confirmed"
    assert recovered.receipt.confirmed is True
    ton.send_message.assert_awaited_once()


async def test_operator_resolution_requires_evidence_and_does_not_claim_fulfillment(setup_payment):
    client, prepared, wallet, ton = setup_payment
    ton.send_message.side_effect = TimeoutError()
    with pytest.raises(BroadcastUncertainError) as caught:
        await wallets.execute_prepared(client, prepared)
    with pytest.raises(ConfigurationError):
        await client.resolve_payment(caught.value.operation_id, outcome="settled", evidence="")
    record = await client.resolve_payment(caught.value.operation_id, outcome="settled", evidence="Verified wallet transaction hash abc")
    assert record.state == "settled" and not record.receipt.confirmed
    assert record.resolution_evidence


async def test_shared_auth_wallet_cannot_be_a_payer():
    client = FragmentClient()
    with pytest.raises(ConfigurationError, match="shared authentication wallet"):
        await wallets.build_account_info(client)


async def test_journal_survives_new_storage_instance(tmp_path):
    path = tmp_path / "payments.db"
    prepared = invoice(1)
    record = PaymentRecord(operation_id="op", sender_address="sender", state="sending", prepared=prepared)
    await SQLitePaymentStorage(path).save(record)
    assert await SQLitePaymentStorage(path).get("op") == record
    assert await SQLitePaymentStorage(path).get("missing") is None


async def test_separate_wallet_locks_serialize_and_cancel_cleanly():
    entered = asyncio.Event()
    async def second():
        async with file_wallet_lock("test-lock-address"):
            entered.set()
    async with file_wallet_lock("test-lock-address"):
        waiting = asyncio.create_task(second())
        await asyncio.sleep(0.1)
        assert not entered.is_set()
        waiting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting
    await asyncio.wait_for(second(), 2)
    assert entered.is_set()


async def test_wallet_lock_is_shared_with_processes_and_released_after_crash():
    code = """
import asyncio
from FragmentAPI.utils.locking import file_wallet_lock
async def main():
    async with file_wallet_lock('test-process-wallet'):
        print('locked', flush=True)
        await asyncio.sleep(30)
asyncio.run(main())
"""
    child = subprocess.Popen(
        [sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    entered = asyncio.Event()
    async def acquire():
        async with file_wallet_lock("test-process-wallet"):
            entered.set()
    waiter = None
    try:
        line = await asyncio.wait_for(asyncio.to_thread(child.stdout.readline), 10)
        assert line.strip() == "locked"
        waiter = asyncio.create_task(acquire())
        await asyncio.sleep(0.15)
        assert not entered.is_set()
        child.kill()
        await asyncio.to_thread(child.wait, timeout=5)
        await asyncio.wait_for(waiter, 3)
        assert entered.is_set()
    finally:
        if child.poll() is None:
            child.kill()
            await asyncio.to_thread(child.wait, timeout=5)
        if waiter is not None and not waiter.done():
            waiter.cancel()
        child.stdout.close()
        child.stderr.close()


async def test_usdt_batch_checks_the_summed_balance_before_signing(setup_payment, monkeypatch):
    client, prepared, wallet, ton = setup_payment
    prepared.payment_method = "usdt_ton"
    prepared.required_usdt_units = 3_000_000
    monkeypatch.setattr(wallets, "_get_usdt_units", AsyncMock(return_value=2_000_000))
    from FragmentAPI.exceptions import WalletError
    with pytest.raises(WalletError, match="Insufficient USDT"):
        await wallets.execute_prepared(client, prepared)
    wallet.build_external_message.assert_not_awaited()
    ton.send_message.assert_not_awaited()


async def test_wallet_sequence_observation_is_not_purchase_confirmation(setup_payment):
    client, prepared, wallet, ton = setup_payment
    wallet.seqno = AsyncMock(side_effect=[5, 6])
    receipt = await wallets.execute_prepared(client, prepared)
    assert (receipt.seqno_before, receipt.seqno_after) == (5, 6)
    assert receipt.status == "broadcast" and not receipt.confirmed
    ton.send_message.assert_awaited_once()


async def test_sequence_timeout_blocks_a_second_send_until_resolved(setup_payment):
    client, prepared, wallet, ton = setup_payment
    client.timeout = 0.02
    wallet.seqno = AsyncMock(return_value=5)
    receipt = await wallets.execute_prepared(client, prepared)
    assert receipt.seqno_after is None
    assert receipt.confirmation_error
    with pytest.raises(BroadcastUncertainError) as caught:
        await wallets.execute_prepared(client, invoice(2))
    assert caught.value.operation_id == receipt.operation_id
    assert caught.value.attempted is False
    ton.send_message.assert_awaited_once()
