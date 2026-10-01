"""Client capability and lifecycle tests without live payments."""

from unittest.mock import AsyncMock

import pytest

from FragmentAPI import FragmentClient
from FragmentAPI.exceptions import ConfigurationError


@pytest.mark.parametrize(
    ("method", "arguments"),
    [
        ("get_profile", ()),
        ("get_sessions", ()),
        ("list_sessions", ()),
        ("terminate_session", ("session",)),
        ("get_my_assets", ()),
        ("get_my_bids", ()),
        ("get_login_code", ("88812345678",)),
        ("terminate_sessions", ("88812345678",)),
    ],
)
async def test_wallet_auth_blocks_account_access(method: str, arguments: tuple) -> None:
    """Reject account operations before attempting shared authentication."""
    client = FragmentClient()
    with pytest.raises(ConfigurationError):
        await getattr(client, method)(*arguments)
    await client.aclose()


async def test_raw_call_cannot_override_method() -> None:
    """Block restricted methods even through the raw interface."""
    client = FragmentClient()
    with pytest.raises(ConfigurationError):
        await client.call("tonTerminateSession", {"session_id": "session"})
    await client.aclose()


async def test_session_reused_and_closed() -> None:
    """Reuse one transport and close its owned session exactly once."""
    client = FragmentClient(
        cookies={"stel_ssid": "ssid", "stel_dt": "0", "stel_token": "token"}
    )
    first = client._get_transport()
    assert client._get_transport() is first
    first.session.close = AsyncMock()
    await client.aclose()
    await client.aclose()
    first.session.close.assert_awaited_once()


async def test_bool_purchase_rejected_before_network() -> None:
    """Reject bool quantities before authentication or HTTP."""
    client = FragmentClient()
    with pytest.raises(ConfigurationError):
        await client.topup_gram("recipient", True)
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("channel", True, 3)
    await client.aclose()