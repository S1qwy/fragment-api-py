'''
Example 08: Search the Fragment marketplace.

Demonstrates searching for usernames, anonymous numbers,
and gifts with various filters, sorting, and pagination.
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
    Search usernames, numbers, and gifts on Fragment marketplace.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Search usernames ---
        usernames = await client.search_usernames(
            query="crypto",
            sort="price_asc",
            filter="sale",
        )
        print(f"=== Usernames ({len(usernames.items)} found) ===")
        for item in usernames.items[:5]:
            print(
                f"  {item['name']}: {item['price']} TON "
                f"— {item['status']}"
            )
        if usernames.next_offset_id:
            print(f"  Next page: offset_id={usernames.next_offset_id}")

        # --- Paginate to next page ---
        if usernames.next_offset_id:
            page2 = await client.search_usernames(
                query="crypto",
                sort="price_asc",
                filter="sale",
                offset_id=usernames.next_offset_id,
            )
            print(f"  Page 2: {len(page2.items)} items")

        # --- Search anonymous numbers ---
        numbers = await client.search_numbers(
            query="888",
            sort="price_desc",
            filter="auction",
        )
        print(f"\n=== Numbers ({len(numbers.items)} found) ===")
        for item in numbers.items[:5]:
            print(
                f"  {item['name']}: {item['price']} TON "
                f"— {item['status']}"
            )

        # --- Search gifts ---
        gifts = await client.search_gifts(
            query="",
            collection="artisanbrick",
            sort="price_asc",
            filter="sale",
        )
        print(f"\n=== Gifts ({len(gifts.items)} found) ===")
        for item in gifts.items[:5]:
            print(
                f"  {item['name']}: {item['price']} TON "
                f"— {item['status']}"
            )
        if gifts.next_offset:
            print(f"  Next page: offset={gifts.next_offset}")

        # --- Search gifts with attribute filters ---
        filtered_gifts = await client.search_gifts(
            query="",
            collection="artisanbrick",
            view="Model",
            attr={"Model": ["Duck"]},
        )
        print(
            f"\n  Filtered gifts (Duck model): "
            f"{len(filtered_gifts.items)} found"
        )


if __name__ == "__main__":
    asyncio.run(main())