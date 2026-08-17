"""
Price checking examples.

Demonstrates fetching current prices for Stars packages,
custom Stars quantities, and Premium subscription options.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = "stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok"


async def get_all_stars_prices():
    """Fetch all predefined Stars package prices."""
    client = FragmentClient(cookies=COOKIES)

    prices = await client.get_stars_prices()
    print(f"GRAM rate: {prices.gram_rate}")
    print(f"TON rate (alias): {prices.ton_rate}")
    print(f"\nAvailable packages ({len(prices.packages)}):")

    for pkg in prices.packages:
        print(f"  {pkg.stars:>10,} stars — {pkg.gram_price:>10} GRAM — ${pkg.usd_price}")
        print(f"    TON price (alias): {pkg.ton_price}")


async def get_custom_stars_price():
    """Get price for a specific custom Stars quantity."""
    client = FragmentClient(cookies=COOKIES)

    for quantity in [100, 500, 1000, 5000, 10000]:
        price = await client.get_stars_price(quantity)
        print(f"  {price.stars:>6,} stars — {price.gram_price} GRAM — ${price.usd_price}")


async def get_premium_prices():
    """Fetch all Premium subscription price options."""
    client = FragmentClient(cookies=COOKIES)

    prices = await client.get_premium_prices()
    print(f"GRAM rate: {prices.gram_rate}")
    print(f"\nPremium options ({len(prices.options)}):")

    for opt in prices.options:
        discount_str = f" ({opt.discount})" if opt.discount else ""
        print(f"  {opt.label}{discount_str}")
        print(f"    {opt.months} months — {opt.gram_price} GRAM — ${opt.usd_price}")
        print(f"    TON price (alias): {opt.ton_price}")


if __name__ == "__main__":
    asyncio.run(get_all_stars_prices())