"""Wallet contract capability tests."""

import time
from typing import Any

import pytest
from ton_core import WalletHighloadV2Params, WalletHighloadV3Params
from tonutils.contracts.wallet import WalletTg

from FragmentAPI.exceptions import WalletError
from FragmentAPI.types.constants import (
    FEE_ADDRESS,
    WALLET_CLASSES,
    WALLET_MAX_MESSAGES,
)
from FragmentAPI.utils import wallet as wallet_module
from FragmentAPI.utils.wallet import (
    HIGHLOAD_BIT_NUMBER_MASK,
    HIGHLOAD_QUERY_ID_SPACE,
    build_wallet_params,
    next_highload_query_id,
    prepare_transaction,
)


def test_message_limits_follow_the_contracts() -> None:
    """Derive every capacity from the installed wallet contract."""
    assert WALLET_MAX_MESSAGES == {
        name: contract.MAX_MESSAGES for name, contract in WALLET_CLASSES.items()
    }
    assert WALLET_MAX_MESSAGES["V4R2"] == 4
    assert WALLET_MAX_MESSAGES["HighloadV2"] == 254
    assert WALLET_MAX_MESSAGES["HighloadV3R1"] == 64516
    assert WALLET_MAX_MESSAGES["WalletTg"] == 255
    assert WALLET_CLASSES["WalletTg"] is WalletTg


def test_highload_query_ids_are_unique_and_accepted() -> None:
    """Skip the reserved bit number and never reuse a live query id."""
    seen: set[int] = set()
    for _ in range(5_000):
        query_id = next_highload_query_id()
        assert 0 <= query_id < HIGHLOAD_QUERY_ID_SPACE
        assert query_id & HIGHLOAD_BIT_NUMBER_MASK != HIGHLOAD_BIT_NUMBER_MASK
        assert query_id not in seen
        seen.add(query_id)


def test_highload_v3_params_are_fresh() -> None:
    """Carry a contract-valid creation timestamp and a fresh query id."""
    params = build_wallet_params("HighloadV3R1")
    other = build_wallet_params("HighloadV3R1")
    assert isinstance(params, WalletHighloadV3Params)
    assert isinstance(other, WalletHighloadV3Params)
    now = int(time.time())
    assert params.created_at is not None and params.created_at <= now
    assert params.created_at > now - 300
    assert params.query_id is not None
    assert params.query_id != other.query_id


def test_highload_v2_params_are_allocated() -> None:
    """Allocate a bounded identifier the contract can index."""
    params = build_wallet_params("HighloadV2")
    assert isinstance(params, WalletHighloadV2Params)
    assert params.bounded_id is not None and params.bounded_id > 0


@pytest.mark.parametrize("version", ["V4R2", "V5R1", "WalletTg"])
def test_other_wallets_need_no_params(version: str) -> None:
    """Only highload contracts accept broadcast-time query parameters."""
    assert build_wallet_params(version) is None


def test_unhandled_highload_version_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse default parameters when a new highload contract appears."""
    monkeypatch.setattr(
        wallet_module, "HIGHLOAD_WALLET_VERSIONS", frozenset({"HighloadV4R2"})
    )
    with pytest.raises(WalletError):
        build_wallet_params("HighloadV4R2")
    assert build_wallet_params("V5R1") is None


class _RecordingWallet:
    """Wallet double that records the parameters it was called with."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    async def transfer_message(self, message: Any, params: Any = None) -> str:
        self.calls.append(("single", params))
        return "single-hash"

    async def batch_transfer_message(self, messages: Any, params: Any = None) -> str:
        self.calls.append(("batch", params))
        return "batch-hash"


def _prepared(count: int) -> Any:
    """Build a fee-free native invoice carrying exactly the requested messages."""
    data = {
        "transaction": {
            "validUntil": int(time.time()) + 300,
            "messages": [
                {"address": FEE_ADDRESS, "amount": "1000000"} for _ in range(count)
            ],
        }
    }
    return prepare_transaction(
        data,
        payment_method="ton",
        payment_nanoton=0,
        wallet_version="HighloadV3R1",
        item_kind="stars",
        target="recipient",
        amount=100,
    )


async def test_transfer_forwards_highload_params() -> None:
    """Hand the allocated parameters to whichever message API is available."""
    params = build_wallet_params("HighloadV3R1")
    wallet = _RecordingWallet()

    assert await wallet_module._transfer(wallet, _prepared(1), params) == "single-hash"
    assert wallet.calls[-1] == ("single", params)

    assert await wallet_module._transfer(wallet, _prepared(3), params) == "batch-hash"
    assert wallet.calls[-1] == ("batch", params)
