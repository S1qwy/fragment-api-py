"""
Exception hierarchy for Fragment API library.

All exceptions inherit from FragmentError for easy catching.
Errors are organized by category: client config, API responses, and operations.
"""

from __future__ import annotations


MNEMONIC_WORD_COUNTS_VALID = (12, 18, 24)
PREMIUM_MONTHS_VALID = (3, 6, 12)
STARS_PURCHASE_MIN = 50
STARS_PURCHASE_MAX = 10_000_000
GRAM_TOPUP_MIN = 1
GRAM_TOPUP_MAX = 1_000_000_000
STARS_WINNERS_MIN = 1
STARS_WINNERS_MAX = 5
PREMIUM_WINNERS_MIN = 1
PREMIUM_WINNERS_MAX = 24_000
STARS_GIVEAWAY_MIN = 500
STARS_GIVEAWAY_MAX = 1_000_000


class FragmentError(Exception):
    """Base exception for all Fragment API library errors."""


class ClientError(FragmentError):
    """Raised for client configuration and setup issues."""


class ConfigurationError(ClientError):
    """Raised when required client parameters are missing or invalid."""

    MISSING_VARS = "Missing required parameter(s): {keys}."
    UNSUPPORTED_VERSION = "Unsupported wallet version '{version}'. Supported values: {supported}."
    INVALID_MNEMONIC = (
        f"Invalid mnemonic phrase: expected "
        f"{', '.join(str(n) for n in sorted(MNEMONIC_WORD_COUNTS_VALID))} words, got {{count}}."
    )
    UNSUPPORTED_PROVIDER = "Unsupported API provider '{provider}'. Supported values: {supported}."
    UNSUPPORTED_METHOD = (
        "EVM payment methods are not supported for '{item_type}' purchases. "
        "Use 'gram' or 'ton' payment method instead."
    )
    INVALID_MONTHS = (
        f"Invalid Premium duration: choose "
        f"{', '.join(str(m) for m in sorted(PREMIUM_MONTHS_VALID))} months."
    )
    INVALID_STARS_AMOUNT = (
        f"Invalid Stars amount: must be an integer between "
        f"{STARS_PURCHASE_MIN:,} and {STARS_PURCHASE_MAX:,}."
    )
    INVALID_GRAM_AMOUNT = (
        f"Invalid GRAM amount: must be an integer between "
        f"{GRAM_TOPUP_MIN:,} and {GRAM_TOPUP_MAX:,}."
    )
    INVALID_TON_AMOUNT = INVALID_GRAM_AMOUNT
    INVALID_WINNERS_STARS = (
        f"Invalid winners count: must be an integer between "
        f"{STARS_WINNERS_MIN:,} and {STARS_WINNERS_MAX:,}."
    )
    INVALID_WINNERS_PREMIUM = (
        f"Invalid winners count: must be an integer between "
        f"{PREMIUM_WINNERS_MIN:,} and {PREMIUM_WINNERS_MAX:,}."
    )
    INVALID_STARS_PER_WINNER = (
        f"Invalid Stars per winner: must be an integer between "
        f"{STARS_GIVEAWAY_MIN:,} and {STARS_GIVEAWAY_MAX:,}."
    )
    INVALID_PAYMENT_METHOD = "Invalid payment method '{method}'. Supported values: {supported}."
    INVALID_GIVEAWAY_PACKAGE = (
        "Invalid Stars giveaway amount: {amount}. Must be one of: {packages}."
    )
    INVALID_GIVEAWAY_WINNERS = (
        "Invalid winners count: {winners}. "
        "For {amount} stars, winners must be 1 to {max_winners} (total_stars / 100)."
    )
    INVALID_ITEM_TYPE = (
        "Invalid item_type: {item_type}. Must be 1 (username), 3 (number), or 5 (gift)."
    )
    INVALID_BID_AMOUNT = "Invalid bid amount: must be a positive integer (GRAM)."
    INVALID_OFFER_AMOUNT = "Invalid offer amount: must be a positive integer (GRAM)."
    INVALID_CREDITS_AMOUNT = "Invalid credits amount: must be a positive integer."
    SEED_REQUIRED = (
        "This operation requires a wallet seed phrase. "
        "Initialize FragmentClient with seed=... parameter."
    )
    TON_TOKEN_REQUIRED = (
        "This operation requires stel_ton_token cookie. "
        "Make sure you have connected your TON wallet on fragment.com."
    )
    API_KEY_REQUIRED = (
        "This operation requires an API key (Tonconsole or Toncenter). "
        "Initialize FragmentClient with api_key=... parameter."
    )
    COOKIES_REQUIRED = (
        "This operation requires Fragment cookies. "
        "Initialize FragmentClient with cookies=... parameter."
    )
    NOKYC_UNSUPPORTED_METHOD = (
        "No-KYC mode only supports GRAM/TON payment methods. Got: '{method}'."
    )
    NOKYC_UNSUPPORTED_OPERATION = (
        "Operation '{operation}' is not available in No-KYC mode. "
        "Provide Fragment cookies to use this feature."
    )
    INVALID_PROXY = (
        "Invalid proxy format: '{proxy}'. "
        "Expected format: 'http://host:port', 'socks5://host:port', "
        "or 'socks5://user:pass@host:port'."
    )


