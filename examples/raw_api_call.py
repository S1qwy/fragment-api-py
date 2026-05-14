'''
Example 18: Send raw requests to Fragment API.

Demonstrates using the low-level `call` method to invoke
any Fragment API method directly, including undocumented ones.
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
    Use the raw call method to invoke Fragment API endpoints.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Search for a Premium recipient ---
        result = await client.call(
            method="searchPremiumGiftRecipient",
            data={
                "query": "@durov",
                "months": "3",
            },
            page_url="https://fragment.com/premium/gift",
        )
        print("=== Search Premium Recipient ===")
        if result.get("found"):
            found = result["found"]
            print(f"  Recipient ID: {found.get('recipient')}")
            print(f"  Name:         {found.get('name')}")
        else:
            print(f"  Error: {result.get('error', 'Not found')}")

        # --- Search for a Stars recipient ---
        stars_result = await client.call(
            method="searchStarsRecipient",
            data={
                "query": "@username",
                "quantity": "",
            },
            page_url="https://fragment.com/stars",
        )
        print(f"\n=== Search Stars Recipient ===")
        print(f"  Found: {bool(stars_result.get('found'))}")

        # --- Update Stars prices for custom amount ---
        price_result = await client.call(
            method="updateStarsPrices",
            data={
                "stars": "0",
                "quantity": "12345",
            },
            page_url="https://fragment.com/stars",
        )
        print(f"\n=== Custom Stars Price ===")
        print(f"  Response: {price_result.get('cur_price', 'N/A')[:50]}...")

        # --- Search auctions ---
        auctions = await client.call(
            method="searchAuctions",
            data={
                "type": "usernames",
                "query": "vip",
                "sort": "price_asc",
                "filter": "sale",
            },
            page_url="https://fragment.com",
        )
        print(f"\n=== Search Auctions ===")
        has_html = bool(auctions.get("html"))
        print(f"  Has results: {has_html}")
        if auctions.get("next_offset_id"):
            print(f"  Next offset: {auctions['next_offset_id']}")

        # --- Check item sellability ---
        can_sell = await client.call(
            method="canSellItem",
            data={
                "type": "1",
                "username": "myusername",
                "auction": "true",
            },
            page_url="https://fragment.com/username/myusername",
        )
        print(f"\n=== Can Sell Item ===")
        print(f"  OK: {can_sell.get('ok', False)}")

        # --- Confirm request (after transaction) ---
        # This is typically called automatically after purchases,
        # but can also be called manually:
        #
        # confirm = await client.confirm_request(
        #     req_id="some_request_id",
        #     boc="base64_encoded_boc_string",
        #     referer="stars/buy",
        # )
        # print(f"Confirm result: {confirm}")


if __name__ == "__main__":
    asyncio.run(main())