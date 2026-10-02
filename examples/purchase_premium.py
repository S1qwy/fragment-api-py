"""Resolve Premium recipients and choose prepared, native, or EVM payment flows."""

from _common import make_client, required, run, show_result


async def recipient() -> None:
    """Check whether Fragment resolves the intended Premium recipient."""
    async with make_client() as client:
        show_result(await client.get_premium_recipient(
            required("FRAGMENT_TARGET"),
            months=3,
        ))


async def prepare() -> None:
    """Prepare a three-month Premium gift without broadcasting."""
    async with make_client(mode="prepare") as client:
        show_result(await client.purchase_premium(required("FRAGMENT_TARGET"), 3))


async def purchase() -> None:
    """Broadcast a Premium gift and distinguish broadcast from fulfillment."""
    async with make_client(mode="pay") as client:
        show_result(await client.purchase_premium(required("FRAGMENT_TARGET"), 3))


async def evm() -> None:
    """Request an external USDC invoice on Base."""
    async with make_client() as client:
        show_result(await client.purchase_premium(
            required("FRAGMENT_TARGET"),
            3,
            payment_method="usdc_base",
        ))


if __name__ == "__main__":
    run(
        {"recipient": recipient, "prepare": prepare, "purchase": purchase, "evm": evm},
        "recipient",
    )