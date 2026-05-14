'''
Example 01: Authenticate with Fragment and obtain session cookies.

Demonstrates how to generate session cookies using a TON wallet
mnemonic phrase, with optional Telegram phone-based authorization.
'''

import asyncio
from FragmentAPI import FragmentClient


async def main():
    '''
    Authenticate using only a TON wallet seed phrase.
    Returns cookies dict that can be saved and reused.
    '''

    # --- Option 1: Wallet-only authentication ---
    cookies = await FragmentClient.authenticate(
        seed=(
            "word1 word2 word3 word4 word5 word6 "
            "word7 word8 word9 word10 word11 word12 "
            "word13 word14 word15 word16 word17 word18 "
            "word19 word20 word21 word22 word23 word24"
        ),
        wallet_version="V5R1",
    )

    print("Cookies obtained (wallet-only):")
    for key, value in cookies.items():
        print(f"  {key}: {value[:20]}...")

    # --- Option 2: Wallet + Telegram phone authorization ---
    # This will send a login confirmation request to your Telegram app.
    cookies_with_tg = await FragmentClient.authenticate(
        seed=(
            "word1 word2 word3 word4 word5 word6 "
            "word7 word8 word9 word10 word11 word12 "
            "word13 word14 word15 word16 word17 word18 "
            "word19 word20 word21 word22 word23 word24"
        ),
        wallet_version="V5R1",
        telegram_phone="+1234567890",
        timeout=60.0,
    )

    print("\nCookies obtained (wallet + Telegram):")
    for key, value in cookies_with_tg.items():
        print(f"  {key}: {value[:20]}...")


if __name__ == "__main__":
    asyncio.run(main())