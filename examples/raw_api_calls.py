"""Raw API access with method restrictions and explicit BOC reporting."""

from _common import (
    make_client,
    require_execution,
    required,
    run,
    setting,
)


async def search() -> None:
    """Read raw search response keys without assuming a single HTML field."""
    async with make_client() as client:
        result = await client.call(
            "searchAuctions",
            {"type": "usernames", "query": "", "sort": "price_asc"},
        )
        print(f"Response keys: {sorted(result)}")
        if result.get("error"):
            print(f"Fragment error: {result['error']}")


async def prices() -> None:
    """Request raw Stars pricing from the correct purchase page."""
    async with make_client() as client:
        result = await client.call(
            "updateStarsPrices",
            {"stars": "0", "quantity": 1000},
            page_url="https://fragment.com/stars/buy",
        )
        print(f"Response keys: {sorted(result)}")


async def confirm() -> None:
    """Report an already broadcast BOC using the invoice's original session."""
    require_execution()
    async with make_client(account=True) as client:
        result = await client.confirm_request(
            required("FRAGMENT_REQ_ID"),
            required("TON_SIGNED_BOC"),
            referer=setting("FRAGMENT_CONFIRM_REFERER", "stars/buy"),
        )
        print(f"Confirmation response keys: {sorted(result)}")
        print("This response alone is not a fulfillment receipt.")


if __name__ == "__main__":
    run({"search": search, "prices": prices, "confirm": confirm}, "search")