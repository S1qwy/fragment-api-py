'''
Fragment authentication utilities - TON proof and Telegram login
'''

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
import struct
import time
import urllib.parse
from typing import Any

import httpx
from nacl.signing import SigningKey
from tonsdk.crypto import mnemonic_to_wallet_key
from tonsdk.contract.wallet import Wallets, WalletVersionEnum

from FragmentAPI.exceptions import FragmentPageError, UnexpectedError
from FragmentAPI.types.constants import DEFAULT_TIMEOUT, FRAGMENT_BASE_URL, BASE_HEADERS


def _get_wallet_enum(version: str) -> WalletVersionEnum:
    '''Map version string to tonsdk enum.'''
    mapping = {
        "V4R2": WalletVersionEnum.v4r2,
        "V5R1": WalletVersionEnum.v4r2,
    }
    return mapping.get(version, WalletVersionEnum.v4r2)


def _parse_init_page(html: str) -> tuple[str, str]:
    '''Parse ajInit hash and ton_proof payload from Fragment homepage HTML.'''
    match_aj = re.search(r'ajInit\((.*?)\);', html)
    if not match_aj:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=FRAGMENT_BASE_URL)
        )
    aj_data = json.loads(match_aj.group(1))
    api_hash = aj_data.get("apiUrl", "").split("hash=")[-1]

    match_wallet = re.search(r'Wallet\.init\((.*?)\);', html)
    if not match_wallet:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=FRAGMENT_BASE_URL)
        )
    ton_proof_payload = json.loads(match_wallet.group(1)).get("ton_proof", "")

    return api_hash, ton_proof_payload


