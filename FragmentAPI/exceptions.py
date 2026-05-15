'''
Exception hierarchy for Fragment API library.
'''

from __future__ import annotations


class FragmentBaseError(Exception):
    '''Base exception for all Fragment API library errors.'''


class ClientError(FragmentBaseError):
    '''Raised for client configuration and setup problems.'''


class ConfigError(ClientError):
    '''Raised when required client parameters are missing or invalid.'''

    MISSING_PARAMS = "Missing required parameter(s): {keys}."
    BAD_WALLET_VERSION = (
        "Unsupported wallet version '{version}'. Supported: {supported}."
    )
    BAD_MNEMONIC = (
        "Invalid mnemonic: expected 12, 18, or 24 words, got {count}."
    )
    BAD_API_KEY = (
        "Invalid API key: expected at least 48 characters, got {length}."
    )
    INVALID_MONTHS = (
        "Invalid Premium duration: must be 3, 6, or 12 months."
    )
    INVALID_STARS_AMOUNT = (
        "Invalid Stars amount: must be an integer between 50 and 10 000 000."
    )
    INVALID_TON_AMOUNT = (
        "Invalid TON amount: must be an integer between 1 and 1 000 000 000."
    )
    INVALID_USERNAME = (
        "Invalid username '{username}'. "
        "Must be 5-32 characters, only letters, digits, or underscores."
    )
    INVALID_WINNERS_STARS = (
        "Invalid winners count for Stars giveaway: must be 1-5."
    )
    INVALID_WINNERS_PREMIUM = (
        "Invalid winners count for Premium giveaway: must be 1-24000."
    )
    INVALID_STARS_PER_WINNER = (
        "Invalid Stars per winner: must be 500-1 000 000."
    )
    INVALID_PAYMENT_METHOD = (
        "Invalid payment method: must be 'ton' or 'usdt_ton'."
    )
    INVALID_GIVEAWAY_PACKAGE = (
        "Invalid Stars giveaway amount: {amount}. "
        "Must be one of: {packages}."
    )
    INVALID_GIVEAWAY_WINNERS = (
        "Invalid winners count: {winners}. "
        "For {amount} stars, winners must be 1 to {max_winners} "
        "(total_stars / 100)."
    )


class CookieError(ClientError):
    '''Raised when cookies are invalid or missing required fields.'''

    PARSE_FAILED = (
        "Failed to parse cookies: expected a JSON string or dict, got: {exc}"
    )
    MISSING_KEYS = (
        "Fragment cookies missing or empty for key(s): {keys}. "
        "Log in at fragment.com and copy fresh cookies."
    )


class FragmentAPIError(FragmentBaseError):
    '''Raised for errors returned by Fragment API responses.'''

    NO_REQUEST_ID = (
        "Fragment did not return a request ID for '{context}'. "
        "Session may have expired — refresh your cookies."
    )


class FragmentPageError(FragmentAPIError):
    '''Raised when Fragment page cannot be fetched or API hash not found.'''

    BAD_STATUS = (
        "Fragment returned HTTP {status} for {url}. "
        "Cookies may be invalid or expired."
    )
    HASH_NOT_FOUND = (
        "Could not extract API hash from {url}. "
        "Page structure may have changed, or you are not logged in."
    )
    ITEM_NOT_FOUND = (
        "Item not found at {url}. Fragment returned HTTP 302 redirect."
    )


class UserNotFoundError(FragmentAPIError):
    '''Raised when target Telegram user is not found on Fragment.'''

    NOT_FOUND = (
        "Telegram user '{username}' was not found on Fragment. "
        "Check the username and make sure the account exists."
    )


class AnonymousNumberError(FragmentAPIError):
    '''Raised for Fragment anonymous number API failures.'''

    NOT_OWNED = (
        "Number '{number}' is not associated with your Fragment account "
        "or has no active sessions to terminate."
    )
    TERMINATE_FAILED = (
        "Failed to terminate sessions for '{number}': {error}"
    )


class TransactionError(FragmentAPIError):
    '''Raised when TON transaction fails to build or broadcast.'''

    INVALID_PAYLOAD = (
        "Fragment returned invalid transaction payload — "
        "'transaction.messages' is missing or empty."
    )
    BROADCAST_FAILED = "Transaction broadcast failed: {exc}"
    BROADCAST_SSL_ERROR = (
        "Transaction broadcast failed due to SSL error: {exc}\n"
        "Fix: run `pip install --upgrade certifi` and retry. "
        "On macOS you may also need to run the 'Install Certificates.command'."
    )
    DUPLICATE_SEQNO = (
        "Transaction rejected: previous transaction with same seqno "
        "is still pending. Wait a few seconds and retry."
    )


class ConfirmationTimeout(TransactionError):
    '''Raised when seqno/balance confirmation times out.

    The TON was likely sent but confirmation was not received
    within the timeout window. Manual check is recommended.
    '''

    TIMEOUT = (
        "Transaction confirmation timed out after {seconds}s. "
        "TON may have been sent — check the blockchain manually. "
        "seqno_before={seqno_before}, balance_before={balance_before:.4f} TON."
    )


class SeqnoError(TransactionError):
    '''Raised when seqno retrieval or validation fails.'''

    FETCH_FAILED = "Failed to fetch wallet seqno: {exc}"
    STALE = (
        "Seqno did not increment after {seconds}s. "
        "Transaction may not have been accepted by the network."
    )


class ParseError(FragmentAPIError):
    '''Raised when Fragment API response cannot be parsed.'''

    UNPARSEABLE = (
        "Failed to parse Fragment response for '{context}': {exc}"
    )


class VerificationError(FragmentAPIError):
    '''Raised when Fragment requires KYC verification.'''

    KYC_REQUIRED = (
        "Fragment requires identity verification (KYC). "
        "Complete verification at https://fragment.com/my/profile and retry."
    )


class OperationError(FragmentBaseError):
    '''Raised for runtime operation failures unrelated to Fragment API.'''


class WalletError(OperationError):
    '''Raised for TON wallet issues.'''

    LOW_BALANCE = (
        "Insufficient balance: {balance:.4f} {currency} available, "
        "{required:.4f} {currency} required "
        "(amount + {gas:.3f} {currency} gas)."
    )
    BALANCE_FAILED = "Failed to fetch wallet balance: {exc}"
    ACCOUNT_INFO_FAILED = "Failed to retrieve wallet account info: {exc}"
    WALLET_INFO_FAILED = "Failed to retrieve wallet info: {exc}"


class ProxyError(OperationError):
    '''Raised when TON API proxy is unavailable.'''

    PROXY_UNAVAILABLE = (
        "TON API proxy at {url} is unavailable: {exc}. "
        "Please provide an api_key parameter to use the "
        "standard tonapi.io endpoint."
    )


class UnexpectedError(OperationError):
    '''Raised when an unexpected error occurs during operation.'''

    UNEXPECTED = "Unexpected error during operation: {exc}"