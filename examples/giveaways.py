"""Stars package giveaways and Premium giveaways with explicit payment actions."""

from _common import make_client, required, run, show_result


async def recipients() -> None:
    """Resolve giveaway channels without starting a giveaway."""
    async with make_client() as client:
        channel = required("FRAGMENT_CHANNEL")
        show_result(await client.get_giveaway_stars_recipient(
            channel,
            winners=10,
            amount=1000,
        ))
        show_result(await client.get_giveaway_premium_recipient(
            channel,
            winners=5,
            months=3,
        ))


async def prepare() -> None:
    """Prepare a Stars giveaway using a total-package amount."""
    async with make_client(mode="prepare") as client:
        show_result(await client.giveaway_stars(
            required("FRAGMENT_CHANNEL"),
            winners=10,
            amount=1000,
        ))


async def stars() -> None:
    """Broadcast one giveaway invoice for 1000 total Stars."""
    async with make_client(mode="pay") as client:
        show_result(await client.giveaway_stars(
            required("FRAGMENT_CHANNEL"),
            winners=10,
            amount=1000,
        ))


async def premium() -> None:
    """Broadcast a giveaway for five three-month Premium subscriptions."""
    async with make_client(mode="pay") as client:
        show_result(await client.giveaway_premium(
            required("FRAGMENT_CHANNEL"),
            winners=5,
            months=3,
        ))


if __name__ == "__main__":
    run(
        {"recipients": recipients, "prepare": prepare, "stars": stars, "premium": premium},
        "recipients",
    )