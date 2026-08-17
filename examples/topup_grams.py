"""
Telegram Ads GRAM top-up examples.

Demonstrates topping up GRAM to a Telegram Ads account balance.
Requires stel_ton_token cookie and wallet configuration.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}
SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx"


async def check_ads_recipient():
    """Verify an Ads top-up recipient exists."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    recipient = await client.get_ads_topup_recipient("my_channel")
    if recipient:
        print(f"Ads recipient: {recipient.name}")
    else:
        print("Channel not found for Ads top-up")


async def topup_gram_basic():
    """Top up 10 GRAM to a Telegram Ads balance."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.topup_gram(
        username="my_channel",
        amount=10,
        show_sender=True,
    )
    print(f"Top-up successful!")
    print(f"  Transaction: {result.transaction_id}")
    print(f"  To: {result.username}")
    print(f"  Amount: {result.amount} GRAM")


async def topup_ton_alias():
    """Top up using topup_ton (backward-compatible alias for topup_gram)."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.topup_ton(
        username="my_channel",
        amount=5,
    )
    print(f"TON top-up (alias): {result}")


async def topup_via_unified():
    """Top up using the unified purchase() method."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase(
        "gram",
        username="my_channel",
        amount=10,
        payment_method="gram",
    )
    print(f"Unified top-up: {result}")


if __name__ == "__main__":
    asyncio.run(topup_gram_basic())