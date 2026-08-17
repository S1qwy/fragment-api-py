"""
Raw Fragment API call examples.

Demonstrates using the low-level call() method for direct API access,
and the confirm_request() method for manual transaction confirmation.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}


async def raw_search_call():
    """Make a raw searchAuctions API call."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.call(
        "searchAuctions",
        {
            "type": "usernames",
            "query": "test",
            "sort": "price_asc",
        },
    )
    print(f"Raw result keys: {list(result.keys())}")
    if "html" in result:
        print(f"HTML length: {len(result['html'])} chars")
    if "next_offset_id" in result:
        print(f"Next offset: {result['next_offset_id']}")


async def raw_update_prices():
    """Make a raw updateStarsPrices API call."""
    client = FragmentClient(cookies=COOKIES)

    result = await client.call(
        "updateStarsPrices",
        {
            "stars": "0",
            "quantity": "1000",
        },
        page_url="https://fragment.com/stars",
    )
    print(f"Price update result: {result}")


async def manual_confirm_request():
    """Manually confirm a transaction after broadcasting.

    This is useful when you manage the transaction lifecycle
    yourself and need to notify Fragment of the broadcast.
    """
    client = FragmentClient(cookies=COOKIES)

    result = await client.confirm_request(
        req_id="12345",
        boc="base64_encoded_boc_here",
        referer="stars/buy",
    )
    print(f"Confirm result: {result}")


if __name__ == "__main__":
    asyncio.run(raw_search_call())