ConfigError = ConfigurationError


class CookieError(ClientError):
    """Raised when cookies are unreadable or missing required fields."""

    READ_FAILED = "Failed to parse cookies: expected a JSON string or a dict, got {exc}."
    MISSING_KEYS = (
        "Fragment cookies are missing or empty for key(s): {keys}. "
        "Open fragment.com in your browser, log in, and copy fresh cookies."
    )
    UNSUPPORTED_BROWSER = "Unsupported browser '{browser}'. Supported values: {supported}."
    BROWSER_READ_FAILED = (
        "Failed to read {browser} cookies: {exc}. "
        "Make sure {browser} is installed and you are logged in to {url}."
    )
    MISSING_BROWSER_KEYS = (
        "Fragment cookies not found in {browser}: {keys}. "
        "Make sure you are logged in to {url} and have connected your TON wallet in {browser}."
    )
    EXPIRED = (
        "Fragment session cookie expired at {expires}. "
        "Log in to fragment.com in your browser and extract fresh cookies."
    )
    REFRESH_FAILED = (
        "Failed to refresh Fragment session cookies: {exc}. "
        "Manual re-authentication may be required."
    )


class FragmentAPIError(FragmentError):
    """Raised for errors returned by Fragment API responses."""

    NO_REQUEST_ID = (
        "Fragment did not return a request ID for '{context}'. "
        "Your session may have expired. Refresh your cookies and try again."
    )


class MarketAppAPIError(FragmentError):
    """Raised for errors returned by MarketApp API in No-KYC mode."""

    API_CALL_FAILED = "MarketApp API call failed for '{method}': {error}"
    RECIPIENT_NOT_FOUND = "Recipient '{username}' not found via MarketApp API."
    TRANSACTION_BUILD_FAILED = "Failed to build transaction via MarketApp API: {error}"


class FragmentPageError(FragmentAPIError):
    """Raised when Fragment page cannot be fetched or API hash not found."""

    BAD_STATUS = (
        "Fragment returned HTTP {status} when loading {url}. "
        "Your cookies may be invalid or expired. Refresh them and try again."
    )
    HASH_NOT_FOUND = (
        "Could not extract the API hash from {url}. "
        "The page structure may have changed, or you may not be logged in."
    )
    ITEM_NOT_FOUND = "Item not found at {url}. Fragment returned HTTP 302 redirect."


class UserNotFoundError(FragmentAPIError):
    """Raised when target Telegram user is not found on Fragment."""

    NOT_FOUND = (
        "Telegram user '{username}' was not found on Fragment. "
        "Double-check the username and make sure the account exists."
    )
    NOT_A_USER = (
        "'{username}' does not belong to a user account. "
        "Make sure the username is assigned to a personal Telegram account, not a channel or bot."
    )


class AlreadySubscribedError(FragmentAPIError):
    """Raised when trying to gift Premium to a user who already has an active subscription."""

    PREMIUM_ACTIVE = "This account is already subscribed to Telegram Premium."


class AnonymousNumberError(FragmentAPIError):
    """Raised for Fragment anonymous number API failures."""

    NOT_OWNED = (
        "Number '{number}' is not associated with your Fragment account "
        "or has no active sessions to terminate."
    )
    TERMINATE_FAILED = "Failed to terminate sessions for '{number}': {error}"


