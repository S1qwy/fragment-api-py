"""Account asset management with explicit guards on bids and mutations."""

from _common import (
    make_client,
    require_execution,
    required,
    run,
    setting,
    show_result,
)


def item_type() -> int:
    """Read the numeric asset category."""
    return int(setting("FRAGMENT_ITEM_TYPE", "1"))


async def assets() -> None:
    """List user-owned assets without initiating a transaction."""
    async with make_client(account=True) as client:
        show_result(await client.get_my_assets(setting("FRAGMENT_CATEGORY", "usernames")))


async def bids() -> None:
    """Read account bid history."""
    async with make_client(account=True) as client:
        show_result(await client.get_my_bids(setting("FRAGMENT_CATEGORY", "usernames")))


async def bid() -> None:
    """Place the explicitly configured integer TON bid."""
    async with make_client(mode="pay", account=True) as client:
        show_result(await client.place_bid(
            item_type(),
            required("FRAGMENT_SLUG"),
            int(required("FRAGMENT_TON_AMOUNT")),
        ))


async def offer() -> None:
    """Make an explicitly configured native TON offer."""
    async with make_client(mode="pay", account=True) as client:
        show_result(await client.make_offer(
            item_type(),
            required("FRAGMENT_SLUG"),
            int(required("FRAGMENT_TON_AMOUNT")),
        ))


async def auction() -> None:
    """Start an auction with the supplied minimum price."""
    async with make_client(mode="pay", account=True) as client:
        show_result(await client.start_auction(
            item_type(),
            required("FRAGMENT_SLUG"),
            int(required("FRAGMENT_TON_AMOUNT")),
        ))


async def sell() -> None:
    """Create a fixed-price listing."""
    async with make_client(mode="pay", account=True) as client:
        show_result(await client.sell_asset(
            item_type(),
            required("FRAGMENT_SLUG"),
            int(required("FRAGMENT_TON_AMOUNT")),
        ))


async def cancel() -> None:
    """Request cancellation of an owned auction."""
    async with make_client(mode="pay", account=True) as client:
        show_result(await client.cancel_auction(
            item_type(),
            required("FRAGMENT_SLUG"),
        ))


async def destinations() -> None:
    """Inspect available Telegram assignment destinations."""
    async with make_client(account=True) as client:
        show_result(await client.get_assign_accounts(
            item_type(),
            required("FRAGMENT_SLUG"),
        ))


async def assign() -> None:
    """Request assignment without automatically paying a bot assignment charge."""
    require_execution()
    async with make_client(account=True) as client:
        show_result(await client.assign_to_telegram(
            item_type(),
            required("FRAGMENT_SLUG"),
            assign_to=required("FRAGMENT_ASSIGN_TO"),
            wait_for_bot_payment=False,
        ))


async def subscribe() -> None:
    """Enable notifications for the chosen asset."""
    require_execution()
    async with make_client(account=True) as client:
        show_result(await client.subscribe_to_item(
            item_type(),
            required("FRAGMENT_SLUG"),
        ))


async def unsubscribe() -> None:
    """Disable notifications for the chosen asset."""
    require_execution()
    async with make_client(account=True) as client:
        show_result(await client.unsubscribe_from_item(
            item_type(),
            required("FRAGMENT_SLUG"),
        ))


if __name__ == "__main__":
    run(
        {
            "assets": assets,
            "bids": bids,
            "bid": bid,
            "offer": offer,
            "auction": auction,
            "sell": sell,
            "cancel": cancel,
            "destinations": destinations,
            "assign": assign,
            "subscribe": subscribe,
            "unsubscribe": unsubscribe,
        },
        "assets",
    )