'''
Example 10: Place bids and buy-now on Fragment marketplace items.

Demonstrates placing bids on usernames, numbers, and gifts,
including using the buy-now feature when bid equals buy-now price.
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
    Place bids on various item types and demonstrate buy-now.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Bid on a username (item_type=1) ---
        bid_result = await client.place_bid(
            item_type=1,
            slug="coolname",
            bid=50,
        )
        print("=== Username Bid Result ===")
        print(f"  Transaction ID: {bid_result.transaction_id}")
        print(f"  Item Type:      {bid_result.item_type}")
        print(f"  Slug:           {bid_result.slug}")
        print(f"  Bid:            {bid_result.bid} TON")
        print(f"  Confirm Method: {bid_result.confirm_method}")
        print(f"  Confirm ID:     {bid_result.confirm_id}")

        # --- Bid on an anonymous number (item_type=3) ---
        number_bid = await client.place_bid(
            item_type=3,
            slug="8881234567",
            bid=150,
        )
        print(f"\n=== Number Bid Result ===")
        print(f"  Transaction ID: {number_bid.transaction_id}")
        print(f"  Bid:            {number_bid.bid} TON")

        # --- Buy-now a gift (item_type=5) ---
        # First check the buy-now price
        gift_info = await client.get_gift_info(
            slug="plushpepe-1821",
        )
        buy_now = gift_info.auction.buy_now_price if gift_info.auction else None
        if buy_now:
            buy_result = await client.place_bid(
                item_type=5,
                slug="plushpepe-1821",
                bid=int(buy_now),
            )
            print(f"\n=== Gift Buy-Now Result ===")
            print(f"  Transaction ID: {buy_result.transaction_id}")
            print(f"  Bought for:     {buy_result.bid} TON")


if __name__ == "__main__":
    asyncio.run(main())