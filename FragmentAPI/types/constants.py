'''
Constants and configuration for Fragment API library.
'''

from __future__ import annotations

import json
from typing import (
    Any,
    Literal,
    get_args,
)

from tonutils.contracts.wallet import (
    WalletV4R2,
    WalletV5R1,
)

WalletVersionType = Literal["V4R2", "V5R1"]
SUPPORTED_WALLET_VERSIONS: frozenset[str] = frozenset(
    get_args(WalletVersionType),
)

WALLET_CLASSES: dict[str, Any] = {
    "V4R2": WalletV4R2,
    "V5R1": WalletV5R1,
}

WALLET_MAX_MESSAGES: dict[str, int] = {
    "V4R2": 4,
    "V5R1": 255,
}

MIN_TON_BALANCE: float = 0.01

DEFAULT_TIMEOUT: float = 30.0

CONFIRMATION_INTERVAL: float = 3.0
CONFIRMATION_MAX_ATTEMPTS: int = 40

REQUIRED_COOKIE_KEYS: tuple[str, ...] = (
    "stel_ssid",
    "stel_dt",
    "stel_token",
    "stel_ton_token",
)

AUTH_REQUIRED_COOKIE_KEYS: tuple[str, ...] = (
    "stel_ssid",
    "stel_dt",
)

TONAPI_BASE_URL: str = "https://tonapi.io/v2"
TONAPI_PROXY_BASE: str = "https://tonapi.ru:444/v2"
TONAPI_DEFAULT_KEY: str = "AH" + "0" * 48

FRAGMENT_DOMAIN: str = "fragment.com"
FRAGMENT_BASE_URL: str = f"https://{FRAGMENT_DOMAIN}"
STARS_PAGE: str = f"{FRAGMENT_BASE_URL}/stars"
STARS_BUY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/buy"
STARS_HISTORY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/history"
STARS_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/giveaway"
PREMIUM_PAGE: str = f"{FRAGMENT_BASE_URL}/premium"
PREMIUM_GIFT_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/gift"
PREMIUM_HISTORY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/history"
PREMIUM_GIVEAWAY_PAGE: str = f"{FRAGMENT_BASE_URL}/premium/giveaway"
ADS_TOPUP_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/topup"
ADS_HISTORY_PAGE: str = f"{FRAGMENT_BASE_URL}/ads/history"
NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/gifts"
PROFILE_PAGE: str = f"{FRAGMENT_BASE_URL}/my/profile"
SESSIONS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/sessions"
MY_BIDS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/bids"
MY_ASSETS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/assets"
MY_USERNAMES_PAGE: str = f"{FRAGMENT_BASE_URL}/my/usernames"
MY_GIFTS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/gifts"
MY_NUMBERS_PAGE: str = f"{FRAGMENT_BASE_URL}/my/numbers"
STARS_WITHDRAW_PAGE: str = f"{FRAGMENT_BASE_URL}/stars/withdraw"
NFT_WITHDRAW_PAGE: str = f"{FRAGMENT_BASE_URL}/gift/withdraw"

STATS_ENDPOINT: str = "https://fragment.s1qwy.ru/statistic/collect"

STARS_GIVEAWAY_PACKAGES: frozenset[int] = frozenset({
    500,
    1_000,
    1_500,
    2_500,
    5_000,
    10_000,
    25_000,
    35_000,
    50_000,
    100_000,
    150_000,
    500_000,
    1_000_000,
})

DEVICE_FINGERPRINT: str = json.dumps(
    {
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
    },
    separators=(",", ":"),
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
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Mobile Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

EVM_PAYMENT_METHODS: frozenset[str] = frozenset({
    "usdt_eth",
    "usdt_pol",
    "usdc_eth",
    "usdc_base",
    "usdc_pol",
})

EVM_CHAIN_NAMES: dict[int, str] = {
    1: "ETH",
    8453: "BASE",
    137: "POL",
}

EVM_TOKEN_DECIMALS: dict[str, int] = {
    "0xdac17f958d2ee523a2206206994597c177e3d24f": 6,
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 6,
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": 6,
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": 6,
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": 6,
}

EVM_TOKEN_SYMBOLS: dict[str, str] = {
    "0xdac17f958d2ee523a2206206994597c177e3d24f": "USDT",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": "USDC",
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": "USDT",
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC",
}

VALID_PAYMENT_METHODS: frozenset[str] = frozenset({
    "ton",
    "usdt_ton",
    "usdt_eth",
    "usdt_pol",
    "usdc_eth",
    "usdc_base",
    "usdc_pol",
})

BATCH_PAYMENT_METHODS: frozenset[str] = frozenset({
    "ton",
    "usdt_ton",
})

TON_PAYMENT_METHODS: frozenset[str] = frozenset({"ton", "usdt_ton"})