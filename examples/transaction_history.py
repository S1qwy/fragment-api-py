'''
Example 12: View transaction history for Stars, Premium, and Ads.

Demonstrates fetching and displaying all types of
transaction history available on Fragment.
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
    Retrieve Stars, Premium, and Ads topup transaction history.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Stars history (newest first) ---
        stars_history = await client.get_stars_history(
            sort="desc",
        )
        print(f"=== Stars History ({len(stars_history)} entries) ===")
        for tx in stars_history[:10]:
            print(
                f"  @{tx.recipient}: {tx.stars} stars — "
                f"{tx.price_ton} TON — {tx.date}"
            )

        # --- Premium history (oldest first) ---
        premium_history = await client.get_premium_history(
            sort="asc",
        )
        print(f"\n=== Premium History ({len(premium_history)} entries) ===")
        for tx in premium_history[:10]:
            print(
                f"  @{tx.recipient}: {tx.duration} — "
                f"{tx.price_ton} TON — {tx.date}"
            )

        # --- Ads topup history ---
        topup_history = await client.get_topup_history(
            sort="desc",
        )
        print(f"\n=== Ads Topup History ({len(topup_history)} entries) ===")
        for tx in topup_history[:10]:
            print(
                f"  @{tx.recipient}: {tx.amount} TON — {tx.date}"
            )


if __name__ == "__main__":
    asyncio.run(main())