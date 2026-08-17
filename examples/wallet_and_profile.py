"""
Wallet information and profile management examples.

Demonstrates wallet balance checking, profile info retrieval,
and session management on Fragment.
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


async def check_wallet_balance():
    """Fetch and display wallet address, state, GRAM and USDT balances."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    wallet = await client.get_wallet()
    print(f"Address:       {wallet.address}")
    print(f"State:         {wallet.state}")
    print(f"GRAM balance:  {wallet.gram_balance} GRAM")
    print(f"USDT balance:  {wallet.usdt_balance} USDT")

    print(f"TON balance (backward compat): {wallet.balance_ton} TON")
    print(f"USDT balance (alias):          {wallet.balance_usdt} USDT")


async def get_profile_info():
    """Retrieve Fragment account profile information."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    profile = await client.get_profile()
    print(f"Name:              {profile.name}")
    print(f"Username:          @{profile.username}")
    print(f"Photo:             {profile.photo_url}")
    print(f"Identity verified: {profile.identity_verified}")
    print(f"Wallet address:    {profile.wallet_address}")
    print(f"Wallet label:      {profile.wallet_label}")
    print(f"Wallet verified:   {profile.wallet_verified}")


async def manage_sessions():
    """List active sessions and terminate a specific one."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    sessions = await client.get_sessions()
    print(f"Active sessions: {len(sessions)}")

    for session in sessions:
        print(f"  [{session.session_id}] {session.device} - {session.location}")
        print(f"    Date: {session.date}, Current: {session.is_current}")

    if sessions and not sessions[0].is_current:
        success = await client.terminate_session(sessions[0].session_id)
        print(f"Terminated session {sessions[0].session_id}: {success}")


if __name__ == "__main__":
    asyncio.run(check_wallet_balance())