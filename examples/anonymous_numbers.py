'''
Example 11: Manage anonymous numbers on Fragment.

Demonstrates getting login codes, toggling code delivery,
and terminating all Telegram sessions for anonymous numbers.
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
    Manage login codes and sessions for an anonymous number.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        number = "+888 1234 5678"

        # --- Enable login code delivery ---
        await client.toggle_login_codes(
            number=number,
            can_receive=True,
        )
        print(f"Login codes enabled for {number}")

        # --- Get pending login code ---
        code_result = await client.get_login_code(
            number=number,
        )
        print(f"\n=== Login Code Result ===")
        print(f"  Number:          {code_result.number}")
        print(f"  Code:            {code_result.code}")
        print(f"  Active Sessions: {code_result.active_sessions}")

        if code_result.code:
            print(f"\n  Current login code: {code_result.code}")
        else:
            print("\n  No pending login code at the moment.")

        # --- Disable login code delivery ---
        await client.toggle_login_codes(
            number=number,
            can_receive=False,
        )
        print(f"\nLogin codes disabled for {number}")

        # --- Terminate all Telegram sessions ---
        terminate_result = await client.terminate_sessions(
            number=number,
        )
        print(f"\n=== Terminate Sessions Result ===")
        print(f"  Number:  {terminate_result.number}")
        print(f"  Message: {terminate_result.message}")


if __name__ == "__main__":
    asyncio.run(main())