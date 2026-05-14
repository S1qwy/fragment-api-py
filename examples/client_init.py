'''
Example 02: Initialize FragmentClient with various cookie formats.

Shows how to create an async FragmentClient instance using
dict cookies, JSON string cookies, or raw cookie strings.
'''

import asyncio
import json
from FragmentAPI import FragmentClient


async def main():
    '''
    Demonstrate three ways to pass cookies to FragmentClient.
    '''

    seed = (
        "word1 word2 word3 word4 word5 word6 "
        "word7 word8 word9 word10 word11 word12 "
        "word13 word14 word15 word16 word17 word18 "
        "word19 word20 word21 word22 word23 word24"
    )

    # --- Option 1: Dict cookies ---
    cookies_dict = {
        "stel_ssid": "your_ssid_value",
        "stel_dt": "-180",
        "stel_token": "your_token_value",
        "stel_ton_token": "your_ton_token_value",
    }

    async with FragmentClient(
        seed=seed,
        cookies=cookies_dict,
        wallet_version="V5R1",
    ) as client:
        print(f"Client initialized: {client}")
        wallet = await client.get_wallet()
        print(f"Wallet address: {wallet.address}")
        print(f"Balance: {wallet.balance_ton} TON, {wallet.balance_usdt} USDT")

    # --- Option 2: JSON string cookies ---
    cookies_json = json.dumps(cookies_dict)

    async with FragmentClient(
        seed=seed,
        cookies=cookies_json,
        wallet_version="V5R1",
    ) as client:
        print(f"\nClient from JSON: {client}")

    # --- Option 3: Raw cookie string ---
    cookies_raw = (
        "stel_ssid=your_ssid_value; "
        "stel_dt=-180; "
        "stel_token=your_token_value; "
        "stel_ton_token=your_ton_token_value"
    )

    async with FragmentClient(
        seed=seed,
        cookies=cookies_raw,
        wallet_version="V5R1",
        api_key="your_tonapi_key_here_at_least_48_characters_long_abcdef",
        timeout=45.0,
    ) as client:
        print(f"\nClient from raw string: {client}")


if __name__ == "__main__":
    asyncio.run(main())