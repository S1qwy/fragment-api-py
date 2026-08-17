"""
Detailed item information retrieval examples.

Demonstrates fetching full details for usernames, numbers, and gifts,
including auction info, bid history, ownership history, and attributes.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = "stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok"


async def get_username_details():
    """Get detailed info about a specific username listing."""
    client = FragmentClient(cookies=COOKIES)

    info = await client.get_username_info("durov")
    print(f"Username:       @{info.username}")
    print(f"Status:         {info.status}")
    print(f"GRAM rate:      {info.gram_rate}")
    print(f"TON rate (alias): {info.ton_rate}")

    if info.auction:
        print(f"Highest bid:    {info.auction.highest_bid} GRAM")
        print(f"Bid step:       {info.auction.bid_step} GRAM")
        print(f"Minimum bid:    {info.auction.minimum_bid} GRAM")
        print(f"Buy now:        {info.auction.buy_now_price} GRAM")
        print(f"Sell price:     {info.auction.sell_price} GRAM")

    if info.auction_end:
        print(f"Auction ends:   {info.auction_end}")

    if info.owner_wallet:
        print(f"Owner wallet:   {info.owner_wallet}")

    if info.purchased_date:
        print(f"Purchased:      {info.purchased_date}")

    print(f"\nBid history ({len(info.bid_history)} entries):")
    for bid in info.bid_history[:5]:
        print(f"  {bid.price} GRAM — {bid.date} — {bid.wallet}")

    if info.bid_history_next_offset:
        print(f"  ... more available (offset: {info.bid_history_next_offset})")

    print(f"\nOwnership history ({len(info.owner_history)} entries):")
    for owner in info.owner_history[:5]:
        print(f"  {owner.price} — {owner.date} — {owner.wallet}")


async def get_number_details():
    """Get detailed info about a specific number listing."""
    client = FragmentClient(cookies=COOKIES)

    info = await client.get_number_info("+88812345678")
    print(f"Number:         {info.display_number}")
    print(f"Status:         {info.status}")
    print(f"Restricted:     {info.restricted}")
    print(f"GRAM rate:      {info.gram_rate}")

    if info.auction:
        print(f"Highest bid:    {info.auction.highest_bid} GRAM")


async def get_gift_details():
    """Get detailed info about a specific gift listing."""
    client = FragmentClient(cookies=COOKIES)

    info = await client.get_gift_info("plush-pepe-42")
    print(f"Gift:           {info.name}")
    print(f"Slug:           {info.slug}")
    print(f"Status:         {info.status}")
    print(f"Image:          {info.image_url}")
    print(f"Sticker:        {info.sticker_url}")
    print(f"Issued:         {info.issued}")

    print(f"\nAttributes ({len(info.attributes)}):")
    for attr in info.attributes:
        rarity_str = f" ({attr.rarity})" if attr.rarity else ""
        print(f"  {attr.name}: {attr.value}{rarity_str}")

    print(f"\nBid history: {len(info.bid_history)} entries")
    print(f"Ownership history: {len(info.owner_history)} entries")


async def load_more_history():
    """Load additional bid/ownership history pages for an item."""
    client = FragmentClient(cookies=COOKIES)

    info = await client.get_username_info("durov")

    if info.bid_history_next_offset:
        more_bids = await client.get_orders_history(
            item_type=1,
            username="durov",
            offset_id=info.bid_history_next_offset,
        )
        print(f"Additional bid history loaded: {more_bids}")

    if info.owner_history_next_offset:
        more_owners = await client.get_owners_history(
            item_type=1,
            username="durov",
            offset_id=info.owner_history_next_offset,
        )
        print(f"Additional ownership history loaded: {more_owners}")


if __name__ == "__main__":
    asyncio.run(get_username_details())