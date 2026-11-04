import pytest
from ton_core import MnemonicType
from tonutils.contracts.wallet import WalletTg,WalletV5R1
from FragmentAPI import FragmentClient,ConfigurationError
from FragmentAPI.utils.auth import OfflineClient,derive_account,_generate_proof
from FragmentAPI.utils.validation import normalize_seed

# Public BIP-39 test vector, never used for network operations.
BIP39='abandon '*11+'about'

def test_multichain_is_explicit_for_ordinary_wallets():
    with pytest.raises(ConfigurationError):normalize_seed(BIP39)
    assert normalize_seed(BIP39,'V5R1','multichain')==BIP39
    expected=WalletV5R1.from_mnemonic(OfflineClient(),BIP39,mnemonic_type=MnemonicType.MULTICHAIN)[0]
    assert derive_account(BIP39,'V5R1','multichain')['address']==expected.address.to_str(is_user_friendly=False)

def test_telegram_wallet_uses_bip39_and_supports_rotation():
    expected=WalletTg.from_mnemonic(OfflineClient(),BIP39)[0]
    account=derive_account(BIP39,'WalletTg')
    rotated=derive_account(BIP39+' '+BIP39,'WalletTg')
    assert account['address']==rotated['address']==expected.address.to_str(is_user_friendly=False)
    proof_account,_,proof=_generate_proof(BIP39.split(),'WalletTg','challenge')
    assert proof_account==account
    assert proof['payload']=='challenge'

@pytest.mark.parametrize('scheme',['invalid',True,'ton'])
def test_telegram_wallet_rejects_wrong_scheme(scheme):
    with pytest.raises(ConfigurationError):FragmentClient(seed=BIP39,wallet_version='WalletTg',mnemonic_type=scheme)

@pytest.mark.parametrize('count',[15,21])
@pytest.mark.parametrize('scheme',[MnemonicType.TON,MnemonicType.MULTICHAIN])
def test_supported_phrase_lengths(count,scheme):
    words=WalletV5R1.create(OfflineClient(),mnemonic_length=count,mnemonic_type=scheme)[3]
    assert normalize_seed(' '.join(words),'V5R1',scheme)==' '.join(words)

def test_checksum_is_not_just_word_count():
    with pytest.raises(ConfigurationError):normalize_seed('abandon '*12,'V5R1','multichain')
