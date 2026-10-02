"""Asset details, public history, and raw history pagination."""

from _common import make_client, required, run, show_result


async def username() -> None:
    """Read a username and its auction or ownership details."""
    async with make_client() as client:
        show_result(await client.get_username_info(required("FRAGMENT_TARGET")))


async def number() -> None:
    """Read an anonymous-number listing."""
    async with make_client() as client:
        show_result(await client.get_number_info(required("FRAGMENT_NUMBER")))


async def gift() -> None:
    """Read a gift's attributes, images, issuance, and history."""
    async with make_client() as client:
        show_result(await client.get_gift_info(required("FRAGMENT_SLUG")))


async def history() -> None:
    """Load another bid-history page when a public item exposes a cursor."""
    async with make_client() as client:
        target = required("FRAGMENT_TARGET")
        info = await client.get_username_info(target)
        if info.bid_history_next_offset is None:
            print("No additional bid-history cursor.")
            return
        result = await client.get_orders_history(
            1,
            target,
            info.bid_history_next_offset,
        )
        print(f"Raw history response keys: {sorted(result)}")


if __name__ == "__main__":
    run(
        {"username": username, "number": number, "gift": gift, "history": history},
        "username",
    )