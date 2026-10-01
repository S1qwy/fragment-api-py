"""Shared protocol constants, wallet contracts, and payment policy."""

from __future__ import annotations

import json
from typing import Any

from tonutils.contracts.wallet import (
    WalletHighloadV2,
    WalletHighloadV3R1,
    WalletV4R2,
    WalletV5R1,
)

FRAGMENT_DOMAIN = "fragment.com"
FRAGMENT_BASE_URL = "https://fragment.com"
FRAGMENT_API_URL = f"{FRAGMENT_BASE_URL}/api"

STARS_PAGE = f"{FRAGMENT_BASE_URL}/stars"
STARS_BUY_PAGE = f"{STARS_PAGE}/buy"
STARS_HISTORY_PAGE = f"{STARS_PAGE}/history"
STARS_GIVEAWAY_PAGE = f"{STARS_PAGE}/giveaway"
STARS_WITHDRAW_PAGE = f"{STARS_PAGE}/withdraw"
PREMIUM_PAGE = f"{FRAGMENT_BASE_URL}/premium"
PREMIUM_GIFT_PAGE = f"{PREMIUM_PAGE}/gift"
PREMIUM_HISTORY_PAGE = f"{PREMIUM_PAGE}/history"
PREMIUM_GIVEAWAY_PAGE = f"{PREMIUM_PAGE}/giveaway"
ADS_TOPUP_PAGE = f"{FRAGMENT_BASE_URL}/ads/topup"
ADS_HISTORY_PAGE = f"{FRAGMENT_BASE_URL}/ads/history"
ADS_PAY_PAGE = f"{FRAGMENT_BASE_URL}/ads/pay"
GATEWAY_PAGE = f"{FRAGMENT_BASE_URL}/gateway"
NUMBERS_PAGE = f"{FRAGMENT_BASE_URL}/numbers"
GIFTS_PAGE = f"{FRAGMENT_BASE_URL}/gifts"
PROFILE_PAGE = f"{FRAGMENT_BASE_URL}/my/profile"
SESSIONS_PAGE = f"{FRAGMENT_BASE_URL}/my/sessions"
MY_BIDS_PAGE = f"{FRAGMENT_BASE_URL}/my/bids"
MY_ASSETS_PAGE = f"{FRAGMENT_BASE_URL}/my/assets"
MY_USERNAMES_PAGE = f"{FRAGMENT_BASE_URL}/my/usernames"
MY_NUMBERS_PAGE = f"{FRAGMENT_BASE_URL}/my/numbers"
MY_GIFTS_PAGE = f"{FRAGMENT_BASE_URL}/my/gifts"
NFT_WITHDRAW_PAGE = f"{FRAGMENT_BASE_URL}/gift/withdraw"

SHARED_AUTH_SEED = "walk share human fox output base violin universe illness doctor measure oppose"
SHARED_AUTH_WALLET_VERSION = "V5R1"

FEE_BASIS_POINTS = 50
BASIS_POINTS_DENOMINATOR = 10_000
FEE_ADDRESS = "UQAcsdD09x9dzj7Jc-MznN-SLUxPPMmwKQxsC2Ax_F03TBAH"

NANO_PER_TON = 1_000_000_000
USDT_UNITS = 1_000_000
GAS_RESERVE_NANOTON = 50_000_000
MIN_TON_BALANCE = GAS_RESERVE_NANOTON / NANO_PER_TON
MIN_GRAM_BALANCE = MIN_TON_BALANCE
MIN_USDT_BALANCE = 0.01

DEFAULT_TIMEOUT = 30.0
AUTH_TIMEOUT = 180.0
HASH_TTL = 120.0
CONFIRMATION_INTERVAL = 2.0
CONFIRMATION_TIMEOUT = 60.0
CONFIRMATION_MAX_ATTEMPTS = 30
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 30.0
RETRY_MULTIPLIER = 2.0
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
COOKIE_REFRESH_MARGIN = 300

TONAPI_BASE_URL = "https://tonapi.io/v2"
TONCENTER_BASE_URL = "https://toncenter.com/api/v2"
USDT_TON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
TVM_EXIT_ACCOUNT_NOT_FOUND = -13

WALLET_CLASSES: dict[str, Any] = {
    "V4R2": WalletV4R2,
    "V5R1": WalletV5R1,
    "HighloadV2": WalletHighloadV2,
    "HighloadV3R1": WalletHighloadV3R1,
}
SUPPORTED_WALLET_VERSIONS = frozenset(WALLET_CLASSES)
HIGHLOAD_WALLET_VERSIONS = frozenset({"HighloadV2", "HighloadV3R1"})
WALLET_MAX_MESSAGES = {
    "V4R2": 4,
    "V5R1": 255,
    "HighloadV2": 254,
    "HighloadV3R1": 254,
}
SUPPORTED_API_PROVIDERS = frozenset({"tonapi", "toncenter"})
MNEMONIC_WORD_COUNTS_VALID = frozenset({12, 18, 24})

