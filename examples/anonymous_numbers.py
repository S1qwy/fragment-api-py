"""
Anonymous number management examples.

Demonstrates login code retrieval, code toggling, and session
termination for Fragment anonymous phone numbers.
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


async def get_login_code():
    """Fetch the current pending login code for an anonymous number."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.get_login_code("+88812345678")
    print(f"Number:          {result.number}")
    print(f"Login code:      {result.code}")
    print(f"Active sessions: {result.active_sessions}")


async def poll_login_code():
    """Poll for login code until one appears (useful for automation)."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    number = "+88812345678"
    print(f"Polling login code for {number}...")

    for attempt in range(30):
        result = await client.get_login_code(number)
        if result.code:
            print(f"Code received: {result.code}")
            return result.code

        print(f"  Attempt {attempt + 1}: no code yet...")
        await asyncio.sleep(2)

    print("Timed out waiting for login code")
    return None


async def toggle_login_codes():
    """Enable and disable login code delivery."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    number = "+88812345678"

    await client.toggle_login_codes(number, can_receive=True)
    print(f"Login codes ENABLED for {number}")

    await client.toggle_login_codes(number, can_receive=False)
    print(f"Login codes DISABLED for {number}")


async def terminate_all_sessions():
    """Terminate all active Telegram sessions for an anonymous number."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.terminate_sessions("+88812345678")
    print(f"Sessions terminated for {result.number}")
    print(f"Message: {result.message}")


if __name__ == "__main__":
    asyncio.run(get_login_code())