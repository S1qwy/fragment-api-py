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
        ("terminate_session", ("session",)),
        ("get_my_assets", ()),
        ("get_my_bids", ()),
        ("get_login_code", ("88812345678",)),
        ("terminate_sessions", ("88812345678",)),
    ],
)
async def test_missing_cookies_blocks_account_access(method: str, arguments: tuple) -> None:
    """Reject account operations before any network access."""
    client = FragmentClient()
    with pytest.raises(ConfigurationError):
        await getattr(client, method)(*arguments)
    await client.aclose()


async def test_raw_call_cannot_override_method() -> None:
    """Require cookies even through the raw interface."""
    client = FragmentClient()
    with pytest.raises(ConfigurationError):
        await client.call("tonTerminateSession", {"session_id": "session"})
    await client.aclose()


@pytest.mark.parametrize("method", ["searchAuctions", "searchStarsRecipient", "initBuyStarsRequest"])
async def test_no_implicit_authentication_without_cookies(method, monkeypatch) -> None:
    """A payer or public operation must never trigger automatic wallet proof."""
    from FragmentAPI import client as module
    proof = AsyncMock()
    monkeypatch.setattr(module, "auth_ton_proof", proof)
    async with FragmentClient() as client:
        client.seed = "user-owned-seed"
        client._get_transport().call = AsyncMock()
        with pytest.raises(ConfigurationError, match="cookies"):
            await client.call(method)
        proof.assert_not_awaited()
        client._get_transport().call.assert_not_awaited()


@pytest.mark.parametrize("option", ["shared_auth_seed", "wallet_auth"])
def test_removed_shared_mode_options_are_rejected(option) -> None:
    with pytest.raises(TypeError):
        FragmentClient(**{option: True})


async def test_explicit_cookie_session_can_call_account_methods() -> None:
    async with FragmentClient(cookies={"stel_ssid": "ssid", "stel_dt": "0", "stel_token": "token"}) as client:
        transport = client._get_transport()
        transport.call = AsyncMock(return_value={"ok": True})
        assert await client.call("tonTerminateSession", {"session_id": "session"}) == {"ok": True}
        assert not hasattr(client, "wallet_auth")
        assert not hasattr(client, "nokyc_mode")


def test_shared_identity_is_not_exported() -> None:
    import FragmentAPI
    from FragmentAPI.types import constants
    assert not hasattr(constants, "SHARED_AUTH_SEED")
    assert not hasattr(constants, "SHARED_AUTH_WALLET_VERSION")
    assert not hasattr(constants, "WALLET_AUTH_ALLOWED_METHODS")
    assert not hasattr(FragmentAPI, "NoKycBatchResult")


async def test_refresh_requires_user_seed_without_proof_call(monkeypatch) -> None:
    from FragmentAPI import client as module
    proof = AsyncMock()
    monkeypatch.setattr(module, "auth_ton_proof", proof)
    async with FragmentClient() as client:
        with pytest.raises(ConfigurationError, match="seed"):
            await client.refresh_cookies()
        proof.assert_not_awaited()


async def test_refresh_uses_only_caller_seed_and_persists_session(monkeypatch) -> None:
    from FragmentAPI import client as module
    cookies = {"stel_ssid": "ssid", "stel_dt": "0", "stel_token": "token", "stel_ton_token": "ton"}
    proof = AsyncMock(return_value=cookies)
    monkeypatch.setattr(module, "auth_ton_proof", proof)
    storage = AsyncMock()
    async with FragmentClient(
        cookies=cookies, wallet_version="V4R2", session_storage=storage, session_id="own",
    ) as client:
        client.seed = "caller-seed"
        assert await client.refresh_cookies() == cookies
        assert proof.await_args.args[:2] == ("caller-seed", "V4R2")
        assert proof.await_args.kwargs["session"] is client._session
        storage.save.assert_awaited_once_with("own", cookies, {"mode": "cookies"})


async def test_profile_reads_full_home_page() -> None:
    """The AJAX body omits account details from the shared page header."""
    client = FragmentClient(
        cookies={"stel_ssid": "ssid", "stel_dt": "0", "stel_token": "token"}
    )
    transport = client._get_transport()
    transport.get_text = AsyncMock(return_value='''
        <div class="tm-menu-tg-account"><div class="tm-menu-tg-account-name">Alice</div></div>
        <script>Wallet.init({"address":"0:123"});</script>
    ''')
    result = await client.get_profile()
    assert result.name == "Alice"
    assert result.wallet_address == "0:123"
    transport.get_text.assert_awaited_once_with("https://fragment.com/my/profile")
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
        await client.purchase("ton", "recipient", True)
    with pytest.raises(ConfigurationError):
        await client.giveaway_premium("channel", True, 3)
    await client.aclose()
