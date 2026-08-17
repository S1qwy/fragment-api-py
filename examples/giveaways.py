"""
Giveaway examples for Stars and Premium.

Demonstrates running channel giveaways with different
winner counts, amounts, and payment methods.
"""

import asyncio
from FragmentAPI import FragmentClient, EvmPaymentResult


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}
SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx"


async def check_giveaway_recipients():
    """Verify channel recipients for Stars and Premium giveaways."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    stars_recipient = await client.get_giveaway_stars_recipient(
        channel="my_channel",
        winners=3,
        amount=1500,
    )
    if stars_recipient:
        print(f"Stars giveaway channel: {stars_recipient.name}")

    premium_recipient = await client.get_giveaway_premium_recipient(
        channel="my_channel",
        winners=5,
        months=3,
    )
    if premium_recipient:
        print(f"Premium giveaway channel: {premium_recipient.name}")


async def giveaway_stars_basic():
    """Run a Stars giveaway for 3 winners with 1500 total Stars."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.giveaway_stars(
        channel="my_channel",
        winners=3,
        amount=1500,
        payment_method="gram",
    )

    if not isinstance(result, EvmPaymentResult):
        print(f"Stars giveaway started!")
        print(f"  Transaction: {result.transaction_id}")
        print(f"  Channel: {result.channel}")
        print(f"  Winners: {result.winners}")
        print(f"  Total Stars: {result.amount}")
        print(f"  Stars per winner: {result.amount // result.winners}")


async def giveaway_stars_large():
    """Run a large Stars giveaway with 1,000,000 Stars."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.giveaway_stars(
        channel="my_channel",
        winners=5,
        amount=1_000_000,
    )
    print(f"Large giveaway: {result}")


async def giveaway_premium_basic():
    """Run a Premium giveaway for 10 winners, 3 months each."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.giveaway_premium(
        channel="my_channel",
        winners=10,
        months=3,
        payment_method="gram",
    )

    if not isinstance(result, EvmPaymentResult):
        print(f"Premium giveaway started!")
        print(f"  Transaction: {result.transaction_id}")
        print(f"  Channel: {result.channel}")
        print(f"  Winners: {result.winners}")
        print(f"  Duration: {result.amount} months per winner")


async def giveaway_premium_12_months():
    """Run a 12-month Premium giveaway for 5 winners."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.giveaway_premium(
        channel="my_channel",
        winners=5,
        months=12,
    )
    print(f"12-month giveaway: {result}")


if __name__ == "__main__":
    asyncio.run(giveaway_stars_basic())