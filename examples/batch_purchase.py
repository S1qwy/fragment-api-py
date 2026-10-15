"""Prepare all invoices and send their messages in one wallet transaction."""

from FragmentAPI import PurchaseItem

from _common import make_client, required, run, show_result


def items() -> list[PurchaseItem]:
    """Build a small batch using explicitly configured recipients."""
    return [
        PurchaseItem(
            type="stars",
            username=required("FRAGMENT_TARGET"),
            amount=100,
        ),
        PurchaseItem(
            type="premium",
            username=required("FRAGMENT_SECOND_TARGET"),
            months=3,
        ),
    ]


async def prepare() -> None:
    """Inspect result.transaction: the combined payload for one external signature."""
    async with make_client(mode="prepare") as client:
        show_result(await client.batch_purchase(items(), payment_method="ton"))


async def purchase() -> None:
    """Send one wallet message and display each invoice's fulfillment status."""
    async with make_client(mode="pay") as client:
        show_result(await client.batch_purchase(items(), payment_method="ton"))


async def highload() -> None:
    """Use HighloadV3R1 for a larger single broadcast; fulfillment is per invoice."""
    async with make_client(
        mode="pay",
        wallet_version="HighloadV3R1",
    ) as client:
        show_result(await client.purchase(items(), payment_method="ton"))


if __name__ == "__main__":
    run({"prepare": prepare, "purchase": purchase, "highload": highload}, "prepare")
