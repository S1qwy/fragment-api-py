"""
Fragment marketplace search examples.

Demonstrates searching for usernames, numbers, and gifts
with filtering, sorting, and pagination support.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = "stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok"


async def search_usernames_basic():
    """Search for usernames with default settings (browse all)."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.search_usernames()
    print(f"Found {len(result.items)} usernames")
    for item in result.items[:5]:
        print(f"  {item['name']} — {item['status']} — {item['price']} GRAM")

    if result.next_offset_id:
        print(f"Next page cursor: {result.next_offset_id}")


async def search_usernames_filtered():
    """Search usernames with query, sorting, and filtering."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.search_usernames(
        query="crypto",
        sort="price_asc",
        filter="sale",
    )
    print(f"Cheapest 'crypto' usernames for sale:")
    for item in result.items[:10]:
        print(f"  @{item['name']} — {item['price']} GRAM")


async def search_usernames_paginated():
    """Paginate through all available usernames."""
    client = FragmentClient(cookies=COOKIES)

    all_items = []
    offset_id = None

    for page in range(3):
        result = await client.search_usernames(
            sort="price_asc",
            filter="sale",
            offset_id=offset_id,
        )
        all_items.extend(result.items)
        print(f"Page {page + 1}: {len(result.items)} items (total: {len(all_items)})")

        if not result.next_offset_id:
            break
        offset_id = result.next_offset_id

    print(f"Total collected: {len(all_items)} usernames")


async def search_numbers():
    """Search for anonymous Telegram numbers."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.search_numbers(
        query="888",
        sort="price_asc",
        filter="sale",
    )
    print(f"Numbers matching '888': {len(result.items)}")
    for item in result.items[:5]:
        print(f"  {item['name']} — {item['price']} GRAM — {item['status']}")


async def search_gifts_basic():
    """Search the gifts marketplace."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.search_gifts(
        sort="price_asc",
        filter="sale",
    )
    print(f"Gifts for sale: {len(result.items)}")
    for item in result.items[:5]:
        print(f"  {item['name']} — {item['price']} GRAM")

    if result.next_offset:
        print(f"Next page offset: {result.next_offset}")


async def search_gifts_with_collection():
    """Search gifts within a specific collection."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.search_gifts(
        collection="plush-pepe",
        sort="price_asc",
    )
    print(f"Plush Pepe gifts: {len(result.items)}")
    for item in result.items[:5]:
        print(f"  {item['name']} — {item['price']} GRAM")


async def search_gifts_with_attributes():
    """Search gifts with attribute filters."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.search_gifts(
        collection="plush-pepe",
        attr={
            "backdrop": ["Starry Night"],
            "model": ["Rare Pepe"],
        },
    )
    print(f"Filtered gifts: {len(result.items)}")


if __name__ == "__main__":
    asyncio.run(search_usernames_basic())