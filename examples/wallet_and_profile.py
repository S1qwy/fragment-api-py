'''
Example 03: Wallet info, profile, and session management.

Demonstrates how to check wallet balances, view profile details,
list active Fragment sessions, and terminate specific sessions.
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
    Retrieve wallet, profile, and session data from Fragment.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Wallet info ---
        wallet = await client.get_wallet()
        print("=== Wallet Info ===")
        print(f"  Address:      {wallet.address}")
        print(f"  State:        {wallet.state}")
        print(f"  Balance TON:  {wallet.balance_ton}")
        print(f"  Balance USDT: {wallet.balance_usdt}")

        # --- Profile info ---
        profile = await client.get_profile()
        print("\n=== Profile Info ===")
        print(f"  Name:          {profile.name}")
        print(f"  Username:      @{profile.username}")
        print(f"  Photo URL:     {profile.photo_url}")
        print(f"  KYC Verified:  {profile.identity_verified}")
        print(f"  Wallet Label:  {profile.wallet_label}")
        print(f"  Wallet Addr:   {profile.wallet_address}")
        print(f"  Wallet Verif:  {profile.wallet_verified}")

        # --- Active sessions ---
        sessions = await client.get_sessions()
        print(f"\n=== Active Sessions ({len(sessions)}) ===")
        for s in sessions:
            current = " [CURRENT]" if s.is_current else ""
            print(
                f"  {s.session_id}: {s.device} — "
                f"{s.location} ({s.date}){current}"
            )

        # --- Terminate a non-current session ---
        for s in sessions:
            if not s.is_current and s.session_id:
                success = await client.terminate_session(
                    session_id=s.session_id,
                )
                print(f"\n  Terminated session {s.session_id}: {success}")
                break


if __name__ == "__main__":
    asyncio.run(main())