"""Read and manage only user-owned anonymous-number sessions."""

import asyncio

from _common import (
    make_client,
    require_execution,
    required,
    run,
)


async def code() -> None:
    """Report whether a login code exists without logging the code itself."""
    async with make_client(account=True) as client:
        result = await client.get_login_code(required("FRAGMENT_NUMBER"))
        print(f"Pending code available: {result.code is not None}")
        print(f"Active sessions: {result.active_sessions}")


async def poll() -> None:
    """Poll for a pending login code within a bounded interval."""
    async with make_client(account=True) as client:
        number = required("FRAGMENT_NUMBER")
        for _ in range(30):
            result = await client.get_login_code(number)
            if result.code:
                print("A login code is available. Handle it as a secret.")
                return
            await asyncio.sleep(2)
        print("No code appeared within the polling interval.")


async def enable() -> None:
    """Enable code delivery for the configured owned number."""
    require_execution()
    async with make_client(account=True) as client:
        await client.toggle_login_codes(required("FRAGMENT_NUMBER"), True)
        print("Code delivery enabled.")


async def disable() -> None:
    """Disable code delivery for the configured owned number."""
    require_execution()
    async with make_client(account=True) as client:
        await client.toggle_login_codes(required("FRAGMENT_NUMBER"), False)
        print("Code delivery disabled.")


async def terminate() -> None:
    """Terminate Telegram sessions associated with the configured owned number."""
    require_execution()
    async with make_client(account=True) as client:
        result = await client.terminate_sessions(required("FRAGMENT_NUMBER"))
        print(result.message or "Session termination request processed.")


if __name__ == "__main__":
    run(
        {
            "code": code,
            "poll": poll,
            "enable": enable,
            "disable": disable,
            "terminate": terminate,
        },
        "code",
    )