"""Read Stars and Premium prices without enabling automatic payment."""

from _common import make_client, run, show_result


async def stars() -> None:
    """Read available Stars packages."""
    async with make_client() as client:
        show_result(await client.get_stars_prices())


async def custom() -> None:
    """Read an exact Stars quantity quote."""
    async with make_client() as client:
        show_result(await client.get_stars_price(1000))


async def premium() -> None:
    """Read available Premium duration prices."""
    async with make_client() as client:
        show_result(await client.get_premium_prices())


if __name__ == "__main__":
    run({"stars": stars, "custom": custom, "premium": premium}, "stars")