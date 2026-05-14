'''
Example 05: Gift Telegram Premium to a user.

Demonstrates purchasing Premium subscriptions for 3, 6, or 12 months
with TON or USDT payment, and checking prices beforehand.
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
    Check Premium prices and gift Premium to a Telegram user.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Check Premium prices ---
        prices = await client.get_premium_prices()
        print(f"=== Premium Prices (TON rate: {prices.ton_rate}) ===")
        for opt in prices.options:
            discount = f" ({opt.discount})" if opt.discount else ""
            print(
                f"  {opt.months:>2} months — {opt.label}: "
                f"{opt.ton_price} TON (${opt.usd_price}){discount}"
            )

        # --- Gift Premium for 3 months ---
        result = await client.purchase_premium(
            username="@durov",
            months=3,
            show_sender=True,
            payment_method="ton",
        )
        print(f"\n=== Premium Gift Result ===")
        print(f"  Transaction ID: {result.transaction_id}")
        print(f"  Recipient:      {result.username}")
        print(f"  Duration:       {result.amount} months")
        print(f"  Payment:        {result.payment_method}")

        # --- Gift Premium for 12 months with USDT ---
        result_yearly = await client.purchase_premium(
            username="@friend",
            months=12,
            show_sender=False,
            payment_method="usdt_ton",
        )
        print(f"\n=== Yearly Premium Result ===")
        print(f"  Transaction ID: {result_yearly.transaction_id}")
        print(f"  Duration:       {result_yearly.amount} months")


if __name__ == "__main__":
    asyncio.run(main())