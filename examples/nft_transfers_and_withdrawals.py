"""Explicit NFT transfer and separate withdrawal approval steps."""

from _common import (
    make_client,
    require_execution,
    required,
    run,
    show_result,
)


async def recipient() -> None:
    """Resolve an NFT recipient without transferring an asset."""
    async with make_client(account=True) as client:
        show_result(await client.search_nft_transfer_recipient(
            required("FRAGMENT_TARGET")
        ))


async def transfer() -> None:
    """Initialize and broadcast a transfer to the explicitly selected recipient."""
    async with make_client(mode="pay", account=True) as client:
        found = await client.search_nft_transfer_recipient(required("FRAGMENT_TARGET"))
        if found is None:
            print("Recipient not found.")
            return
        request = await client.init_nft_transfer(
            required("FRAGMENT_SLUG"),
            found.recipient,
        )
        show_result(await client.transfer_nft(request.req_id))


async def nft_init() -> None:
    """Initialize an NFT withdrawal without automatically accepting its challenge."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        show_result(await client.init_nft_withdrawal(
            required("FRAGMENT_TRANSACTION"),
            keep_gift=False,
        ))


async def nft_confirm() -> None:
    """Submit a separately reviewed NFT withdrawal challenge."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        show_result(await client.confirm_nft_withdrawal(
            required("FRAGMENT_TRANSACTION"),
            required("FRAGMENT_CONFIRM_HASH"),
            keep_gift=False,
        ))


async def stars_init() -> None:
    """Read current Stars withdrawal state and request an approval challenge."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        state = await client.get_stars_withdrawal_state(required("FRAGMENT_TRANSACTION"))
        show_result(await client.init_stars_withdrawal(
            state.transaction,
            state.withdrawal_data,
        ))


async def stars_confirm() -> None:
    """Confirm a reviewed Stars withdrawal using its original opaque state."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        show_result(await client.confirm_stars_withdrawal(
            required("FRAGMENT_TRANSACTION"),
            required("FRAGMENT_WITHDRAWAL_DATA"),
            required("FRAGMENT_CONFIRM_HASH"),
        ))


async def ads_init() -> None:
    """Request an Ads withdrawal approval challenge."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        show_result(await client.init_ads_withdrawal(required("FRAGMENT_TRANSACTION")))


async def ads_confirm() -> None:
    """Confirm a separately reviewed Ads withdrawal."""
    require_execution()
    async with make_client(mode="prepare", account=True) as client:
        show_result(await client.confirm_ads_withdrawal(
            required("FRAGMENT_TRANSACTION"),
            required("FRAGMENT_CONFIRM_HASH"),
        ))


if __name__ == "__main__":
    run(
        {
            "recipient": recipient,
            "transfer": transfer,
            "nft-init": nft_init,
            "nft-confirm": nft_confirm,
            "stars-init": stars_init,
            "stars-confirm": stars_confirm,
            "ads-init": ads_init,
            "ads-confirm": ads_confirm,
        },
        "recipient",
    )