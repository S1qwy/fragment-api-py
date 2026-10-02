"""Explicit Telegram authentication with persistent, non-printed cookies."""

import os

from FragmentAPI import FileSessionStorage, FragmentClient

from _common import required, run, setting


async def authenticate(phone: str | None = None) -> None:
    """Authenticate interactively and save cookies without printing their values."""
    cookies = await FragmentClient.authenticate(
        seed=required("TON_SEED"),
        wallet_version=setting("TON_WALLET_VERSION", "V5R1"),
        phone=phone,
        print_qr=phone is None,
        proxy=os.getenv("FRAGMENT_PROXY") or None,
        on_status=on_status,
    )
    storage = FileSessionStorage(setting("FRAGMENT_SESSION_DIR", ".fragment_sessions"))
    await storage.save(
        setting("FRAGMENT_SESSION_ID", "default"),
        cookies,
        {"mode": "cookies"},
    )
    print("Authentication completed. Session saved locally.")


def on_status(status: str, payload: object) -> None:
    """Report progress without logging OAuth tokens or cookie values."""
    if status != "qr_link":
        print(f"Authentication status: {status}")


async def qr() -> None:
    """Display the interactive QR authentication link."""
    await authenticate()


async def phone() -> None:
    """Request Telegram approval using the configured phone number."""
    await authenticate(required("TELEGRAM_PHONE"))


if __name__ == "__main__":
    run({"qr": qr, "phone": phone}, "qr")