import json
from unittest.mock import AsyncMock
import pytest
from FragmentAPI import FragmentClient,ConfigurationError,FragmentAPIError,KycRequiredError,ParseError
from FragmentAPI.methods.withdrawals import parse_withdrawal_url

COOKIES={'stel_ssid':'ssid','stel_dt':'0','stel_token':'token'}
URL='https://fragment.com/stars/withdraw?transaction=abc%2B123'

def page(kind='stars',**extra):
    state={'transaction':'abc+123','mode':'new',**({'withdrawalData':'opaque'} if kind=='stars' else {}),**extra}
    return '<form class="js-withdraw-form"><input name="amount" value="3.25"><input name="currency" value="TON"><input name="source" value="Channel"></form><script>ajInit('+json.dumps({'state':state})+');</script>'

@pytest.mark.parametrize('url',[
    'http://fragment.com/stars/withdraw?transaction=x',
    'https://fragment.com.evil.test/stars/withdraw?transaction=x',
    'https://fragment.com@evil.test/stars/withdraw?transaction=x',
    'https://fragment.com:444/stars/withdraw?transaction=x',
    'https://fragment.com/stars/withdraw?transaction=x&transaction=y',
    'https://fragment.com/stars/withdraw?transaction=',
    'https://fragment.com/gift/withdraw?transaction=x',
    'https://fragment.com/stars/withdraw?transaction=x#fragment',
    'https://fragment.com/stars/withdraw?transaction=x%0A',None,
])
def test_invalid_links_rejected(url):
    with pytest.raises(ConfigurationError):parse_withdrawal_url(url)

async def test_inspection_is_read_only():
    async with FragmentClient(cookies=COOKIES) as c:
        transport=c._get_transport()
        transport.get_text=AsyncMock(return_value=page())
        c.call=AsyncMock()
        info=await c.inspect_withdrawal(URL+'&ignored=other')
        assert info.transaction=='abc+123' and info.withdrawal_data=='opaque'
        assert info.amount=='3.25' and info.currency=='TON' and info.source=='Channel'
        assert info.kyc_required is None
        assert info.url==URL
        assert 'opaque' not in repr(info) and 'abc+123' not in repr(info)
        c.call.assert_not_awaited()

@pytest.mark.parametrize('state',[{'transaction':''},{'transaction':'other'},{'withdrawalData':None}])
async def test_expired_or_mismatched_page_rejected(state):
    async with FragmentClient(cookies=COOKIES) as c:
        c._get_transport().get_text=AsyncMock(return_value=page(**state))
        with pytest.raises(ParseError):await c.inspect_withdrawal(URL)

@pytest.mark.parametrize('kind',['stars','ads'])
async def test_prepare_then_confirm_requires_explicit_call(monkeypatch,kind):
    monkeypatch.setattr('FragmentAPI.methods.withdrawals.build_account_info',AsyncMock(return_value={'address':'destination'}))
    async with FragmentClient(cookies=COOKIES) as c:
        c._get_transport().get_text=AsyncMock(return_value=page(kind))
        c._withdraw=AsyncMock(side_effect=[{'confirm_hash':'secret','confirm_message':'Withdraw 3.25 TON?'},{'ok':True}])
        request=await c.prepare_withdrawal(URL.replace('/stars/','/'+kind+'/'))
        assert request.confirmation_required and request.destination=='destination'
        assert 'secret' not in repr(request)
        assert c._withdraw.await_count==1
        assert 'confirm_hash' not in c._withdraw.await_args.kwargs
        result=await c.confirm_withdrawal(request)
        assert result.ok
        assert c._withdraw.await_args.args[2]=='secret'
        with pytest.raises(ConfigurationError,match='already submitted'):await c.confirm_withdrawal(request)
        assert c._withdraw.await_count==2

async def test_page_kyc_blocks_initialization():
    async with FragmentClient(cookies=COOKIES) as c:
        c._get_transport().get_text=AsyncMock(return_value=page(need_verify=True,withdrawalData=None))
        c._withdraw=AsyncMock()
        assert (await c.inspect_withdrawal(URL)).kyc_required is True
        with pytest.raises(KycRequiredError):await c.prepare_withdrawal(URL)
        c._withdraw.assert_not_awaited()

@pytest.mark.parametrize('mode',['processing','done'])
async def test_existing_withdrawal_is_not_initialized_again(mode):
    async with FragmentClient(cookies=COOKIES) as c:
        c._get_transport().get_text=AsyncMock(return_value=page(mode=mode))
        c._withdraw=AsyncMock()
        with pytest.raises(ConfigurationError,match='already processing or done'):
            await c.prepare_withdrawal(URL)
        c._withdraw.assert_not_awaited()

async def test_changed_destination_and_uncertain_submission(monkeypatch):
    account=AsyncMock(return_value={'address':'destination'})
    monkeypatch.setattr('FragmentAPI.methods.withdrawals.build_account_info',account)
    async with FragmentClient(cookies=COOKIES) as c:
        c._get_transport().get_text=AsyncMock(return_value=page())
        c._withdraw=AsyncMock(return_value={'confirm_hash':'secret','confirm_message':'Review'})
        request=await c.prepare_withdrawal(URL)
        account.return_value={'address':'other'}
        with pytest.raises(ConfigurationError,match='changed'):await c.confirm_withdrawal(request)
        account.return_value={'address':'destination'}
        c._withdraw.side_effect=TimeoutError('Unknown outcome')
        with pytest.raises(TimeoutError):await c.confirm_withdrawal(request)
        with pytest.raises(ConfigurationError,match='already submitted'):await c.confirm_withdrawal(request)

async def test_no_challenge_is_not_automatically_replayed(monkeypatch):
    monkeypatch.setattr('FragmentAPI.methods.withdrawals.build_account_info',AsyncMock(return_value={'address':'destination'}))
    async with FragmentClient(cookies=COOKIES) as c:
        c._get_transport().get_text=AsyncMock(return_value=page())
        c._withdraw=AsyncMock(return_value={'ok':True,'mode':'processing'})
        request=await c.prepare_withdrawal(URL)
        assert not request.confirmation_required
        with pytest.raises(ConfigurationError):await c.confirm_withdrawal(request)
        c._withdraw.assert_awaited_once()