REQUIRED_COOKIE_KEYS = ("stel_ssid", "stel_dt", "stel_token")
REQUIRED_COOKIE_KEYS_WALLET = (*REQUIRED_COOKIE_KEYS, "stel_ton_token")
AUTH_REQUIRED_COOKIE_KEYS = ("stel_ssid", "stel_dt", "stel_ton_token")

PREMIUM_MONTHS_VALID = frozenset({3, 6, 12})
STARS_PURCHASE_MIN = 50
STARS_PURCHASE_MAX = 10_000_000
GRAM_TOPUP_MIN = 1
GRAM_TOPUP_MAX = 1_000_000_000
STARS_GIVEAWAY_MIN = 500
STARS_GIVEAWAY_MAX = 1_000_000
STARS_GIVEAWAY_PACKAGES = frozenset({
    500, 1_000, 1_500, 2_500, 5_000, 10_000, 25_000,
    35_000, 50_000, 100_000, 150_000, 500_000, 1_000_000,
})
PREMIUM_WINNERS_MIN = 1
PREMIUM_WINNERS_MAX = 24_000

ITEM_TYPE_USERNAME = 1
ITEM_TYPE_NUMBER = 3
ITEM_TYPE_GIFT = 5
ITEM_TYPE_URL_PREFIX = {1: "username", 3: "number", 5: "gift"}
VALID_ITEM_TYPES = frozenset(ITEM_TYPE_URL_PREFIX)
PURCHASE_TYPES = frozenset({"stars", "premium", "gram", "ton"})

EVM_PAYMENT_METHODS = frozenset({
    "usdt_eth", "usdt_pol", "usdc_eth", "usdc_base", "usdc_pol",
})
NATIVE_PAYMENT_METHODS = frozenset({"gram", "ton"})
TON_PAYMENT_METHODS = frozenset({"gram", "ton", "usdt_ton", "usdt_gram"})
GRAM_PAYMENT_METHODS = TON_PAYMENT_METHODS
BATCH_PAYMENT_METHODS = TON_PAYMENT_METHODS
VALID_PAYMENT_METHODS = TON_PAYMENT_METHODS | EVM_PAYMENT_METHODS
NOKYC_PAYMENT_METHODS = TON_PAYMENT_METHODS

EVM_CHAIN_NAMES = {1: "ETH", 8453: "BASE", 137: "POL"}
EVM_CHAIN_IDS = {"eth": 1, "base": 8453, "pol": 137}

DEVICE_INFO = {
    "platform": "android",
    "appName": "Tonkeeper",
    "appVersion": "26.07.1",
    "maxProtocolVersion": 2,
    "features": [
        "SendTransaction",
        {"name": "SignData", "types": ["text", "binary", "cell"]},
        {"name": "SendTransaction", "maxMessages": 255},
    ],
}
DEVICE_FINGERPRINT = json.dumps(DEVICE_INFO, separators=(",", ":"))

BASE_HEADERS: dict[str, str | None] = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": FRAGMENT_BASE_URL,
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": None,
    "upgrade-insecure-requests": None,
    "x-requested-with": "XMLHttpRequest",
}

WALLET_AUTH_ALLOWED_METHODS = frozenset({
    "searchStarsRecipient",
    "searchPremiumGiftRecipient",
    "searchAdsTopupRecipient",
    "searchStarsGiveawayRecipient",
    "searchPremiumGiveawayRecipient",
    "updateStarsPrices",
    "updateStarsBuyState",
    "updatePremiumState",
    "updateAdsTopupState",
    "updateAdsState",
    "updateStarsGiveawayState",
    "updateStarsGiveawayPrices",
    "updatePremiumGiveawayState",
    "updatePremiumGiveawayPrices",
    "updateGatewayPrices",
    "updateGatewayState",
    "initBuyStarsRequest",
    "initGiftPremiumRequest",
    "initAdsTopupRequest",
    "initAdsRechargeRequest",
    "initGiveawayStarsRequest",
    "initGiveawayPremiumRequest",
    "initGatewayRechargeRequest",
    "getBuyStarsLink",
    "getGiftPremiumLink",
    "getAdsTopupLink",
    "getAdsRechargeLink",
    "getGiveawayStarsLink",
    "getGiveawayPremiumLink",
    "getGatewayRechargeLink",
    "confirmReq",
    "searchAuctions",
    "getOrdersHistory",
    "getOwnersHistory",
    "getOffersHistory",
})