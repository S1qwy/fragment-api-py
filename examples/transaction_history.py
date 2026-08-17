"""
Transaction history retrieval examples.

Demonstrates fetching Stars, Premium, and Ads top-up
transaction history from Fragment.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}


async def stars_history():
    """Fetch Stars transaction history (newest first)."""
    client = FragmentClient(cookies=COOKIES)

    transactions = await client.get_stars_history(sort="desc")
    print(f"Stars transactions: {len(transactions)}")

    for tx in transactions[:10]:
        print(f"  @{tx.recipient} — {tx.stars} stars — {tx.price_gram} GRAM — {tx.date}")
        print(f"    Price TON (alias): {tx.price_ton}")


async def premium_history():
    """Fetch Premium gift transaction history (newest first)."""
    client = FragmentClient(cookies=COOKIES)

    transactions = await client.get_premium_history(sort="desc")
    print(f"Premium transactions: {len(transactions)}")

    for tx in transactions[:10]:
        print(f"  @{tx.recipient} — {tx.duration} — {tx.price_gram} GRAM — {tx.date}")


async def topup_history():
    """Fetch Ads GRAM top-up history (oldest first)."""
    client = FragmentClient(cookies=COOKIES)

    transactions = await client.get_topup_history(sort="asc")
    print(f"Top-up transactions: {len(transactions)}")

    for tx in transactions[:10]:
        print(f"  @{tx.recipient} — {tx.amount} GRAM — {tx.date}")


if __name__ == "__main__":
    asyncio.run(stars_history())