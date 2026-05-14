'''
Example 06: Top up Telegram Ads balance with TON.

Demonstrates funding a Telegram Ads account via Fragment
and viewing topup transaction history.
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
    Top up a Telegram Ads account and view topup history.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # --- Top up Ads balance ---
        result = await client.topup_ton(
            username="@my_ads_account",
            amount=100,
            show_sender=True,
        )
        print("=== Ads Top-up Result ===")
        print(f"  Transaction ID: {result.transaction_id}")
        print(f"  Recipient:      {result.username}")
        print(f"  Amount:         {result.amount} TON")

        # --- View topup history ---
        history = await client.get_topup_history(
            sort="desc",
        )
        print(f"\n=== Topup History ({len(history)} entries) ===")
        for tx in history:
            print(
                f"  @{tx.recipient}: {tx.amount} TON — {tx.date}"
            )


if __name__ == "__main__":
    asyncio.run(main())