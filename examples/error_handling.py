'''
Example: Comprehensive error handling.

Demonstrates how to catch and handle all exception types
from the Fragment API library hierarchy, including the
new batch_purchase specific errors.
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
    Demonstrate proper error handling for various operations
    including initialization, single purchases, and batch purchases.
    '''

    try:
        FragmentClient(
            seed="only three words here",
            cookies=COOKIES,
        )
    except ConfigError as exc:
        print(f"[ConfigError] Bad mnemonic: {exc}")

    try:
        FragmentClient(
            seed=SEED,
            cookies={"stel_ssid": "only_one_key"},
        )
    except CookieError as exc:
        print(f"[CookieError] Missing keys: {exc}")

    try:
        FragmentClient(
            seed=SEED,
            cookies=COOKIES,
            wallet_version="V3R1",
        )
    except ConfigError as exc:
        print(f"[ConfigError] Bad wallet version: {exc}")

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        try:
            await client.purchase_stars(
                username="@nonexistent_user_xyz_123",
                amount=500,
            )
        except UserNotFoundError as exc:
            print(f"\n[UserNotFoundError] {exc}")
        except VerificationError as exc:
            print(f"\n[VerificationError] {exc}")
        except WalletError as exc:
            print(f"\n[WalletError] {exc}")
        except TransactionError as exc:
            print(f"\n[TransactionError] {exc}")
        except FragmentPageError as exc:
            print(f"\n[FragmentPageError] {exc}")
        except ProxyError as exc:
            print(f"\n[ProxyError] {exc}")
        except ParseError as exc:
            print(f"\n[ParseError] {exc}")
        except FragmentAPIError as exc:
            print(f"\n[FragmentAPIError] {exc}")
        except OperationError as exc:
            print(f"\n[OperationError] {exc}")
        except UnexpectedError as exc:
            print(f"\n[UnexpectedError] {exc}")

        try:
            await client.get_username_info(
                username="some_username",
            )
        except FragmentBaseError as exc:
            print(f"\n[FragmentBaseError] {type(exc).__name__}: {exc}")

        try:
            await client.purchase_stars(
                username="@user",
                amount=10,
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid stars amount: {exc}")

        try:
            await client.purchase_premium(
                username="@user",
                months=5,
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid months: {exc}")

        try:
            await client.place_bid(
                item_type=99,
                slug="test",
                bid=10,
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid item type: {exc}")

        try:
            await client.batch_purchase(
                items=[
                    {"type": "stars", "username": "@user1", "amount": 500},
                ],
                payment_method="usdt_eth",
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Batch EVM not supported: {exc}")

        try:
            await client.batch_purchase(
                items=[
                    {"type": "invalid", "username": "@user1", "amount": 100},
                ],
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid batch item type: {exc}")

        try:
            await client.batch_purchase(
                items=[
                    {"type": "premium", "username": "@user1", "months": 5},
                ],
            )
        except ConfigError as exc:
            print(f"\n[ConfigError] Invalid batch premium months: {exc}")

        try:
            result = await client.batch_purchase(
                items=[
                    {"type": "stars", "username": "@user1", "amount": 500},
                    {"type": "stars", "username": "@user2", "amount": 1000},
                ],
            )
            print(f"\nBatch result: {result}")
        except WalletError as exc:
            print(f"\n[WalletError] Batch insufficient balance: {exc}")
        except FragmentBaseError as exc:
            print(f"\n[FragmentBaseError] Batch error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())