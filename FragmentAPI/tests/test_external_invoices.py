"""Network-specific invoices and the unified public purchase API."""
import json
from unittest.mock import AsyncMock
import pytest
from FragmentAPI import FragmentClient, ExternalInvoice
from FragmentAPI.exceptions import FragmentAPIError
from FragmentAPI.utils.external import _fetch
from FragmentAPI.utils.validation import normalize_payment_method


@pytest.mark.parametrize(('method','network','chain'), [('usdt_tron','tron',728126428),('usdt_eth','evm',1),('usdt_pol','evm',137),('usdc_base','evm',8453)])
async def test_external_invoice_networks(monkeypatch,method,network,chain):
    state={'invoiceReqId':'id','invoiceAddress':'recipient','invoiceToken':'contract','invoiceChainId':chain,'invoiceNetwork':network,'invoiceAmount':'0x362b30','invoiceTokenDecimals':6}
    monkeypatch.setattr('FragmentAPI.utils.external.FragmentTransport.get_text',AsyncMock(return_value='ajInit('+json.dumps({'state':state})+');'))
    invoice=await _fetch(None,'https://fragment.com/stars/buy',method)
    assert isinstance(invoice,ExternalInvoice)
    assert invoice.invoice_amount_raw==3550000
    assert invoice.invoice_network==network
    assert invoice.invoice_chain_name==('TRON' if network=='tron' else {'usdt_eth':'ETH','usdt_pol':'POL','usdc_base':'BASE'}[method])


async def test_tron_network_mismatch_rejected(monkeypatch):
    state={'invoiceReqId':'id','invoiceAddress':'recipient','invoiceToken':'contract','invoiceChainId':1,'invoiceNetwork':'evm','invoiceAmount':'0x01'}
    monkeypatch.setattr('FragmentAPI.utils.external.FragmentTransport.get_text',AsyncMock(return_value='ajInit('+json.dumps({'state':state})+');'))
    with pytest.raises(FragmentAPIError,match='network'):
        await _fetch(None,'https://fragment.com/stars/buy','usdt_tron')


@pytest.mark.parametrize("chain_id", [56, 1])
async def test_bsc_invoice_without_explicit_precision(monkeypatch, chain_id):
    state = {
        "invoiceReqId": "id",
        "invoiceAddress": "recipient",
        "invoiceToken": "0x55d398326f99059ff775485246999027b3197955",
        "invoiceChainId": chain_id,
        "invoiceNetwork": "evm",
        "invoiceAmount": "0xa688906bd8b0000",
    }
    monkeypatch.setattr(
        "FragmentAPI.utils.external.FragmentTransport.get_text",
        AsyncMock(return_value="ajInit(" + json.dumps({"state": state}) + ");"),
    )
    url = "https://fragment.com/stars/buy"
    if chain_id != 56:
        with pytest.raises(FragmentAPIError, match="network"):
            await _fetch(None, url, "usdt_bsc")
        return
    invoice = await _fetch(None, url, "usdt_bsc")
    assert invoice.invoice_chain_name == "BSC"
    assert invoice.token_symbol == "USDT"
    assert invoice.token_decimals == 18
    assert invoice.invoice_amount_raw == 750_000_000_000_000_000
    assert invoice.invoice_amount == 0.75


def test_removed_purchase_adapters():
    for name in ('purchase_stars','purchase_premium','topup_gram','topup_ton','batch_purchase','list_sessions'):
        assert not hasattr(FragmentClient,name)
    assert normalize_payment_method('usdt_tron')=='usdt_tron'


async def test_external_flow_initializes_payment_link(monkeypatch):
    from FragmentAPI.methods import purchases
    invoice=ExternalInvoice(req_id='id',invoice_address='address',invoice_token='token',invoice_chain_id=728126428,invoice_chain_name='TRON',invoice_network='tron',invoice_amount_hex='0x01',invoice_amount_raw=1,invoice_amount=.000001,token_symbol='USDT',token_decimals=6,expires_at=0,payment_method='usdt_tron',page_url='https://fragment.com/stars/buy')
    methods=[]
    async def call(method,data,**kwargs):
        methods.append(method)
        if method=='searchStarsRecipient':return {'found':{'recipient':'resolved'}}
        if method=='initBuyStarsRequest':return {'req_id':'id'}
        return {'ok':True}
    async def fetch(*args,**kwargs):
        assert methods[-1]=='getBuyStarsLink'
        return invoice
    monkeypatch.setattr(purchases,'fetch_external_invoice',fetch)
    async with FragmentClient() as client:
        client.call=AsyncMock(side_effect=call)
        result=await client.purchase('stars','recipient',50,payment_method='usdt_tron')
        assert result.invoice is invoice
        assert not client.has_wallet
