'''
Example 13: View your assets and bid history on Fragment.

Demonstrates fetching owned usernames, numbers, gifts,
and bid history with assignment information.
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
    Fetch owned assets and bid history from Fragment.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- My usernames ---
        usernames = await client.get_my_assets(
            item_type="usernames",
        )
        print(f"=== My Usernames ({usernames.total_count} total) ===")
        for asset in usernames.items:
            assigned = f" → {asset.assigned_name}" if asset.assigned_name else ""
            print(f"  {asset.name}{assigned}")

        # --- My gifts ---
        gifts = await client.get_my_assets(
            item_type="gifts",
        )
        print(f"\n=== My Gifts ({gifts.total_count} total) ===")
        for asset in gifts.items:
            desc = f" ({asset.description})" if asset.description else ""
            assigned = f" → {asset.assigned_name}" if asset.assigned_name else ""
            print(f"  {asset.name}{desc}{assigned}")

        # --- My numbers ---
        numbers = await client.get_my_assets(
            item_type="numbers",
        )
        print(f"\n=== My Numbers ({numbers.total_count} total) ===")
        for asset in numbers.items:
            print(f"  {asset.name}")

        # --- My bid history (usernames) ---
        bids = await client.get_my_bids(
            item_type="usernames",
            sort="desc",
        )
        print(f"\n=== My Username Bids ({bids.total_count} total) ===")
        for bid in bids.items[:10]:
            print(
                f"  {bid.name}: {bid.bid} TON — "
                f"{bid.status} — {bid.date}"
            )

        # --- My bid history (gifts) ---
        gift_bids = await client.get_my_bids(
            item_type="gifts",
            sort="desc",
        )
        print(f"\n=== My Gift Bids ({gift_bids.total_count} total) ===")
        for bid in gift_bids.items[:10]:
            desc = f" ({bid.description})" if bid.description else ""
            print(
                f"  {bid.name}{desc}: {bid.bid} TON — "
                f"{bid.status}"
            )


if __name__ == "__main__":
    asyncio.run(main())