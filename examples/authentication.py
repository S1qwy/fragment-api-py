"""
Fragment authentication examples.

Demonstrates how to obtain session cookies via TON wallet proof
combined with Telegram OAuth (QR code or phone confirmation).
"""

import asyncio
from FragmentAPI import FragmentClient


async def authenticate_with_qr():
    """Authenticate using QR code scanning flow.

    This will print a QR code to the terminal. Scan it with
    the Telegram app to complete authentication.
    The returned cookies can be saved and reused for future sessions.
    """
    cookies = await FragmentClient.authenticate(
        seed="word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24",
        wallet_version="V5R1",
        print_qr=True,
    )

    print("Authentication successful!")
    print(f"Cookies: {cookies}")

    client = FragmentClient(
        cookies=cookies,
        seed="word1 word2 ... word24",
        api_key="your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx",
    )
    print(f"Client ready: {client}")


async def authenticate_with_phone():
    """Authenticate using phone number confirmation.

    Instead of scanning a QR code, Telegram will send a confirmation
    request to the device associated with the phone number.
    """
    cookies = await FragmentClient.authenticate(
        seed="word1 word2 ... word24",
        wallet_version="V5R1",
        phone="+1234567890",
        print_qr=False,
    )
    print(f"Authenticated via phone: {cookies}")


async def authenticate_with_status_callback():
    """Authenticate with a status callback to track progress."""

    def on_status(status: str, payload):
        """Handle authentication status updates."""
        if status == "qr_link":
            print(f"QR link generated: {payload}")
        elif status == "consumed":
            print("QR code scanned, waiting for confirmation...")
        elif status == "confirmed":
            print("Authentication confirmed by Telegram!")
        elif status == "refresh":
            print(f"QR token refreshed: {payload}")
        elif status == "phone_sent":
            print("Phone confirmation sent, check your Telegram app")

    cookies = await FragmentClient.authenticate(
        seed="word1 word2 ... word24",
        wallet_version="V5R1",
        on_status=on_status,
        print_qr=True,
    )
    print(f"Cookies obtained: {len(cookies)} keys")


if __name__ == "__main__":
    asyncio.run(authenticate_with_qr())