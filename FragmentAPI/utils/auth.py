'''
Fragment authentication utilities — TON proof and Telegram OAuth (QR/phone).
Async only.
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

from FragmentAPI.exceptions import (
    FragmentPageError,
    UnexpectedError,
)
from FragmentAPI.types.constants import (
    BASE_HEADERS,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
    WALLET_CLASSES,
)

TELEGRAM_CLIENT_ID = "5444323279"
TELEGRAM_OAUTH_BASE = "https://oauth.telegram.org"

TELEGRAM_BASE_PARAMS = (
    f"client_id={TELEGRAM_CLIENT_ID}"
    f"&origin=https%3A%2F%2Ffragment.com"
    f"&return_to=https%3A%2F%2Ffragment.com%2F"
    f"&scope=openid%20profile%20telegram%3Abot_access"
    f"&redirect_uri=https%3A%2F%2Ffragment.com%2F"
    f"&response_type=post_message"
)

BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def _parse_init_page(html: str) -> tuple[str, str]:
    '''Parse ajInit hash and ton_proof payload from Fragment homepage HTML.'''
    match_aj = re.search(r"ajInit\((.*?)\);", html)
    if not match_aj:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=FRAGMENT_BASE_URL),
        )
    aj_data = json.loads(match_aj.group(1))
    api_hash = aj_data.get("apiUrl", "").split("hash=")[-1]

    match_wallet = re.search(r"Wallet\.init\((.*?)\);", html)
    if not match_wallet:
        raise FragmentPageError(
            FragmentPageError.HASH_NOT_FOUND.format(url=FRAGMENT_BASE_URL),
        )
    ton_proof_payload = json.loads(
        match_wallet.group(1),
    ).get("ton_proof", "")

    return api_hash, ton_proof_payload


def _generate_proof(
    mnemonic: list[str],
    wallet_version: str,
    ton_proof_payload: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    '''Generate TON proof data for Fragment authentication.'''

    wallet_cls = WALLET_CLASSES.get(
        wallet_version.upper(),
        WALLET_CLASSES["V5R1"],
    )

    wallet, pub_key, priv_key, _ = wallet_cls.from_mnemonic(
        client=None,
        mnemonic=" ".join(mnemonic),
    )

    raw_address = wallet.address.to_str(is_user_friendly=False)
    workchain, addr_hash_hex = raw_address.split(":")

    state_init_boc = wallet.state_init.serialize().to_boc()
    state_init_b64 = base64.b64encode(state_init_boc).decode("utf-8")

    domain = "fragment.com"
    timestamp = int(time.time())

    domain_bytes = domain.encode("utf-8")
    payload_bytes = ton_proof_payload.encode("utf-8")

    msg = b"ton-proof-item-v2/"
    msg += struct.pack(">i", int(workchain))
    msg += bytes.fromhex(addr_hash_hex)
    msg += struct.pack("<I", len(domain_bytes))
    msg += domain_bytes
    msg += struct.pack("<Q", timestamp)
    msg += payload_bytes

    msg_hash = hashlib.sha256(msg).digest()
    sign_payload = b"\xff\xff" + b"ton-connect" + msg_hash
    final_hash = hashlib.sha256(sign_payload).digest()

    signing_key = SigningKey(priv_key[:32])
    signature = signing_key.sign(final_hash).signature
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    account_data = {
        "address": raw_address,
        "chain": "-239",
        "walletStateInit": state_init_b64,
        "publicKey": pub_key.hex(),
    }

    device_data = {
        "platform": "android",
        "appName": "Tonkeeper",
        "appVersion": "26.04.3",
        "maxProtocolVersion": 2,
        "features": [
            "SendTransaction",
            {
                "name": "SignData",
                "types": ["text", "binary", "cell"],
            },
            {
                "name": "SendTransaction",
                "maxMessages": 255,
            },
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


def _print_qr_ascii(data: str) -> None:
    '''Render QR code as ASCII art in terminal.'''
    try:
        import qrcode
    except ImportError:
        print(f"[!] qrcode lib not installed. Open URL manually: {data}")
        return
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


async def _poll_telegram_auth(
    session: httpx.AsyncClient,
    qtoken: str,
    on_status: Any = None,
) -> str:
    '''
    Poll Telegram OAuth until the auth flow is confirmed.

    Returns the final tgAuthResult string extracted from /auth/push.
    '''
    headers = {
        **BROWSER_HEADERS,
        "Content-type": "application/x-www-form-urlencoded",
    }

    consumed = False
    current_qtoken = qtoken

    while True:
        poll_url = (
            f"{TELEGRAM_OAUTH_BASE}/auth/login"
            f"?{TELEGRAM_BASE_PARAMS}&qtoken={current_qtoken}"
        )

        try:
            res = await session.post(
                poll_url,
                content=b"",
                headers=headers,
            )
            data = res.json()
            status = data.get("status") if isinstance(data, dict) else None

            if status == "refresh":
                current_qtoken = data.get("qtoken", current_qtoken)
                if on_status:
                    on_status("refresh", current_qtoken)

            elif status == "consumed":
                if not consumed:
                    consumed = True
                    if on_status:
                        on_status("consumed", None)

            elif status == "confirmed":
                if on_status:
                    on_status("confirmed", None)
                push_url = (
                    f"{TELEGRAM_OAUTH_BASE}/auth/push"
                    f"?{TELEGRAM_BASE_PARAMS}"
                )
                res_push = await session.get(
                    push_url,
                    headers=BROWSER_HEADERS,
                )
                text = res_push.text
                m = re.search(
                    r"#tgAuthResult=([A-Za-z0-9_\-]+)",
                    text,
                )
                if not m:
                    raise UnexpectedError(
                        "Failed to extract tgAuthResult from push response.",
                    )
                return m.group(1)

        except (httpx.HTTPError, ValueError):
            pass

        await asyncio.sleep(1)


async def _telegram_auth_qr(
    session: httpx.AsyncClient,
    print_qr: bool = True,
    on_status: Any = None,
) -> str:
    '''Run Telegram OAuth via QR-code flow.'''
    url = (
        f"{TELEGRAM_OAUTH_BASE}/auth/auth"
        f"?{TELEGRAM_BASE_PARAMS}&quick_auth=new"
    )
    res = await session.get(url, headers=BROWSER_HEADERS)

    m = re.search(r"setToken\('([^']+)'\)", res.text)
    if not m:
        raise UnexpectedError("Failed to fetch QR qtoken from Telegram OAuth.")

    qtoken = m.group(1)
    tg_link = f"https://t.me/oauth?startapp={qtoken}"

    if on_status:
        on_status("qr_link", tg_link)

    if print_qr:
        print(f"\n[*] Scan this QR (or open the link):\n    {tg_link}\n")
        _print_qr_ascii(tg_link)

    return await _poll_telegram_auth(
        session,
        qtoken,
        on_status=on_status,
    )


async def _telegram_auth_phone(
    session: httpx.AsyncClient,
    phone: str,
    on_status: Any = None,
) -> str:
    '''Run Telegram OAuth via phone-confirmation flow.'''
    auth_page_url = (
        f"{TELEGRAM_OAUTH_BASE}/auth/auth"
        f"?{TELEGRAM_BASE_PARAMS}&phone_login=1"
    )
    await session.get(auth_page_url, headers=BROWSER_HEADERS)

    digits = "".join(ch for ch in phone if ch.isdigit())

    post_url = (
        f"{TELEGRAM_OAUTH_BASE}/auth/request"
        f"?{TELEGRAM_BASE_PARAMS}"
    )
    post_headers = {
        **BROWSER_HEADERS,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": TELEGRAM_OAUTH_BASE,
        "Referer": auth_page_url,
    }
    res = await session.post(
        post_url,
        data={"phone": digits},
        headers=post_headers,
    )

    qtoken = res.text.strip().strip('"').strip("'")
    if (
        not qtoken
        or qtoken.lower() == "session expired"
        or len(qtoken) > 100
    ):
        raise UnexpectedError(
            f"Telegram OAuth phone request failed: {qtoken!r}",
        )

    if on_status:
        on_status("phone_sent", qtoken)

    return await _poll_telegram_auth(
        session,
        qtoken,
        on_status=on_status,
    )


async def authenticate(
    seed: str,
    wallet_version: str = "V5R1",
    phone: str | None = None,
    print_qr: bool = True,
    on_status: Any = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, str]:
    '''
    Perform full Fragment authentication and return session cookies.

    First obtains stel_ssid / stel_dt / stel_ton_token via TON wallet proof.
    If stel_token is missing, runs Telegram OAuth (QR by default, or phone
    confirmation if `phone` is provided) and finalizes the login via the
    `tgAuthResult` redirect.

    Args:
        seed: TON wallet mnemonic phrase.
        wallet_version: "V4R2" or "V5R1".
        phone: If provided, uses phone-confirmation flow instead of QR.
        print_qr: Print the QR code to terminal (QR flow only).
        on_status: Optional callback(status_name, payload) for progress.
        timeout: HTTP timeout in seconds.

    Returns:
        Dict of session cookies with all required keys.
    '''
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as session:
            session.headers.update({
                "User-Agent": BASE_HEADERS["user-agent"],
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            })
            session.cookies.set(
                "stel_dt",
                "-180",
                domain="fragment.com",
            )

            resp = await session.get(f"{FRAGMENT_BASE_URL}/")
            resp.raise_for_status()

            api_hash, ton_proof_payload = _parse_init_page(resp.text)

            mnemonic = seed.strip().split()
            account_data, device_data, proof_data = _generate_proof(
                mnemonic,
                wallet_version,
                ton_proof_payload,
            )

            form_data = {
                "account": json.dumps(
                    account_data,
                    separators=(",", ":"),
                ),
                "device": json.dumps(
                    device_data,
                    separators=(",", ":"),
                ),
                "proof": json.dumps(
                    proof_data,
                    separators=(",", ":"),
                ),
                "method": "checkTonProofAuth",
            }

            session.headers.update({
                "Accept": (
                    "application/json, text/javascript, */*; q=0.01"
                ),
                "Origin": FRAGMENT_BASE_URL,
                "Referer": f"{FRAGMENT_BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": (
                    "application/x-www-form-urlencoded; charset=UTF-8"
                ),
            })

            api_url = f"{FRAGMENT_BASE_URL}/api?hash={api_hash}"
            auth_resp = await session.post(api_url, data=form_data)
            auth_resp.raise_for_status()

            cookies = {c.name: c.value for c in session.cookies.jar}

            if "stel_token" in cookies and cookies["stel_token"]:
                return cookies

            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
            ) as tg_session:
                if phone:
                    tg_auth_result = await _telegram_auth_phone(
                        tg_session,
                        phone,
                        on_status=on_status,
                    )
                else:
                    tg_auth_result = await _telegram_auth_qr(
                        tg_session,
                        print_qr=print_qr,
                        on_status=on_status,
                    )

            tg_form_data = {
                "auth": tg_auth_result,
                "method": "logIn",
            }
            tg_resp = await session.post(api_url, data=tg_form_data)
            tg_resp.raise_for_status()

            cookies = {c.name: c.value for c in session.cookies.jar}
            return cookies

    except (FragmentPageError, UnexpectedError):
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc