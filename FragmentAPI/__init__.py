"""
Fragment API Python Library - Async and Sync support for Telegram payments

Professional library for Fragment.com API with:
- Support for Telegram Stars, Premium, and TON
- Both async/await and synchronous interfaces
- Automatic wallet balance validation
- Comprehensive error handling
"""

from .async_client import AsyncFragmentAPI
from .sync_client import SyncFragmentAPI
from .wallet import WalletManager
from .exceptions import (
    FragmentAPIException,
    AuthenticationError,
    UserNotFoundError,
    InvalidAmountError,
    PaymentInitiationError,
    TransactionError,
    NetworkError,
    RateLimitError,
    InsufficientBalanceError,
    WalletError
)
from .models import (
    UserInfo, 
    TransactionMessage, 
    TransactionData, 
    PurchaseResult,
    WalletBalance
)

__version__ = "3.0.3"
__author__ = "S1qwy"
__email__ = "amirhansuper75@gmail.com"

__all__ = [
    'AsyncFragmentAPI',
    'SyncFragmentAPI',
    'WalletManager',
    'FragmentAPIException',
    'AuthenticationError',
    'UserNotFoundError',
    'InvalidAmountError',
    'PaymentInitiationError',
    'TransactionError',
    'NetworkError',
    'RateLimitError',
    'InsufficientBalanceError',
    'WalletError',
    'UserInfo',
    'TransactionMessage',
    'TransactionData',
    'PurchaseResult',
    'WalletBalance',
]