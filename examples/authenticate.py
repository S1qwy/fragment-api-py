'''
Example: Authenticate with Fragment and obtain session cookies.

Demonstrates how to generate session cookies using a TON wallet
mnemonic phrase. Fragment uses Telegram OIDC for authorization —
after wallet proof the library will show a QR code to scan with
Telegram, or optionally send a phone-based login confirmation.
'''

import asyncio
from FragmentAPI import FragmentClient


SEED = (
    "word1 word2 word3 word4 word5 word6 "
    "word7 word8 word9 word10 word11 word12 "
    "word13 word14 word15 word16 word17 word18 "
    "word19 word20 word21 word22 word23 word24"
)


async def main():
    '''
    Authenticate using a TON wallet seed phrase.

    Option 1 shows QR-based Telegram OIDC flow (default).
    Option 2 shows phone-based confirmation flow.

    Both return a cookies dict that can be saved and reused
    with FragmentClient(cookies=...).
    '''

    cookies_qr = await FragmentClient.authenticate(
        seed=SEED,
        wallet_version="V5R1",
        print_qr=True,
    )

    print("Cookies obtained (QR flow):")
    for key, value in cookies_qr.items():
        print(f"  {key}: {value[:20]}...")

    cookies_phone = await FragmentClient.authenticate(
        seed=SEED,
        wallet_version="V5R1",
        phone="+1234567890",
        timeout=60.0,
    )

    print("\nCookies obtained (phone flow):")
    for key, value in cookies_phone.items():
        print(f"  {key}: {value[:20]}...")


if __name__ == "__main__":
    asyncio.run(main())