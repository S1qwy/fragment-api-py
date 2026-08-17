"""
Marketplace bidding, auction, and asset management examples.

Demonstrates placing bids, starting auctions, selling assets,
managing owned items, and assigning to Telegram accounts.
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


async def place_bid_on_username():
    """Place a bid on a username auction."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.place_bid(
        item_type=1,
        slug="cool_username",
        bid=10,
    )
    print(f"Bid placed!")
    print(f"  Transaction: {result.transaction_id}")
    print(f"  Item: {result.slug}")
    print(f"  Bid: {result.bid} GRAM")
    print(f"  Confirm method: {result.confirm_method}")


async def place_bid_on_number():
    """Place a bid on an anonymous number."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.place_bid(
        item_type=3,
        slug="88812345678",
        bid=50,
    )
    print(f"Number bid: {result}")


async def place_bid_on_gift():
    """Place a bid on a gift."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.place_bid(
        item_type=5,
        slug="plush-pepe-42",
        bid=100,
    )
    print(f"Gift bid: {result}")


async def start_username_auction():
    """Start an auction for an owned username."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.start_auction(
        item_type=1,
        slug="my_username",
        min_amount=5,
    )
    print(f"Auction started: ok={result.ok}, req_id={result.req_id}")


async def sell_gift_fixed_price():
    """Sell a gift at a fixed price (no auction)."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.sell_asset(
        item_type=5,
        slug="my-gift-42",
        price=50,
    )
    print(f"Listed for sale: ok={result.ok}")


async def list_my_assets():
    """List all owned assets by type."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    for item_type in ["usernames", "numbers", "gifts"]:
        assets = await client.get_my_assets(item_type=item_type)
        print(f"\n{item_type.title()} ({assets.total_count} total, rate={assets.gram_rate}):")
        for asset in assets.items:
            assigned = f" -> {asset.assigned_name}" if asset.assigned_name else ""
            print(f"  {asset.name}{assigned}")


async def list_my_bids():
    """List bidding history for all item types."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    for item_type in ["usernames", "numbers", "gifts"]:
        bids = await client.get_my_bids(item_type=item_type, sort="desc")
        print(f"\n{item_type.title()} bids ({bids.total_count} total):")
        for bid in bids.items[:5]:
            print(f"  {bid.name} — {bid.bid} GRAM — {bid.status} — {bid.date}")


async def assign_username_to_telegram():
    """Assign an owned username to a Telegram account."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    accounts = await client.get_assign_accounts(item_type=1, slug="my_username")
    print(f"Available accounts ({len(accounts.accounts)}):")
    print(f"Can disable (don't display): {accounts.can_disable}")

    for acc in accounts.accounts:
        print(f"  [{acc.id}] {acc.name} ({acc.type})")

    if accounts.accounts:
        result = await client.assign_to_telegram(
            item_type=1,
            slug="my_username",
            assign_to=accounts.accounts[0].id,
        )
        print(f"\nAssignment result: ok={result.ok}, message={result.message}")
        if result.need_pay:
            print(f"  Needs payment: req_id={result.req_id}, amount={result.amount}")


if __name__ == "__main__":
    asyncio.run(list_my_assets())