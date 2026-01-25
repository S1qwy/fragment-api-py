"""
Exception classes for Fragment API library
"""


class FragmentAPIException(Exception):
    """
    Base exception for all Fragment API related errors
    """
    pass


class AuthenticationError(FragmentAPIException):
    """
    Raised when authentication fails or cookies are invalid
    """
    pass


class UserNotFoundError(FragmentAPIException):
    """
    Raised when requested user is not found
    """
    pass


class InvalidAmountError(FragmentAPIException):
    """
    Raised when provided amount is invalid (too low or too high)
    """
    pass


class PaymentInitiationError(FragmentAPIException):
    """
    Raised when payment cannot be initiated
    """
    pass


class TransactionError(FragmentAPIException):
    """
    Raised when transaction execution fails
    """
    pass


class NetworkError(FragmentAPIException):
    """
    Raised when network request fails
    """
    pass


class RateLimitError(FragmentAPIException):
    """
    Raised when rate limit is exceeded
    """
    pass


class InsufficientBalanceError(FragmentAPIException):
    """
    Raised when wallet balance is insufficient for transaction
    """
    pass


class WalletError(FragmentAPIException):
    """
    Raised when wallet operations fail
    """
    pass


class InvalidWalletVersionError(WalletError):
    """
    Raised when invalid wallet version is specified
    
    Attributes:
        version: The invalid version that was provided
        supported_versions: List of supported wallet versions
    """
    
    SUPPORTED_VERSIONS = {
        'V4R2': 'WalletV4R2 - Most common wallet version',
        'V5R1': 'WalletV5R1 - Latest wallet version (also known as W5)',
        'W5': 'WalletV5R1 - Alias for V5R1',
        'V3R2': 'WalletV3R2 - Legacy wallet version',
        'V3R1': 'WalletV3R1 - Legacy wallet version'
    }
    
    def __init__(self, version: str):
        self.version = version
        self.supported_versions = self.SUPPORTED_VERSIONS
        
        versions_info = "\n".join([
            f"  - {name}: {desc}" 
            for name, desc in self.SUPPORTED_VERSIONS.items()
        ])
        
        message = (
            f"Invalid wallet version: '{version}'\n"
            f"Supported wallet versions:\n{versions_info}"
        )
        super().__init__(message)
