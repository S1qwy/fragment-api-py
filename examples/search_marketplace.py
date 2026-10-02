"""Marketplace browsing, bounded pagination, and gift attribute filters."""

from _common import make_client, required, run, setting, show_result


async def usernames() -> None:
    """Search username listings."""
    async with make_client() as client:
        show_result(await client.search_usernames(
            query=setting("FRAGMENT_QUERY", ""),
            sort="price_asc",
            filter="sale",
        ))


async def numbers() -> None:
    """Search anonymous-number listings."""
    async with make_client() as client:
        show_result(await client.search_numbers(
            query=setting("FRAGMENT_QUERY", "888"),
            sort="price_asc",
        ))


async def gifts() -> None:
    """Read up to three gift pages and stop on missing or repeated cursors."""
    async with make_client() as client:
        cursor = None
        seen: set[int] = set()
        for _ in range(3):
            result = await client.search_gifts(
                sort="price_asc",
                filter="sale",
                offset=cursor,
            )
            show_result(result)
            next_cursor = result.next_offset
            if next_cursor is None or next_cursor in seen:
                break
            seen.add(next_cursor)
            cursor = next_cursor


async def filters() -> None:
    """Inspect exact collection-specific trait names and values."""
    async with make_client() as client:
        show_result(await client.get_gift_filters(
            collection=required("FRAGMENT_COLLECTION"),
        ))


async def filtered() -> None:
    """Apply an exact trait value returned by get_gift_filters."""
    async with make_client() as client:
        show_result(await client.search_gifts(
            collection=required("FRAGMENT_COLLECTION"),
            attr={
                setting("FRAGMENT_ATTRIBUTE", "Model"): [
                    required("FRAGMENT_ATTRIBUTE_VALUE")
                ],
            },
            sort="price_asc",
        ))


if __name__ == "__main__":
    run(
        {
            "usernames": usernames,
            "numbers": numbers,
            "gifts": gifts,
            "filters": filters,
            "filtered": filtered,
        },
        "usernames",
    )