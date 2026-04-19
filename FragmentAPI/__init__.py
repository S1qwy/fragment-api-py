"""
Fragment API Python Library

Professional library for Fragment.com API with:
- Telegram Stars, Premium, TON purchases
- Stars and Premium giveaways
- Marketplace search (usernames, numbers, gifts)
- Synchronous client (default) and async client (extra)
- Multiple wallet version support (V4R2, V5R1)
- Automatic wallet balance validation
"""

from FragmentAPI.client import FragmentClient
from FragmentAPI.types import (
    AdsTopupResult,
    ConfigError,
    CookieError,
    FragmentAPIError,
    FragmentBaseError,
    FragmentPageError,
    GiftsResult,
    GiveawayPremiumResult,
    GiveawayStarsResult,
    NumbersResult,
    OperationError,
    ParseError,
    PremiumResult,
    StarsResult,
    TransactionError,
    UnexpectedError,
    UsernamesResult,
    UserNotFoundError,
    VerificationError,
    WalletError,
    WalletInfo,
)

__version__ = "4.0.0"
__author__ = "S1qwy"
__email__ = "S1qwy@internet.ru"

__all__ = [
    "__version__",
    "FragmentClient",
    "AdsTopupResult",
    "ConfigError",
    "CookieError",
    "FragmentAPIError",
    "FragmentBaseError",
    "FragmentPageError",
    "GiftsResult",
    "GiveawayPremiumResult",
    "GiveawayStarsResult",
    "NumbersResult",
    "OperationError",
    "ParseError",
    "PremiumResult",
    "StarsResult",
    "TransactionError",
    "UnexpectedError",
    "UsernamesResult",
    "UserNotFoundError",
    "VerificationError",
    "WalletError",
    "WalletInfo",
]
