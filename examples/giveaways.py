'''
Example 07: Run Stars and Premium giveaways in a Telegram channel.

Demonstrates creating channel giveaways for both
Telegram Stars and Premium subscriptions.
'''

import asyncio
from FragmentAPI import FragmentClient


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
    Create Stars and Premium giveaways for a channel.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Stars giveaway ---
        stars_result = await client.giveaway_stars(
            channel="@my_channel",
            winners=3,
            amount=5000,
            payment_method="ton",
        )
        print("=== Stars Giveaway Result ===")
        print(f"  Transaction ID: {stars_result.transaction_id}")
        print(f"  Channel:        {stars_result.channel}")
        print(f"  Winners:        {stars_result.winners}")
        print(f"  Total Stars:    {stars_result.amount}")
        print(f"  Payment:        {stars_result.payment_method}")

        # --- Premium giveaway ---
        premium_result = await client.giveaway_premium(
            channel="@my_channel",
            winners=10,
            months=3,
            payment_method="ton",
        )
        print("\n=== Premium Giveaway Result ===")
        print(f"  Transaction ID: {premium_result.transaction_id}")
        print(f"  Channel:        {premium_result.channel}")
        print(f"  Winners:        {premium_result.winners}")
        print(f"  Months:         {premium_result.amount}")
        print(f"  Payment:        {premium_result.payment_method}")

        # --- Premium giveaway with USDT ---
        usdt_result = await client.giveaway_premium(
            channel="@big_channel",
            winners=100,
            months=12,
            payment_method="usdt_ton",
        )
        print(f"\n  USDT giveaway TX: {usdt_result.transaction_id}")


if __name__ == "__main__":
    asyncio.run(main())