class TransactionError(FragmentAPIError):
    """Raised when TON transaction fails to build or broadcast."""

    INVALID_PAYLOAD = (
        "Fragment returned an invalid transaction payload: "
        "'transaction.messages' is missing or empty."
    )
    BROADCAST_FAILED = "Transaction broadcast failed: {exc}"
    BROADCAST_SSL_ERROR = (
        "Transaction broadcast failed due to an SSL certificate error: {exc}\n"
        "This usually means your system's CA bundle is missing or outdated.\n"
        "Fix: run `pip install --upgrade certifi` and retry. "
        "On macOS you may also need to run the 'Install Certificates.command' "
        "located in your Python installation folder."
    )
    DUPLICATE_SEQNO = (
        "Transaction broadcast failed: the TON wallet rejected the message "
        "because a previous transaction with the same sequence number (seqno) "
        "is still pending confirmation on-chain.\n"
        "Wait a few seconds for the previous transaction to confirm, then retry."
    )


class ConfirmationTimeout(TransactionError):
    """Raised when seqno/balance confirmation times out."""

    TIMEOUT = (
        "Transaction confirmation timed out after {seconds}s. "
        "The transaction may have been sent — check the blockchain manually. "
        "seqno_before={seqno_before}, balance_before={balance_before:.4f} GRAM."
    )


class SeqnoError(TransactionError):
    """Raised when seqno retrieval or validation fails."""

    FETCH_FAILED = "Failed to fetch wallet seqno: {exc}"
    STALE = (
        "Seqno did not increment after {seconds}s. "
        "Transaction may not have been accepted by the network."
    )


class ParseError(FragmentAPIError):
    """Raised when Fragment API response cannot be parsed."""

    UNPARSEABLE = "Failed to parse the Fragment API response for '{context}': {exc}"


class VerificationError(FragmentAPIError):
    """Raised when Fragment requires KYC verification."""

    KYC_REQUIRED = (
        "Fragment requires identity verification (KYC) before this action can be completed. "
        "Complete verification at https://fragment.com/my/profile and retry."
    )


class OperationError(FragmentError):
    """Raised for runtime operation failures unrelated to Fragment API."""


class WalletError(OperationError):
    """Raised for TON wallet issues (connection, balance, account info)."""

    LOW_GRAM_BALANCE = (
        "Insufficient GRAM balance: {balance:.4f} GRAM available, "
        "{required:.4f} GRAM required (includes {gas:.3f} GRAM gas fee)."
    )
    LOW_TON_BALANCE = LOW_GRAM_BALANCE
    LOW_USDT_BALANCE = (
        "Insufficient USDT balance: {balance:.4f} USDT available, "
        "{required:.4f} USDT required."
    )
    GRAM_BALANCE_CHECK_FAILED = "Failed to fetch GRAM balance: {exc}"
    TON_BALANCE_CHECK_FAILED = GRAM_BALANCE_CHECK_FAILED
    USDT_BALANCE_CHECK_FAILED = "Failed to fetch USDT balance: {exc}"
    ACCOUNT_INFO_FAILED = "Failed to retrieve wallet account info from TON network: {exc}"
    WALLET_INFO_FAILED = "Failed to retrieve wallet info from TON network: {exc}"


class UnexpectedError(OperationError):
    """Raised when an unexpected error occurs during an API call."""

    UNEXPECTED = "An unexpected error occurred during the operation: {exc}"


class RetryExhaustedError(OperationError):
    """Raised when all retry attempts have been exhausted."""

    EXHAUSTED = (
        "All {attempts} retry attempts exhausted for {context}. "
        "Last error: {last_error}"
    )


class SessionStorageError(OperationError):
    """Raised for session storage read/write errors."""

    SAVE_FAILED = "Failed to save session to storage: {exc}"
    LOAD_FAILED = "Failed to load session from storage: {exc}"


__all__ = [
    "FragmentError",
    "ClientError",
    "ConfigurationError",
    "ConfigError",
    "CookieError",
    "FragmentAPIError",
    "MarketAppAPIError",
    "FragmentPageError",
    "UserNotFoundError",
    "AlreadySubscribedError",
    "AnonymousNumberError",
    "TransactionError",
    "ConfirmationTimeout",
    "SeqnoError",
    "ParseError",
    "VerificationError",
    "OperationError",
    "WalletError",
    "UnexpectedError",
    "RetryExhaustedError",
    "SessionStorageError",
]