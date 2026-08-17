"""
Batch purchase examples.

Demonstrates executing multiple purchases in a single on-chain
transaction for maximum efficiency. Transactions are automatically
chunked based on wallet version limits.
"""

import asyncio
from FragmentAPI import FragmentClient, PurchaseItem, BatchResult


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}
SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx"


async def batch_stars_and_premium():
    """Purchase Stars and Premium for multiple users in one transaction."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.batch_purchase(
        items=[
            {"type": "stars", "username": "user1", "amount": 100},
            {"type": "stars", "username": "user2", "amount": 200},
            {"type": "premium", "username": "user3", "months": 3},
            {"type": "stars", "username": "user4", "amount": 500, "show_sender": False},
        ],
        payment_method="gram",
    )

    print(f"Batch result: {result.total} total, {result.succeeded} succeeded, {result.failed} failed")
    print(f"Chunks sent: {result.chunks_sent}")

    for item in result.items:
        status = "OK" if item.ok else f"FAILED: {item.error}"
        print(f"  [{item.chunk_index}] {item.type} -> {item.username}: {item.amount} — {status}")


async def batch_with_purchase_items():
    """Batch purchase using PurchaseItem dataclass for type safety."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    items = [
        PurchaseItem(type="stars", username="user1", amount=100),
        PurchaseItem(type="premium", username="user2", months=6),
        PurchaseItem(type="stars", username="user3", amount=1000, show_sender=False),
    ]

    result = await client.batch_purchase(items, payment_method="gram")
    print(f"Typed batch: {result}")


async def batch_via_unified_purchase():
    """Execute batch purchase through the unified purchase() method."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase(
        [
            {"type": "stars", "username": "user1", "amount": 50},
            {"type": "stars", "username": "user2", "amount": 75},
        ],
        payment_method="gram",
    )

    if isinstance(result, BatchResult):
        print(f"Batch via unified: {result.succeeded}/{result.total} succeeded")


async def batch_with_ads_topup():
    """Include Ads GRAM top-ups in a batch with Stars purchases."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.batch_purchase(
        items=[
            {"type": "stars", "username": "user1", "amount": 100},
            {"type": "gram", "username": "my_channel", "amount": 5},
            {"type": "premium", "username": "user2", "months": 3},
        ],
        payment_method="gram",
    )
    print(f"Mixed batch: {result}")


async def batch_large_with_highload():
    """Execute a large batch with HighloadWalletV3 (up to 254 messages)."""
    client = FragmentClient(
        cookies=COOKIES,
        seed=SEED,
        api_key=API_KEY,
        wallet_version="HIGHLOAD_V3",
    )

    items = [
        {"type": "stars", "username": f"user{i}", "amount": 50}
        for i in range(10)
    ]

    result = await client.batch_purchase(items, payment_method="gram")
    print(f"Highload batch: {result.succeeded}/{result.total}, chunks: {result.chunks_sent}")


async def batch_handle_partial_failures():
    """Handle partial failures in batch operations gracefully."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.batch_purchase([
        {"type": "stars", "username": "real_user", "amount": 100},
        {"type": "stars", "username": "nonexistent_user_12345", "amount": 100},
        {"type": "stars", "username": "another_real_user", "amount": 100},
    ])

    print(f"Total: {result.total}, Succeeded: {result.succeeded}, Failed: {result.failed}")

    for item in result.items:
        if item.ok:
            print(f"  SUCCESS: {item.username} — {item.amount} stars")
        else:
            print(f"  FAILED:  {item.username} — {item.error}")


if __name__ == "__main__":
    asyncio.run(batch_stars_and_premium())