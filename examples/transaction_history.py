"""Read user-owned purchase history using a full-account cookie session."""

from _common import make_client, run, show_result


async def stars() -> None:
    """Read Stars purchases, newest first."""
    async with make_client(account=True) as client:
        for item in await client.get_stars_history(sort="desc"):
            show_result(item)


async def premium() -> None:
    """Read Premium gifts, newest first."""
    async with make_client(account=True) as client:
        for item in await client.get_premium_history(sort="desc"):
            show_result(item)


async def topups() -> None:
    """Read Ads top-up history."""
    async with make_client(account=True) as client:
        for item in await client.get_topup_history(sort="asc"):
            show_result(item)


if __name__ == "__main__":
    run({"stars": stars, "premium": premium, "topups": topups}, "stars")