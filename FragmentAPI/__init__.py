"""
Fragment API Python Library - Async and Sync support for Telegram payments

Professional library for Fragment.com API with:
- Support for Telegram Stars, Premium, and TON
- Both async/await and synchronous interfaces
- Multiple wallet version support (V3R1, V3R2, V4R2, V5R1/W5)
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
    WalletError,
    InvalidWalletVersionError
)
from .models import (
    UserInfo, 
    TransactionMessage, 
    TransactionData, 
    PurchaseResult,
    WalletBalance,
    TransferResult
)

__version__ = "3.2.0"
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
    'InvalidWalletVersionError',
    'UserInfo',
    'TransactionMessage',
    'TransactionData',
    'PurchaseResult',
    'WalletBalance',
    'TransferResult',
]
