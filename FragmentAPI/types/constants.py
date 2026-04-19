"""
Constants and configuration for Fragment API library
"""

from __future__ import annotations

import json
from typing import Any, Literal, get_args

from tonutils.contracts.wallet import WalletV4R2, WalletV5R1

WalletVersionType = Literal["V4R2", "V5R1"]
SUPPORTED_WALLET_VERSIONS: frozenset[str] = frozenset(get_args(WalletVersionType))

WALLET_CLASSES: dict[str, Any] = {
    "V4R2": WalletV4R2,
    "V5R1": WalletV5R1,
}

MIN_TON_BALANCE: float = 0.056

DEFAULT_TIMEOUT: float = 30.0

REQUIRED_COOKIE_KEYS: tuple[str, ...] = (
    "stel_ssid",
    "stel_dt",
    "stel_token",
    "stel_ton_token",
)

TONAPI_PROXY_BASE: str = "https://tonapi.ru:444/v2"
TONAPI_DEFAULT_KEY: str = "AH" + "0" * 48

FRAGMENT_DOMAIN: str = "fragment.com"
FRAGMENT_BASE_URL: str = f"https://{FRAGMENT_DOMAIN}"
STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"

DEVICE_FINGERPRINT: str = json.dumps(
    {
        "platform": "iphone",
        "appName": "Tonkeeper",
        "appVersion": "26.04.0",
        "maxProtocolVersion": 2,
        "features": [
            "SendTransaction",
            {"name": "SendTransaction", "maxMessages": 255},
            {"name": "SignData", "types": ["text", "binary", "cell"]},
        ],
    }
)

BASE_HEADERS: dict[str, str] = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": FRAGMENT_BASE_URL,
    "priority": "u=1, i",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 "
        "Mobile/15E148 Safari/604.1"
    ),
    "x-requested-with": "XMLHttpRequest",
}
