'''
Example 04: Purchase Telegram Stars for a user.

Demonstrates buying Stars with TON or USDT payment methods,
including checking prices before purchase.
'''

import asyncio
from FragmentAPI import FragmentClient


SEED = (
    "word1 word2 word3 word4 word5 word6 "
    "word7 word8 word9 word10 word11 word12 "
    "word13 word14 word15 word16 word17 word18 "
    "word19 word20 word21 word22 word23 word24"
)

COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}


async def main():
    '''
    Check Stars prices, then purchase Stars for a Telegram user.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Check all package prices ---
        prices = await client.get_stars_prices()
        print(f"=== Stars Packages (TON rate: {prices.ton_rate}) ===")
        for pkg in prices.packages:
            print(
                f"  {pkg.stars:>8} stars — "
                f"{pkg.ton_price} TON (${pkg.usd_price})"
            )

        # --- Check custom quantity price ---
        custom_price = await client.get_stars_price(
            quantity=777,
        )
        print(
            f"\n  Custom 777 stars: "
            f"{custom_price.ton_price} TON (${custom_price.usd_price})"
        )

        # --- Purchase Stars with TON ---
        result = await client.purchase_stars(
            username="@durov",
            amount=500,
            show_sender=True,
            payment_method="ton",
        )
        print(f"\n=== Purchase Result ===")
        print(f"  Transaction ID: {result.transaction_id}")
        print(f"  Recipient:      {result.username}")
        print(f"  Amount:         {result.amount} stars")
        print(f"  Payment:        {result.payment_method}")

        # --- Purchase Stars with USDT ---
        result_usdt = await client.purchase_stars(
            username="@username",
            amount=1000,
            show_sender=False,
            payment_method="usdt_ton",
        )
        print(f"\n=== USDT Purchase Result ===")
        print(f"  Transaction ID: {result_usdt.transaction_id}")
        print(f"  Amount:         {result_usdt.amount} stars")


if __name__ == "__main__":
    asyncio.run(main())