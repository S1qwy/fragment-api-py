"""
Error handling examples.

Demonstrates proper exception handling for all error categories:
client configuration errors, API errors, transaction errors,
and wallet errors.
"""

import asyncio
from FragmentAPI import (
    FragmentClient,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentPageError,
    UserNotFoundError,
    AlreadySubscribedError,
    TransactionError,
    VerificationError,
    WalletError,
    UnexpectedError,
    FragmentError,
)


async def handle_configuration_errors():
    """Demonstrate client configuration error handling."""
    try:
        FragmentClient(cookies="")
    except CookieError as e:
        print(f"Cookie error: {e}")

    try:
        FragmentClient(
            cookies="stel_ssid=a; stel_dt=b; stel_token=c",
            seed="only three words",
        )
    except ConfigurationError as e:
        print(f"Config error: {e}")

    try:
        FragmentClient(
            cookies="stel_ssid=a; stel_dt=b; stel_token=c",
            api_provider="unsupported",
        )
    except ConfigurationError as e:
        print(f"Provider error: {e}")


async def handle_wallet_requirement():
    """Demonstrate errors when wallet is required but not configured."""
    client = FragmentClient(
        cookies="stel_ssid=a; stel_dt=b; stel_token=c; stel_ton_token=d",
    )

    try:
        await client.get_wallet()
    except ConfigurationError as e:
        print(f"Wallet required: {e}")

    try:
        await client.purchase_stars("user", 100, payment_method="gram")
    except ConfigurationError as e:
        print(f"Seed required for GRAM payment: {e}")


async def handle_ton_token_requirement():
    """Demonstrate errors when stel_ton_token is missing."""
    client = FragmentClient(
        cookies="stel_ssid=a; stel_dt=b; stel_token=c",
    )

    try:
        await client.get_profile()
    except ConfigurationError as e:
        print(f"TON token required: {e}")

    try:
        await client.topup_gram("user", 10)
    except ConfigurationError as e:
        print(f"TON token for topup: {e}")


async def handle_purchase_errors():
    """Demonstrate error handling during purchase operations."""
    client = FragmentClient(
        cookies={
            "stel_ssid": "a", "stel_dt": "b",
            "stel_token": "c", "stel_ton_token": "d",
        },
        seed="word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24",
        api_key="x" * 48,
    )

    try:
        await client.purchase_stars("nonexistent_user_12345", 100)
    except UserNotFoundError as e:
        print(f"User not found: {e}")
    except FragmentPageError as e:
        print(f"Page error (cookies expired?): {e}")
    except TransactionError as e:
        print(f"Transaction failed: {e}")
    except WalletError as e:
        print(f"Wallet issue: {e}")
    except VerificationError as e:
        print(f"KYC required: {e}")
    except FragmentAPIError as e:
        print(f"API error: {e}")
    except FragmentError as e:
        print(f"General Fragment error: {e}")


async def handle_validation_errors():
    """Demonstrate input validation error handling."""
    client = FragmentClient(
        cookies="stel_ssid=a; stel_dt=b; stel_token=c; stel_ton_token=d",
        seed="word " * 24,
        api_key="x" * 48,
    )

    try:
        await client.purchase_stars("user", 10)
    except ConfigurationError as e:
        print(f"Stars amount too low: {e}")

    try:
        await client.purchase_premium("user", months=5)
    except ConfigurationError as e:
        print(f"Invalid months: {e}")

    try:
        await client.purchase_stars("user", 100, payment_method="bitcoin")
    except ConfigurationError as e:
        print(f"Invalid payment method: {e}")


async def comprehensive_try_except():
    """Recommended error handling pattern for production code."""
    client = FragmentClient(
        cookies={
            "stel_ssid": "a", "stel_dt": "b",
            "stel_token": "c", "stel_ton_token": "d",
        },
        seed="word " * 24,
        api_key="x" * 48,
    )

    try:
        result = await client.purchase_stars("target_user", 100)
        print(f"Success: {result}")

    except ConfigurationError as e:
        print(f"[CONFIG] Check your setup: {e}")

    except UserNotFoundError as e:
        print(f"[USER] User doesn't exist: {e}")

    except AlreadySubscribedError as e:
        print(f"[PREMIUM] Already has Premium: {e}")

    except VerificationError as e:
        print(f"[KYC] Complete verification first: {e}")

    except WalletError as e:
        print(f"[WALLET] Insufficient balance or wallet issue: {e}")

    except TransactionError as e:
        print(f"[TX] Transaction failed: {e}")

    except FragmentPageError as e:
        print(f"[PAGE] Cookies may be expired: {e}")

    except FragmentAPIError as e:
        print(f"[API] Fragment returned error: {e}")

    except UnexpectedError as e:
        print(f"[BUG] Unexpected error: {e}")

    except FragmentError as e:
        print(f"[GENERAL] Fragment error: {e}")


if __name__ == "__main__":
    asyncio.run(handle_configuration_errors())