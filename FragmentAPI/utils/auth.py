"""TON proof authentication and bounded interactive Telegram OAuth."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import inspect
import json
import re
import struct
import time
from typing import Any
from urllib.parse import urlencode

from curl_cffi import requests
from nacl.signing import SigningKey
from ton_core import NetworkGlobalID

from FragmentAPI.exceptions import CookieError, FragmentAPIError, ParseError
from FragmentAPI.types.constants import (
    AUTH_REQUIRED_COOKIE_KEYS,
    AUTH_TIMEOUT,
    DEFAULT_TIMEOUT,
    DEVICE_INFO,
    FRAGMENT_BASE_URL,
    REQUIRED_COOKIE_KEYS_WALLET,
    WALLET_CLASSES,
)
from FragmentAPI.utils.http import FragmentTransport, raise_api_error
from FragmentAPI.utils.proxy import build_curl_proxy_args
from FragmentAPI.utils.validation import (
    normalize_seed,
    normalize_wallet_version,
    validate_cookie_keys,
)

TELEGRAM_OAUTH_BASE = "https://oauth.telegram.org"
TELEGRAM_PARAMS = {
    "client_id": "5444323279",
    "origin": FRAGMENT_BASE_URL,
    "return_to": f"{FRAGMENT_BASE_URL}/",
    "scope": "openid profile telegram:bot_access",
    "redirect_uri": f"{FRAGMENT_BASE_URL}/",
    "response_type": "post_message",
}


class OfflineClient:
    """Network identity sufficient for offline wallet derivation."""

    network = NetworkGlobalID.MAINNET


def embedded_object(text: str, marker: str) -> dict[str, Any]:
    """Decode a JavaScript call's first JSON object without regex nesting assumptions."""
    index = text.find(marker)
    if index < 0:
        raise ParseError(f"Missing embedded object: {marker}")
    try:
        result, _ = json.JSONDecoder().raw_decode(text[index + len(marker):].lstrip())
    except ValueError as exc:
        raise ParseError(f"Invalid embedded object: {marker}") from exc
    if not isinstance(result, dict):
        raise ParseError(f"Expected an object in {marker}")
    return result


def _key_bytes(value: Any) -> bytes:
    """Read tonutils key wrappers without transforming their contents."""
    if isinstance(value, bytes):
        return value
    hexadecimal = getattr(value, "as_hex", None)
    if isinstance(hexadecimal, str):
        return bytes.fromhex(hexadecimal)
    for attribute in ("data", "key", "private_key", "public_key"):
        raw = getattr(value, attribute, None)
        if isinstance(raw, bytes):
            return raw
    raise ParseError("Unsupported tonutils key representation.")


def derive_account(seed: str, wallet_version: str) -> dict[str, Any]:
    """Build TON Connect account information offline."""
    wallet, public_key, _, _ = WALLET_CLASSES[
        normalize_wallet_version(wallet_version)
    ].from_mnemonic(client=OfflineClient(), mnemonic=normalize_seed(seed))
    return {
        "address": wallet.address.to_str(is_user_friendly=False),
        "chain": "-239",
        "walletStateInit": base64.b64encode(
            wallet.state_init.serialize().to_boc()
        ).decode(),
        "publicKey": _key_bytes(public_key).hex(),
    }