def _generate_proof(
    mnemonic: list[str],
    wallet_version: str,
    ton_proof_payload: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    '''Generate account_data, device_data, and proof_data for Fragment auth.'''
    public_key_bytes, private_key_bytes = mnemonic_to_wallet_key(mnemonic)

    wallet_enum = _get_wallet_enum(wallet_version)
    _, _, _, wallet = Wallets.from_mnemonics(mnemonic, wallet_enum, 0)
    raw_address = wallet.address.to_string(is_user_friendly=False)
    workchain, addr_hash_hex = raw_address.split(':')

    state_init_cell = wallet.create_state_init()['state_init']
    state_init_b64 = base64.b64encode(state_init_cell.to_boc(False)).decode('utf-8')

    domain = "fragment.com"
    timestamp = int(time.time())

    domain_bytes = domain.encode('utf-8')
    payload_bytes = ton_proof_payload.encode('utf-8')

    msg = b"ton-proof-item-v2/"
    msg += struct.pack(">i", int(workchain))
    msg += bytes.fromhex(addr_hash_hex)
    msg += struct.pack("<I", len(domain_bytes))
    msg += domain_bytes
    msg += struct.pack("<Q", timestamp)
    msg += payload_bytes

    msg_hash = hashlib.sha256(msg).digest()
    sign_payload = b'\xff\xff' + b'ton-connect' + msg_hash
    final_hash = hashlib.sha256(sign_payload).digest()

    signing_key = SigningKey(private_key_bytes[:32])
    signature = signing_key.sign(final_hash).signature
    signature_b64 = base64.b64encode(signature).decode('utf-8')

    account_data = {
        "address": raw_address,
        "chain": "-239",
        "walletStateInit": state_init_b64,
        "publicKey": public_key_bytes.hex(),
    }

    device_data = {
        "platform": "android",
        "appName": "Tonkeeper",
        "appVersion": "26.04.3",
        "maxProtocolVersion": 2,
        "features":[
            "SendTransaction",
            {"name": "SignData", "types": ["text", "binary", "cell"]},
            {"name": "SendTransaction", "maxMessages": 255},
        ],
    }

    proof_data = {
        "timestamp": timestamp,
        "domain": {
            "lengthBytes": len(domain_bytes),
            "value": domain,
        },
        "payload": ton_proof_payload,
        "signature": signature_b64,
    }

    return account_data, device_data, proof_data


def _fetch_tg_auth_result_sync(phone: str, timeout: float = 30.0) -> str:
    '''Perform Telegram OAuth flow via HTTP requests and polling (sync).'''
    bot_id = "5444323279"
    origin = "https://fragment.com"
    request_access = "write"
    return_to = "https://fragment.com/"
    
    base_params = f"?bot_id={bot_id}&origin={origin}&request_access={request_access}&return_to={return_to}"
    auth_url = f"https://oauth.telegram.org/auth{base_params}"
    request_url = f"https://oauth.telegram.org/auth/request{base_params}"
    login_url = f"https://oauth.telegram.org/auth/login{base_params}"
    push_url = f"https://oauth.telegram.org/auth/push{base_params}"
    
    with httpx.Client(timeout=timeout) as session:
        session.get(auth_url)
        
        resp_request = session.post(request_url, data={"phone": phone})
        resp_request.raise_for_status()
        
        login_success = False
        for _ in range(30):
            resp_login = session.post(login_url)
            try:
                if resp_login.json() is True:
                    login_success = True
                    break
            except Exception:
                pass
            time.sleep(3)
            
        if not login_success:
            raise UnexpectedError("Telegram login polling timed out. Please confirm login in Telegram.")
            
        session.get(auth_url)
        resp_push = session.get(push_url, follow_redirects=False)
        location = resp_push.headers.get("Location", "")
        
        match = re.search(r"#tgAuthResult=(.+)", location)
        if not match:
            raise UnexpectedError(f"Failed to extract tgAuthResult from redirect URL: {location}")
            
        return match.group(1)


async def _fetch_tg_auth_result_async(phone: str, timeout: float = 30.0) -> str:
    '''Perform Telegram OAuth flow via HTTP requests and polling (async).'''
    bot_id = "5444323279"
    origin = "https://fragment.com"
    request_access = "write"
    return_to = "https://fragment.com/"
    
    base_params = f"?bot_id={bot_id}&origin={origin}&request_access={request_access}&return_to={return_to}"
    auth_url = f"https://oauth.telegram.org/auth{base_params}"
    request_url = f"https://oauth.telegram.org/auth/request{base_params}"
    login_url = f"https://oauth.telegram.org/auth/login{base_params}"
    push_url = f"https://oauth.telegram.org/auth/push{base_params}"
    
    async with httpx.AsyncClient(timeout=timeout) as session:
        await session.get(auth_url)
        
        resp_request = await session.post(request_url, data={"phone": phone})
        resp_request.raise_for_status()
        
        login_success = False
        for _ in range(30):
            resp_login = await session.post(login_url)
            try:
                if resp_login.json() is True:
                    login_success = True
                    break
            except Exception:
                pass
            await asyncio.sleep(3)
            
        if not login_success:
            raise UnexpectedError("Telegram login polling timed out. Please confirm login in Telegram.")
            
        await session.get(auth_url)
        resp_push = await session.get(push_url, follow_redirects=False)
        location = resp_push.headers.get("Location", "")
        
        match = re.search(r"#tgAuthResult=(.+)", location)
        if not match:
            raise UnexpectedError(f"Failed to extract tgAuthResult from redirect URL: {location}")
            
        return match.group(1)


def authenticate_sync(
    seed: str,
    wallet_version: str = "V4R2",
    telegram_auth_data: str | None = None,
    telegram_phone: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, str]:
    '''Perform full Fragment authentication and return session cookies (sync).'''
    try:
        session = httpx.Client(timeout=timeout, follow_redirects=True)
        session.headers.update({
            "User-Agent": BASE_HEADERS["user-agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        session.cookies.set("stel_dt", "-180", domain="fragment.com")

        resp = session.get(f"{FRAGMENT_BASE_URL}/")
        resp.raise_for_status()

        api_hash, ton_proof_payload = _parse_init_page(resp.text)

        mnemonic = seed.strip().split()
        account_data, device_data, proof_data = _generate_proof(
            mnemonic, wallet_version, ton_proof_payload
        )

        form_data = {
            "account": json.dumps(account_data, separators=(',', ':')),
            "device": json.dumps(device_data, separators=(',', ':')),
            "proof": json.dumps(proof_data, separators=(',', ':')),
            "method": "checkTonProofAuth",
        }

        session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": FRAGMENT_BASE_URL,
            "Referer": f"{FRAGMENT_BASE_URL}/",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })

        api_url = f"{FRAGMENT_BASE_URL}/api?hash={api_hash}"
        auth_resp = session.post(api_url, data=form_data)
        auth_resp.raise_for_status()

        cookies = dict(session.cookies.jar)

        if "stel_token" not in cookies and (telegram_auth_data or telegram_phone):
            if telegram_phone:
                auth_base64 = _fetch_tg_auth_result_sync(telegram_phone, timeout)
            else:
                tg_json_clean = telegram_auth_data.replace('\/', '/')
                tg_url_encoded = urllib.parse.quote(tg_json_clean)
                auth_base64 = base64.b64encode(
                    tg_url_encoded.encode('utf-8')
                ).decode('utf-8')

            tg_form_data = {
                "auth": auth_base64,
                "method": "logIn",
            }
            tg_resp = session.post(api_url, data=tg_form_data)
            tg_resp.raise_for_status()
            cookies = dict(session.cookies.jar)

        session.close()
        return cookies

    except (FragmentPageError, UnexpectedError):
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc


async def authenticate(
    seed: str,
    wallet_version: str = "V4R2",
    telegram_auth_data: str | None = None,
    telegram_phone: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, str]:
    '''Perform full Fragment authentication and return session cookies (async).'''
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True
        ) as session:
            session.headers.update({
                "User-Agent": BASE_HEADERS["user-agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            session.cookies.set("stel_dt", "-180", domain="fragment.com")

            resp = await session.get(f"{FRAGMENT_BASE_URL}/")
            resp.raise_for_status()

            api_hash, ton_proof_payload = _parse_init_page(resp.text)

            mnemonic = seed.strip().split()
            account_data, device_data, proof_data = _generate_proof(
                mnemonic, wallet_version, ton_proof_payload
            )

            form_data = {
                "account": json.dumps(account_data, separators=(',', ':')),
                "device": json.dumps(device_data, separators=(',', ':')),
                "proof": json.dumps(proof_data, separators=(',', ':')),
                "method": "checkTonProofAuth",
            }

            session.headers.update({
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": FRAGMENT_BASE_URL,
                "Referer": f"{FRAGMENT_BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            })

            api_url = f"{FRAGMENT_BASE_URL}/api?hash={api_hash}"
            auth_resp = await session.post(api_url, data=form_data)
            auth_resp.raise_for_status()

            cookies = dict(session.cookies.jar)

            if "stel_token" not in cookies and (telegram_auth_data or telegram_phone):
                if telegram_phone:
                    auth_base64 = await _fetch_tg_auth_result_async(telegram_phone, timeout)
                else:
                    tg_json_clean = telegram_auth_data.replace('\/', '/')
                    tg_url_encoded = urllib.parse.quote(tg_json_clean)
                    auth_base64 = base64.b64encode(
                        tg_url_encoded.encode('utf-8')
                    ).decode('utf-8')

                tg_form_data = {
                    "auth": auth_base64,
                    "method": "logIn",
                }
                tg_resp = await session.post(api_url, data=tg_form_data)
                tg_resp.raise_for_status()
                cookies = dict(session.cookies.jar)

            return cookies

    except (FragmentPageError, UnexpectedError):
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc)
        ) from exc