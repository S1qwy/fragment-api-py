"""Restricted wallet authentication without importing account cookies."""

from FragmentAPI import ConfigurationError

from _common import make_client, required, run, show_result


async def quote() -> None:
    """Read a Stars quote through a restricted wallet-auth session."""
    async with make_client(cookies=None, wallet_auth=True) as client:
        show_result(await client.get_stars_price(100))


async def restrictions() -> None:
    """Demonstrate local rejection of account-management operations."""
    async with make_client(cookies=None, wallet_auth=True) as client:
        try:
            await client.get_profile()
        except ConfigurationError:
            print("Profile access is blocked in wallet_auth mode.")


async def purchase() -> None:
    """Pay with the configured payer, not with the shared authentication wallet."""
    async with make_client(
        mode="pay",
        cookies=None,
        wallet_auth=True,
    ) as client:
        show_result(await client.purchase_stars(required("FRAGMENT_TARGET"), 100))


if __name__ == "__main__":
    run(
        {"quote": quote, "restrictions": restrictions, "purchase": purchase},
        "restrictions",
    )