"""Current Fragment invoice responses prepare external payments without signing."""

from unittest.mock import AsyncMock

import pytest

from FragmentAPI import FragmentClient, PreparedTransaction
from FragmentAPI.methods.purchases import _FLOWS
from FragmentAPI.types.constants import FEE_ADDRESS


@pytest.mark.parametrize(
    ("kind", "amount", "winners", "expected_search"),
    [
        ("stars", 50, None, {"query": "recipient", "quantity": ""}),
        ("premium", 3, None, {"query": "recipient", "months": 3}),
        ("ton", 1, None, {"query": "recipient"}),
        ("giveaway_stars", 500, 1, {"query": "recipient"}),
        ("giveaway_premium", 3, 1, {"query": "recipient", "months": 3, "quantity": 1}),
    ],
)
async def test_current_invoice_prepares_without_broadcast(kind, amount, winners, expected_search):
    """Exercise search, initialization, link decoding, and the unsigned return path."""
    page, search, state, init, link = _FLOWS[kind]
    sender = {"address": FEE_ADDRESS, "chain": "-239", "publicKey": "0" * 64, "walletStateInit": ""}

    async def api(method, data, *, page_url):
        assert page_url == page
        if method == search:
            assert data == expected_search
            return {"ok": True, "found": {"recipient": "resolved", "name": "Recipient"}}
        if method == init:
            assert data["recipient"] == "resolved"
            if kind == "giveaway_stars":
                assert data == {"recipient": "resolved", "quantity": 1, "stars": 500, "payment_method": "ton"}
            return {"req_id": "invoice", "amount": "1.000000001"}
        if method == link:
            assert data["id"] == "invoice"
            assert data["transaction"] == 1
            return {
                "ok": True,
                "transaction": {"messages": [{"address": FEE_ADDRESS, "amount": "1000000001"}]},
                "confirm_method": "confirmReq", "confirm_params": {"id": "invoice"},
            }
        assert method in {state, "updateStarsGiveawayPrices", "updatePremiumGiveawayPrices"}
        return {"ok": True}

    async with FragmentClient(sender_account=sender) as client:
        client.call = AsyncMock(side_effect=api)
        client._confirm = AsyncMock()
        prepared = await client._purchase_flow(kind, "recipient", amount, winners=winners)
        assert isinstance(prepared, PreparedTransaction)
        assert prepared.req_id == "invoice"
        assert prepared.sender_address == FEE_ADDRESS
        assert prepared.payment_nanoton == 1_000_000_001
        assert prepared.fee_nanoton == 15_000_001
        assert len(prepared.messages) == 2
        assert prepared.raw["ok"] is True
        assert prepared.raw["confirm_method"] == "confirmReq"
        client._confirm.assert_not_awaited()
