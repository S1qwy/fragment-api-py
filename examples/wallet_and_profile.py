"""Inspect the payer wallet, account profile, and user-owned Fragment sessions."""

from _common import (
    make_client,
    require_execution,
    required,
    run,
    show_result,
)


async def wallet() -> None:
    """Read the configured payer wallet rather than the shared auth wallet."""
    async with make_client(mode="wallet") as client:
        show_result(await client.get_wallet())


async def profile() -> None:
    """Read the authenticated user's profile."""
    async with make_client(account=True) as client:
        show_result(await client.get_profile())


async def sessions() -> None:
    """List Fragment sessions without terminating any of them."""
    async with make_client(account=True) as client:
        for item in await client.get_sessions():
            show_result(item)


async def terminate() -> None:
    """Terminate only the explicitly supplied Fragment session identifier."""
    require_execution()
    async with make_client(account=True) as client:
        result = await client.terminate_session(required("FRAGMENT_TERMINATE_SESSION_ID"))
        print(f"Termination accepted: {result}")


async def refresh() -> None:
    """Refresh wallet proof without starting Telegram OAuth."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        await client.refresh_cookies()
        print("Wallet proof refreshed. Cookie values were not printed.")


if __name__ == "__main__":
    run(
        {
            "wallet": wallet,
            "profile": profile,
            "sessions": sessions,
            "terminate": terminate,
            "refresh": refresh,
        },
        "profile",
    )