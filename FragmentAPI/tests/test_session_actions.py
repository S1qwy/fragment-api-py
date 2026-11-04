from unittest.mock import AsyncMock
import pytest
from FragmentAPI import FragmentClient, FragmentAPIError, ConfigurationError

COOKIES={'stel_ssid':'ssid','stel_dt':'0','stel_token':'token','stel_ton_token':'ton'}

async def test_link_wallet_uses_existing_session():
    async with FragmentClient(cookies=COOKIES) as c:
        transport=c._get_transport()
        transport.call=AsyncMock(return_value={'ok':True})
        await c.link_wallet()
        transport.call.assert_awaited_once_with('linkWallet',None,'https://fragment.com/my/profile')
        assert c.has_ton_token

async def test_link_requires_connected_wallet():
    c=FragmentClient(cookies={k:v for k,v in COOKIES.items() if k!='stel_ton_token'})
    c.call=AsyncMock()
    with pytest.raises(ConfigurationError,match='stel_ton_token'):
        await c.link_wallet()
    c.call.assert_not_awaited()
    await c.aclose()

@pytest.mark.parametrize('method',['link_wallet','disconnect_wallet','logout'])
async def test_failed_actions_preserve_session(method):
    async with FragmentClient(cookies=COOKIES) as c:
        c.call=AsyncMock(return_value={'error':'Access denied'})
        with pytest.raises(FragmentAPIError):await getattr(c,method)()
        assert c.cookies==COOKIES

async def test_disconnect_preserves_account_and_persists():
    storage=AsyncMock()
    async with FragmentClient(cookies=COOKIES,session_storage=storage,session_id='own') as c:
        c._get_transport().call=AsyncMock(return_value={'ok':True})
        await c.disconnect_wallet()
        assert not c.has_ton_token
        assert c.cookies['stel_token']=='token'
        assert 'stel_ton_token' not in c._session.cookies.get_dict()
        assert 'stel_ton_token' not in storage.save.await_args.args[1]

async def test_logout_cannot_resurrect_persisted_cookies():
    storage=AsyncMock()
    c=FragmentClient(cookies=COOKIES,session_storage=storage,session_id='own')
    c._get_transport().call=AsyncMock(return_value={'ok':True})
    await c.logout()
    assert not c.cookies
    assert not c._session.cookies.get_dict()
    storage.delete.assert_awaited_once_with('own')
    await c.aclose()
    storage.save.assert_not_awaited()

async def test_link_requires_success_not_just_absence_of_error():
    async with FragmentClient(cookies=COOKIES) as c:
        c.call=AsyncMock(return_value={'need_verify':True})
        with pytest.raises(FragmentAPIError,match='not confirm'):await c.link_wallet()
