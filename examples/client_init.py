'''
Example: Initialize FragmentClient with various cookie formats.

Shows how to create an async FragmentClient instance using
dict cookies, JSON string cookies, raw cookie strings,
or no cookies at all (no-cookie / no-KYC mode).
'''

import asyncio
import json
from FragmentAPI import FragmentClient


SEED = (
    "word1 word2 word3 word4 word5 word6 "
    "word7 word8 word9 word10 word11 word12 "
    "word13 word14 word15 word16 word17 word18 "
    "word19 word20 word21 word22 word23 word24"
)


async def main():
    '''
    Demonstrate four ways to initialize FragmentClient.

    1. Dict cookies — pass a plain Python dict.
    2. JSON string cookies — pass a JSON-serialized string.
    3. Raw cookie string — pass a semicolon-separated string.
    4. No-cookie mode — pass cookies=None (only seed required).
    '''

    cookies_dict = {
        "stel_ssid": "your_ssid_value",
        "stel_dt": "-180",
        "stel_token": "your_token_value",
        "stel_ton_token": "your_ton_token_value",
    }

    async with FragmentClient(
        seed=SEED,
        cookies=cookies_dict,
        wallet_version="V5R1",
    ) as client:
        print(f"Dict cookies: {client}")
        wallet = await client.get_wallet()
        print(f"  Address: {wallet.address}")
        print(f"  Balance: {wallet.balance_ton} TON, {wallet.balance_usdt} USDT")

    cookies_json = json.dumps(cookies_dict)

    async with FragmentClient(
        seed=SEED,
        cookies=cookies_json,
        wallet_version="V5R1",
    ) as client:
        print(f"\nJSON cookies: {client}")

    cookies_raw = (
        "stel_ssid=your_ssid_value; "
        "stel_dt=-180; "
        "stel_token=your_token_value; "
        "stel_ton_token=your_ton_token_value"
    )

    async with FragmentClient(
        seed=SEED,
        cookies=cookies_raw,
        wallet_version="V5R1",
        api_key="your_tonapi_key_here_at_least_48_characters_long_abcdef",
        timeout=45.0,
    ) as client:
        print(f"\nRaw string cookies: {client}")

    async with FragmentClient(
        seed=SEED,
        wallet_version="V4R2",
    ) as client:
        print(f"\nNo-cookie mode: {client}")
        print(f"  has_cookies={client.has_cookies}")
        wallet = await client.get_wallet()
        print(f"  Address: {wallet.address}")


if __name__ == "__main__":
    asyncio.run(main())