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