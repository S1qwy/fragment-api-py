"""Resolve Stars recipients, prepare invoices, and make explicit purchases."""

from _common import make_client, required, run, show_result


async def recipient() -> None:
    """Resolve a recipient without buying Stars."""
    async with make_client() as client:
        show_result(await client.get_stars_recipient(required("FRAGMENT_TARGET")))


async def prepare() -> None:
    """Prepare an unsigned native TON invoice."""
    async with make_client(mode="prepare") as client:
        show_result(await client.purchase_stars(required("FRAGMENT_TARGET"), 100))


async def purchase() -> None:
    """Broadcast one native TON purchase and inspect fulfillment status."""
    async with make_client(mode="pay") as client:
        show_result(await client.purchase_stars(
            required("FRAGMENT_TARGET"),
            100,
            payment_method="ton",
        ))


async def usdt() -> None:
    """Purchase using USDT on TON with token and native balance checks."""
    async with make_client(mode="pay") as client:
        show_result(await client.purchase_stars(
            required("FRAGMENT_TARGET"),
            100,
            payment_method="usdt_ton",
        ))


async def hidden_sender() -> None:
    """Request a purchase without displaying the sender in the service notification."""
    async with make_client(mode="pay") as client:
        show_result(await client.purchase(
            {
                "type": "stars",
                "username": required("FRAGMENT_TARGET"),
                "amount": 100,
                "show_sender": False,
            },
            payment_method="ton",
        ))


if __name__ == "__main__":
    run(
        {
            "recipient": recipient,
            "prepare": prepare,
            "purchase": purchase,
            "usdt": usdt,
            "hidden-sender": hidden_sender,
        },
        "recipient",
    )