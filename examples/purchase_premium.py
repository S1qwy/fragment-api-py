"""
Premium gift purchase examples.

Demonstrates gifting Telegram Premium to users with
different durations and payment methods.
"""

import asyncio
from FragmentAPI import FragmentClient, EvmPaymentResult, PurchaseResult


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}
SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx"


async def check_premium_recipient():
    """Verify a user can receive Premium before purchasing."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    recipient = await client.get_premium_recipient("durov", months=3)
    if recipient:
        print(f"Recipient found: {recipient.name}")
        if recipient.myself:
            print("Warning: this is your own account!")
    else:
        print("User not found or cannot receive Premium")


async def gift_premium_3_months():
    """Gift 3 months of Telegram Premium."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase_premium(
        username="durov",
        months=3,
        show_sender=True,
        payment_method="gram",
    )

    if isinstance(result, PurchaseResult):
        print(f"Premium gifted!")
        print(f"  Transaction: {result.transaction_id}")
        print(f"  To: {result.username}")
        print(f"  Duration: {result.amount} months")


async def gift_premium_12_months():
    """Gift 12 months of Telegram Premium for maximum savings."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase_premium(
        username="durov",
        months=12,
        payment_method="gram",
    )
    print(f"12-month Premium result: {result}")


async def gift_premium_evm():
    """Gift Premium using USDC on Base network."""
    client = FragmentClient(
        cookies={
            "stel_ssid": "your_ssid",
            "stel_dt": "-180",
            "stel_token": "your_token",
        },
    )

    result = await client.purchase_premium(
        username="durov",
        months=3,
        payment_method="usdc_base",
    )

    if isinstance(result, EvmPaymentResult):
        print(f"EVM invoice for Premium: {result.invoice}")


async def gift_premium_unified():
    """Gift Premium using the unified purchase() method."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase(
        "premium",
        username="durov",
        months=6,
        payment_method="gram",
    )
    print(f"Unified Premium purchase: {result}")


if __name__ == "__main__":
    asyncio.run(gift_premium_3_months())