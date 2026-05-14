'''
Example 19: Comprehensive error handling.

Demonstrates how to catch and handle all exception types
from the Fragment API library hierarchy.
'''

import asyncio
from FragmentAPI import (
    FragmentClient,
    ConfigError,
    CookieError,
    FragmentAPIError,
    FragmentBaseError,
    FragmentPageError,
    OperationError,
    ParseError,
    ProxyError,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
    WalletError,
)


SEED = (
    "word1 word2 word3 word4 word5 word6 "
    "word7 word8 word9 word10 word11 word12 "
    "word13 word14 word15 word16 word17 word18 "
    "word19 word20 word21 word22 word23 word24"
)

COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}


async def main():
    '''
    Demonstrate proper error handling for various operations.
    '''

    # --- Handle initialization errors ---
    try:
        client = FragmentClient(
            seed="only three words here",
            cookies=COOKIES,
        )
    except ConfigError as exc:
        print(f"[ConfigError] {exc}")

    try:
        client = FragmentClient(
            seed=SEED,
            cookies={"stel_ssid": "only_one_key"},
        )
    except CookieError as exc:
        print(f"[CookieError] {exc}")

    try:
        client = FragmentClient(
            seed=SEED,
            cookies=COOKIES,
            wallet_version="V3R1",
        )
    except ConfigError as exc:
        print(f"[ConfigError] Unsupported wallet: {exc}")

    # --- Handle runtime errors ---
    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # Catch specific errors by type
        try:
            result = await client.purchase_stars(
                username="@nonexistent_user_xyz_123",
                amount=500,
            )
        except UserNotFoundError as exc:
            print(f"\n[UserNotFoundError] {exc}")
        except VerificationError as exc:
            print(f"\n[VerificationError] KYC required: {exc}")
        except WalletError as exc:
            print(f"\n[WalletError] Insufficient funds: {exc}")
        except TransactionError as exc:
            print(f"\n[TransactionError] TX failed: {exc}")
        except FragmentPageError as exc:
            print(f"\n[FragmentPageError] Page issue: {exc}")
        except ProxyError as exc:
            print(f"\n[ProxyError] API proxy down: {exc}")
        except ParseError as exc:
            print(f"\n[ParseError] HTML changed: {exc}")
        except FragmentAPIError as exc:
            print(f"\n[FragmentAPIError] API error: {exc}")
        except OperationError as exc:
            print(f"\n[OperationError] Runtime error: {exc}")
        except UnexpectedError as exc:
            print(f"\n[UnexpectedError] Unknown: {exc}")

        # Catch all library errors at once
        try:
            info = await client.get_username_info(
                username="some_username",
            )
        except FragmentBaseError as exc:
            print(f"\n[FragmentBaseError] Caught: {type(exc).__name__}: {exc}")

        # Validate parameters before calling
        try:
            result = await client.purchase_stars(
                username="@user",
                amount=10,
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid amount: {exc}")

        try:
            result = await client.purchase_premium(
                username="@user",
                months=5,
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid months: {exc}")

        try:
            result = await client.place_bid(
                item_type=99,
                slug="test",
                bid=10,
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid item type: {exc}")


if __name__ == "__main__":
    asyncio.run(main())