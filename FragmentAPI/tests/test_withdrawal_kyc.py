from unittest.mock import AsyncMock
import pytest
from FragmentAPI import FragmentClient, KycRequiredError
from FragmentAPI.utils.html import parse_profile

@pytest.mark.parametrize('verified',[True,False])
def test_restored_profile_scopes_verification(verified):
    badge='tm-badge-verified' if verified else 'tm-badge-unverified'
    html=f'''<div class="tm-settings-item tm-settings-head-item"><span class="tm-settings-account-photo"><img src="alice.jpg"></span><div class="tm-settings-item-head">Alice</div><div class="tm-settings-item-desc">@alice</div><span class="{badge}">Status</span></div><div class="tm-settings-head-item"><span class="tm-wallet">UQwallet</span><span class="tm-badge-verified">Verified</span></div><script>Wallet.init({{"address":"0:123"}});</script>'''
    p=parse_profile(html)
    assert p.username=='alice'
    assert p.identity_verified is verified
    assert p.wallet_verified is True
    assert p.wallet_label=='UQwallet'

@pytest.mark.parametrize('method',['initStarsRevenueWithdrawalRequest','initAdsRevenueWithdrawalRequest'])
@pytest.mark.parametrize('confirm_hash',[None,'challenge'])
async def test_revenue_withdrawal_requires_kyc(monkeypatch,method,confirm_hash):
    monkeypatch.setattr('FragmentAPI.client.build_account_info',AsyncMock(return_value={'address':'destination'}))
    async with FragmentClient(cookies={'stel_ssid':'ssid','stel_dt':'0','stel_token':'token'}) as client:
        client.call=AsyncMock(return_value={'need_verify':True,'popup':'Verification required'})
        with pytest.raises(KycRequiredError):
            await client._withdraw(method,'transaction',confirm_hash)
        client.call.assert_awaited_once()

async def test_verified_withdrawal_preserves_confirmation(monkeypatch):
    monkeypatch.setattr('FragmentAPI.client.build_account_info',AsyncMock(return_value={'address':'destination'}))
    async with FragmentClient(cookies={'stel_ssid':'ssid','stel_dt':'0','stel_token':'token'}) as client:
        client.call=AsyncMock(return_value={'ok':True,'confirm_hash':'challenge'})
        result=await client.init_stars_withdrawal('transaction','opaque')
        assert result.ok and result.confirm_hash=='challenge'
