'''
Example 09: Get detailed information about marketplace items.

Demonstrates retrieving full details for usernames, numbers,
and gifts including auction info, bid history, and ownership history.
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
    Fetch detailed info for username, number, and gift items.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Username details ---
        username_info = await client.get_username_info(
            username="durov",
        )
        print("=== Username Info ===")
        print(f"  Username:     @{username_info.username}")
        print(f"  Status:       {username_info.status}")
        print(f"  TON Rate:     {username_info.ton_rate}")
        print(f"  Owner Wallet: {username_info.owner_wallet}")
        print(f"  Purchased:    {username_info.purchased_date}")
        if username_info.auction:
            a = username_info.auction
            print(f"  Highest Bid:  {a.highest_bid}")
            print(f"  Bid Step:     {a.bid_step}")
            print(f"  Minimum Bid:  {a.minimum_bid}")
            print(f"  Sell Price:   {a.sell_price}")
            print(f"  Buy Now:      {a.buy_now_price}")
        print(f"  Auction End:  {username_info.auction_end}")
        print(f"  Bid History:  {len(username_info.bid_history)} entries")
        for bid in username_info.bid_history[:3]:
            print(f"    {bid.price} TON — {bid.date} — {bid.wallet}")
        print(f"  Owner History: {len(username_info.owner_history)} entries")
        for owner in username_info.owner_history[:3]:
            print(f"    {owner.price} — {owner.date} — {owner.wallet}")

        # --- Number details ---
        number_info = await client.get_number_info(
            number="+888 1234 5678",
        )
        print(f"\n=== Number Info ===")
        print(f"  Number:       {number_info.display_number}")
        print(f"  Status:       {number_info.status}")
        print(f"  Restricted:   {number_info.restricted}")
        print(f"  Bid History:  {len(number_info.bid_history)} entries")

        # --- Gift details ---
        gift_info = await client.get_gift_info(
            slug="plushpepe-1821",
        )
        print(f"\n=== Gift Info ===")
        print(f"  Name:         {gift_info.name}")
        print(f"  Status:       {gift_info.status}")
        print(f"  Image URL:    {gift_info.image_url}")
        print(f"  Sticker URL:  {gift_info.sticker_url}")
        print(f"  Issued:       {gift_info.issued}")
        print(f"  Attributes ({len(gift_info.attributes)}):")
        for attr in gift_info.attributes:
            rarity = f" ({attr.rarity})" if attr.rarity else ""
            print(f"    {attr.name}: {attr.value}{rarity}")
        print(f"  Bid History:  {len(gift_info.bid_history)} entries")
        print(f"  Owner History: {len(gift_info.owner_history)} entries")

        # --- Load more bid history (pagination) ---
        if username_info.bid_history_next_offset:
            more_bids = await client.get_orders_history(
                item_type=1,
                username="durov",
                offset_id=username_info.bid_history_next_offset,
            )
            print(f"\n  More bids loaded: {len(more_bids.get('html', ''))}")

        # --- Load more owner history (pagination) ---
        if username_info.owner_history_next_offset:
            more_owners = await client.get_owners_history(
                item_type=1,
                username="durov",
                offset_id=username_info.owner_history_next_offset,
            )
            print(f"  More owners loaded: {len(more_owners.get('html', ''))}")


if __name__ == "__main__":
    asyncio.run(main())