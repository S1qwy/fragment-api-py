"""Gateway credit quotes and account-specific Ads or Gateway recharges."""

from _common import make_client, required, run, show_result


async def quote() -> None:
    """Quote Gateway credits without sending a payment."""
    async with make_client() as client:
        show_result(await client.get_gateway_price(
            required("FRAGMENT_ACCOUNT_ID"),
            100,
        ))


async def prepare_gateway() -> None:
    """Prepare a Gateway invoice for external signing."""
    async with make_client(mode="prepare") as client:
        show_result(await client.recharge_gateway(
            required("FRAGMENT_ACCOUNT_ID"),
            100,
        ))


async def gateway() -> None:
    """Pay a Gateway recharge invoice."""
    async with make_client(mode="pay") as client:
        show_result(await client.recharge_gateway(
            required("FRAGMENT_ACCOUNT_ID"),
            100,
        ))


async def ads() -> None:
    """Pay an Ads recharge invoice for the exact supplied account identifier."""
    async with make_client(mode="pay") as client:
        show_result(await client.recharge_ads(
            required("FRAGMENT_ACCOUNT_ID"),
            1,
        ))


if __name__ == "__main__":
    run(
        {
            "quote": quote,
            "prepare-gateway": prepare_gateway,
            "gateway": gateway,
            "ads": ads,
        },
        "quote",
    )