def _generate_proof(
    mnemonic: list[str],
    wallet_version: str,
    ton_proof_payload: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Sign the domain-bound TON Connect proof challenge."""
    seed = normalize_seed(" ".join(mnemonic))
    version = normalize_wallet_version(wallet_version)
    wallet, public_key, private_key, _ = WALLET_CLASSES[version].from_mnemonic(
        client=OfflineClient(), mnemonic=seed
    )
    address = wallet.address.to_str(is_user_friendly=False)
    workchain, address_hash = address.split(":")
    domain = b"fragment.com"
    timestamp = int(time.time())
    message = (
        b"ton-proof-item-v2/"
        + struct.pack(">i", int(workchain))
        + bytes.fromhex(address_hash)
        + struct.pack("<I", len(domain))
        + domain
        + struct.pack("<Q", timestamp)
        + ton_proof_payload.encode()
    )
    digest = hashlib.sha256(
        b"\xff\xffton-connect" + hashlib.sha256(message).digest()
    ).digest()
    signature = SigningKey(_key_bytes(private_key)[:32]).sign(digest).signature
    account = {
        "address": address,
        "chain": "-239",
        "publicKey": _key_bytes(public_key).hex(),
        "walletStateInit": base64.b64encode(
            wallet.state_init.serialize().to_boc()
        ).decode(),
    }
    proof = {
        "timestamp": timestamp,
        "domain": {"lengthBytes": len(domain), "value": domain.decode()},
        "payload": ton_proof_payload,
        "signature": base64.b64encode(signature).decode(),
    }
    return account, dict(DEVICE_INFO), proof


def fragment_cookies(session: requests.AsyncSession) -> dict[str, str]:
    """Export only Fragment-domain cookies from a session jar."""
    return {
        cookie.name: cookie.value
        for cookie in session.cookies.jar
        if cookie.domain.lstrip(".") == "fragment.com"
    }


async def _proof_on_session(
    session: requests.AsyncSession,
    seed: str,
    wallet_version: str,
) -> dict[str, str]:
    """Authenticate a wallet using the supplied session."""
    session.cookies.set("stel_dt", "-180", domain="fragment.com")
    transport = FragmentTransport(session)
    text = await transport.get_text(f"{FRAGMENT_BASE_URL}/")
    wallet_data = embedded_object(text, "Wallet.init(")
    challenge = wallet_data.get("ton_proof")
    if not isinstance(challenge, str) or not challenge:
        raise FragmentAPIError("Fragment did not provide a TON proof challenge.")
    account, device, proof = _generate_proof(
        normalize_seed(seed).split(), wallet_version, challenge
    )
    result = await transport.call(
        "checkTonProofAuth",
        {
            "account": json.dumps(account),
            "device": json.dumps(device),
            "proof": json.dumps(proof),
        },
        f"{FRAGMENT_BASE_URL}/",
    )
    raise_api_error(result)
    cookies = fragment_cookies(session)
    validate_cookie_keys(cookies, AUTH_REQUIRED_COOKIE_KEYS)
    return cookies


async def auth_ton_proof(
    seed: str,
    wallet_version: str = "V5R1",
    timeout: float = DEFAULT_TIMEOUT,
    *,
    proxy: str | None = None,
    session: requests.AsyncSession | None = None,
) -> dict[str, str]:
    """Authenticate only wallet ownership; Telegram authentication is not implied."""
    seed = normalize_seed(seed)
    version = normalize_wallet_version(wallet_version)
    if session is not None:
        return await _proof_on_session(session, seed, version)
    async with requests.AsyncSession(
        timeout=timeout, impersonate="chrome", **build_curl_proxy_args(proxy)
    ) as owned:
        return await _proof_on_session(owned, seed, version)


async def _notify(callback: Any, status: str, payload: Any) -> None:
    """Support synchronous and asynchronous progress callbacks."""
    if callback is not None:
        result = callback(status, payload)
        if inspect.isawaitable(result):
            await result


def _print_qr(link: str) -> None:
    """Print an OAuth link and an optional terminal QR code."""
    print(link)
    try:
        import qrcode
    except ImportError:
        return
    qr = qrcode.QRCode()
    qr.add_data(link)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


async def _telegram_login(
    session: requests.AsyncSession,
    phone: str | None,
    print_qr: bool,
    on_status: Any,
) -> str:
    """Complete Telegram OAuth inside a caller-enforced total deadline."""
    query = urlencode(TELEGRAM_PARAMS)
    page = f"{TELEGRAM_OAUTH_BASE}/auth/auth?{query}"
    if phone:
        await session.get(f"{page}&phone_login=1")
        response = await session.post(
            f"{TELEGRAM_OAUTH_BASE}/auth/request?{query}",
            data={"phone": "".join(character for character in phone if character.isdigit())},
            headers={"origin": TELEGRAM_OAUTH_BASE, "referer": page},
        )
        response.raise_for_status()
        token = response.text.strip().strip("\"'")
        if not token or len(token) > 100 or "expired" in token.casefold():
            raise FragmentAPIError("Telegram rejected the phone login request.")
        await _notify(on_status, "phone_sent", None)
    else:
        response = await session.get(f"{page}&quick_auth=new")
        response.raise_for_status()
        match = re.search(r"setToken\(['\"]([^'\"]+)['\"]\)", response.text)
        if not match:
            raise ParseError("Telegram OAuth QR token was not found.")
        token = match.group(1)
        link = f"https://t.me/oauth?startapp={token}"
        await _notify(on_status, "qr_link", link)
        if print_qr:
            _print_qr(link)

    while True:
        response = await session.post(
            f"{TELEGRAM_OAUTH_BASE}/auth/login?{query}&{urlencode({'qtoken': token})}",
            data="",
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ParseError("Telegram OAuth returned a non-object response.")
        status = result.get("status")
        if status == "refresh":
            token = str(result.get("qtoken") or token)
            link = f"https://t.me/oauth?startapp={token}"
            await _notify(on_status, "qr_link", link)
            if print_qr and not phone:
                _print_qr(link)
        elif status == "confirmed":
            await _notify(on_status, "confirmed", None)
            pushed = await session.get(
                f"{TELEGRAM_OAUTH_BASE}/auth/push?{query}"
            )
            pushed.raise_for_status()
            match = re.search(r"tgAuthResult=([A-Za-z0-9_-]+)", pushed.text)
            if not match:
                raise ParseError("Telegram OAuth result was not found.")
            return match.group(1)
        elif status in {"expired", "declined", "cancelled"}:
            raise FragmentAPIError(f"Telegram OAuth ended with status {status}.")
        elif status == "consumed":
            await _notify(on_status, "consumed", None)
        await asyncio.sleep(1)


async def authenticate(
    seed: str,
    wallet_version: str = "V5R1",
    phone: str | None = None,
    print_qr: bool = True,
    on_status: Any = None,
    timeout: float = DEFAULT_TIMEOUT,
    *,
    proxy: str | None = None,
    auth_timeout: float = AUTH_TIMEOUT,
) -> dict[str, str]:
    """Obtain full wallet and Telegram cookies through explicit interactive login."""
    async with requests.AsyncSession(
        timeout=timeout, impersonate="chrome", **build_curl_proxy_args(proxy)
    ) as session:
        cookies = await auth_ton_proof(
            seed, wallet_version, timeout, session=session
        )
        if cookies.get("stel_token"):
            validate_cookie_keys(cookies, REQUIRED_COOKIE_KEYS_WALLET)
            return cookies
        async with requests.AsyncSession(
            timeout=timeout, impersonate="chrome", **build_curl_proxy_args(proxy)
        ) as telegram:
            try:
                token = await asyncio.wait_for(
                    _telegram_login(telegram, phone, print_qr, on_status),
                    timeout=auth_timeout,
                )
            except asyncio.TimeoutError as exc:
                raise CookieError("Telegram authentication timed out.") from exc
        result = await FragmentTransport(session).call("logIn", {"auth": token})
        raise_api_error(result)
        cookies = fragment_cookies(session)
        validate_cookie_keys(cookies, REQUIRED_COOKIE_KEYS_WALLET)
        return cookies


async def refresh_wallet_session(
    seed: str,
    wallet_version: str = "V5R1",
    timeout: float = DEFAULT_TIMEOUT,
    *,
    proxy: str | None = None,
) -> dict[str, str]:
    """Refresh wallet-only cookies without requesting Telegram OAuth."""
    return await auth_ton_proof(seed, wallet_version, timeout, proxy=proxy)