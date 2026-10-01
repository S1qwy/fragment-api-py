"""Public exception hierarchy."""

from __future__ import annotations


class FragmentError(Exception):
    """Base exception for FragmentAPI."""


class ClientError(FragmentError):
    """Invalid client configuration."""


class ConfigurationError(ClientError):
    """Missing or invalid operation parameters."""

    SEED_REQUIRED = "A signing seed is required."
    API_KEY_REQUIRED = "A blockchain API key is required."
    COOKIES_REQUIRED = "Authenticated Fragment cookies are required."
    TON_TOKEN_REQUIRED = "A stel_ton_token cookie is required."
    INVALID_MNEMONIC = "Invalid TON mnemonic word count: {count}."
    INVALID_MNEMONIC_PHRASE = "The supplied phrase is not a valid basic TON mnemonic."
    INVALID_STARS_AMOUNT = "Stars amount must be an integer between 50 and 10000000."
    INVALID_GRAM_AMOUNT = "TON amount must be an integer between 1 and 1000000000."
    INVALID_TON_AMOUNT = INVALID_GRAM_AMOUNT
    INVALID_MONTHS = "Premium duration must be an integer equal to 3, 6, or 12."
    INVALID_WINNERS_PREMIUM = "Premium winners must be an integer between 1 and 24000."
    INVALID_BID_AMOUNT = "Bid must be a positive integer."
    INVALID_OFFER_AMOUNT = "Offer must be a positive integer."
    INVALID_CREDITS_AMOUNT = "Credits must be a positive integer."
    INVALID_ITEM_TYPE = "Invalid item type: {item_type}."
    INVALID_PAYMENT_METHOD = "Invalid payment method '{method}'. Supported: {supported}."
    UNSUPPORTED_VERSION = "Unsupported wallet version '{version}'. Supported: {supported}."
    UNSUPPORTED_PROVIDER = "Unsupported provider '{provider}'. Supported: {supported}."
    INVALID_PROXY = "Invalid proxy URL."
    WALLET_AUTH_UNSUPPORTED = "Operation '{operation}' is unavailable in wallet_auth mode."
    NOKYC_UNSUPPORTED_OPERATION = WALLET_AUTH_UNSUPPORTED
    INVALID_GIVEAWAY_PACKAGE = "Invalid Stars package {amount}. Supported: {packages}."
    INVALID_GIVEAWAY_WINNERS = "For {amount} Stars, winners must be between 1 and {max_winners}."


ConfigError = ConfigurationError


class CookieError(ClientError):
    """Invalid, unavailable, or expired session cookies."""

    READ_FAILED = "Failed to parse cookies: {exc}"
    MISSING_KEYS = "Missing required cookie keys: {keys}."
    REFRESH_FAILED = "Cookie refresh failed: {exc}"
    AUTO_REFRESH_FAILED = "Wallet authentication did not produce cookie keys: {missing}."
    EXPIRED = "Session cookies expired at {expires}."


class FragmentAPIError(FragmentError):
    """Fragment rejected an API operation."""

    NO_REQUEST_ID = "Fragment returned no request ID for '{context}'."


class FragmentPageError(FragmentAPIError):
    """A Fragment page could not be loaded."""

    BAD_STATUS = "Fragment returned HTTP {status} for {url}."
    HASH_NOT_FOUND = "No Fragment API hash was found at {url}."
    ITEM_NOT_FOUND = "Fragment item was not found at {url}."


class UserNotFoundError(FragmentAPIError):
    """A recipient could not be resolved."""

    NOT_FOUND = "Telegram recipient '{username}' was not found."
    NOT_A_USER = "'{username}' is not assigned to a personal Telegram account."


class ChannelNotFoundError(UserNotFoundError):
    """A giveaway channel could not be resolved."""


class AlreadySubscribedError(FragmentAPIError):
    """The recipient already has Premium."""

    PREMIUM_ACTIVE = "This account is already subscribed to Telegram Premium."


class AnonymousNumberError(FragmentAPIError):
    """An anonymous-number operation failed."""

    NOT_OWNED = "Number '{number}' has no available session termination request."
    TERMINATE_FAILED = "Failed to terminate sessions for '{number}': {error}"


class TransactionError(FragmentAPIError):
    """Transaction preparation or execution failed."""

    INVALID_PAYLOAD = "Transaction messages are missing or invalid."
    BROADCAST_FAILED = "Transaction broadcast failed: {exc}"
    DUPLICATE_SEQNO = "The wallet rejected a duplicate or conflicting transaction."


class BroadcastUncertainError(TransactionError):
    """Broadcast outcome is unknown and must not be retried as a new payment."""


class PaidMessageLimitError(FragmentAPIError):
    """Recipient purchase minimum was not met."""

    MINIMUM_REQUIRED = "Recipient minimum purchase limit: {error}"


class ConfirmationTimeout(TransactionError):
    """The transaction or service receipt remains unconfirmed."""


class SeqnoError(TransactionError):
    """Compatibility exception for sequence-number operations."""


class ParseError(FragmentAPIError):
    """A response or payload could not be parsed."""

    UNPARSEABLE = "Failed to parse {context}: {exc}"


class VerificationError(FragmentAPIError):
    """Fragment requires identity verification."""

    KYC_REQUIRED = "Fragment requires identity verification for this operation."


class OperationError(FragmentError):
    """An operation failed outside Fragment's API."""


class WalletError(OperationError):
    """Wallet derivation or balance retrieval failed."""

    LOW_GRAM_BALANCE = "Insufficient TON: {balance} available, {required} required."
    LOW_TON_BALANCE = LOW_GRAM_BALANCE
    LOW_USDT_BALANCE = "Insufficient USDT: {balance} available, {required} required."
    USDT_BALANCE_CHECK_FAILED = "USDT balance lookup failed: {exc}"
    WALLET_INFO_FAILED = "Wallet information lookup failed: {exc}"
    ACCOUNT_INFO_FAILED = "Wallet account construction failed: {exc}"


class UnexpectedError(OperationError):
    """Unexpected implementation or dependency failure."""

    UNEXPECTED = "Unexpected operation failure: {exc}"


class RetryExhaustedError(OperationError):
    """All permitted attempts were exhausted."""


class SessionStorageError(OperationError):
    """Session persistence failed."""

    SAVE_FAILED = "Session save failed: {exc}"
    LOAD_FAILED = "Session load failed: {exc}"


__all__ = [
    name for name, value in globals().items()
    if isinstance(value, type) and issubclass(value, FragmentError)
]