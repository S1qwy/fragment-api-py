'''
Example 14: Assign assets to Telegram accounts and manage auctions.

Demonstrates listing available Telegram accounts for assignment,
assigning/unassigning usernames and gifts, starting auctions,
and selling at fixed prices.
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
    Assign assets, start auctions, and sell items on Fragment.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- List available Telegram accounts ---
        accounts_result = await client.get_assign_accounts(
            item_type=1,
            slug="myusername",
        )
        print("=== Available Telegram Accounts ===")
        print(f"  Can disable display: {accounts_result.can_disable}")
        for acc in accounts_result.accounts:
            print(
                f"  ID: {acc.id} — {acc.name} ({acc.type})"
            )

        # --- Assign username to a Telegram account ---
        if accounts_result.accounts:
            assign_result = await client.assign_to_telegram(
                item_type=1,
                slug="myusername",
                assign_to=accounts_result.accounts[0].id,
            )
            print(f"\n=== Assign Result ===")
            print(f"  OK:          {assign_result.ok}")
            print(f"  Message:     {assign_result.message}")
            print(f"  Need Pay:    {assign_result.need_pay}")
            print(f"  Assign Name: {assign_result.assign_name}")

        # --- Remove assignment (set assign_to=None) ---
        unassign_result = await client.assign_to_telegram(
            item_type=1,
            slug="myusername",
            assign_to=None,
        )
        print(f"\n  Unassign result: {unassign_result.ok}")

        # --- Start an auction (min bid, no buy-now) ---
        auction_result = await client.start_auction(
            item_type=1,
            slug="myusername",
            min_amount=10,
            max_amount=0,
        )
        print(f"\n=== Start Auction Result ===")
        print(f"  OK:     {auction_result.ok}")
        print(f"  Req ID: {auction_result.req_id}")

        # --- Sell at fixed price ---
        sell_result = await client.sell_asset(
            item_type=5,
            slug="plushpepe-1821",
            price=100,
        )
        print(f"\n=== Sell Asset Result ===")
        print(f"  OK:     {sell_result.ok}")
        print(f"  Req ID: {sell_result.req_id}")

        # --- Start auction with buy-now price ---
        auction_buynow = await client.start_auction(
            item_type=1,
            slug="anotherusername",
            min_amount=50,
            max_amount=500,
        )
        print(f"\n  Auction with buy-now: {auction_buynow.ok}")


if __name__ == "__main__":
    asyncio.run(main())