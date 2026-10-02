"""Inspect client configurations without making purchases."""

from _common import make_client, run


async def read_only() -> None:
    """Use cookies when provided, otherwise select restricted wallet authentication."""
    async with make_client() as client:
        print(client)
        print(f"Wallet authentication: {client.wallet_auth}")
        print(f"Automatic payment credentials: {client.has_wallet}")


async def payer() -> None:
    """Configure a payer without broadcasting a transaction."""
    async with make_client(mode="wallet") as client:
        print(client)


async def highload() -> None:
    """Use the supported HighloadV3R1 wallet version name."""
    async with make_client(
        mode="wallet",
        wallet_version="HighloadV3R1",
    ) as client:
        print(client)


async def external() -> None:
    """Configure external preparation without enabling automatic broadcasting."""
    async with make_client(mode="prepare") as client:
        print(client)
        print(f"Automatic payment enabled: {client.has_wallet}")


if __name__ == "__main__":
    run(
        {
            "read": read_only,
            "payer": payer,
            "highload": highload,
            "external": external,
        },
        "read",
    )