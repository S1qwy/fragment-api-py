"""Native TON Ads top-ups with historical gram method-name compatibility."""

from _common import make_client, required, run, show_result


async def recipient() -> None:
    """Resolve an Ads top-up recipient."""
    async with make_client() as client:
        show_result(await client.get_ads_topup_recipient(required("FRAGMENT_TARGET")))


async def prepare() -> None:
    """Prepare a one-TON Ads top-up."""
    async with make_client(mode="prepare") as client:
        show_result(await client.topup_ton(required("FRAGMENT_TARGET"), 1))


async def topup() -> None:
    """Broadcast a one-TON Ads top-up."""
    async with make_client(mode="pay") as client:
        show_result(await client.topup_ton(required("FRAGMENT_TARGET"), 1))


async def unified() -> None:
    """Use the unified purchase dispatcher for the same native TON operation."""
    async with make_client(mode="pay") as client:
        show_result(await client.purchase(
            "ton",
            username=required("FRAGMENT_TARGET"),
            amount=1,
            payment_method="ton",
        ))


if __name__ == "__main__":
    run(
        {"recipient": recipient, "prepare": prepare, "topup": topup, "unified": unified},
        "recipient",
    )