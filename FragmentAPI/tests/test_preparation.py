"""Prepared transaction accounting tests."""

import time

import pytest

from FragmentAPI.exceptions import TransactionError
from FragmentAPI.types.constants import FEE_ADDRESS
from FragmentAPI.utils.wallet import prepare_transaction


def payload(amount: int = 1_100_000_000) -> dict:
    """Build a native transfer fixture with an additional attached reserve."""
    return {
        "transaction": {
            "validUntil": int(time.time()) + 300,
            "messages": [{"address": FEE_ADDRESS, "amount": str(amount)}],
        }
    }


def test_native_fee_excludes_attached_gas() -> None:
    """Charge the quoted principal, not every attached nanoton."""
    original = payload()
    result = prepare_transaction(
        original,
        payment_method="ton",
        payment_nanoton=1_000_000_000,
        wallet_version="V5R1",
        item_kind="stars",
        target="recipient",
        amount=100,
        gas_reserve_nanoton=50_000_000,
    )
    assert result.fee_nanoton == 5_000_000
    assert result.required_nanoton == 1_155_000_000
    assert len(result.messages) == 2
    assert len(original["transaction"]["messages"]) == 1


def test_usdt_has_no_native_fee() -> None:
    """Never append a percentage fee to USDT gas messages."""
    result = prepare_transaction(
        payload(100_000_000),
        payment_method="usdt_ton",
        payment_nanoton=None,
        wallet_version="V5R1",
        item_kind="stars",
        target="recipient",
        amount=100,
    )
    assert result.fee_nanoton == 0
    assert len(result.messages) == 1


def test_native_principal_is_required() -> None:
    """Do not estimate native principal from potentially gas-bearing messages."""
    with pytest.raises(TransactionError):
        prepare_transaction(
            payload(),
            payment_method="ton",
            payment_nanoton=None,
            wallet_version="V5R1",
            item_kind="stars",
            target="recipient",
            amount=100,
        )


def test_fee_consumes_wallet_message_capacity() -> None:
    """Include the extra fee message in V4 capacity checks."""
    data = payload()
    data["transaction"]["messages"] *= 4
    with pytest.raises(TransactionError):
        prepare_transaction(
            data,
            payment_method="ton",
            payment_nanoton=1_000_000_000,
            wallet_version="V4R2",
            item_kind="stars",
            target="recipient",
            amount=100,
        )