'''
Example: Batch purchase Stars, Premium, and Ads top-ups
in bundled TON transactions with inline messages.

Demonstrates how to use client.batch_purchase() to send
multiple purchases as grouped on-chain transactions.

V5R1 wallets can pack up to 255 messages per transaction.
V4R2 wallets can pack up to 4 messages per transaction.
Items exceeding the limit are automatically split into
multiple chunks, each broadcast as a separate transaction.
'''

import asyncio
from FragmentAPI import (
    FragmentClient,
    ConfigError,
    WalletError,
    FragmentBaseError,
)


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
    Run a batch purchase containing mixed item types.

    Each item dict specifies:
      - type: "stars", "premium", or "ton"
      - username: Telegram username of the recipient
      - amount: star count (stars), TON amount (ton)
      - months: subscription duration (premium only, 3/6/12)
      - show_sender: whether to reveal sender (optional)

    The library resolves each recipient, obtains transaction
    payloads from Fragment, groups messages into chunks that
    fit the wallet version limit, checks total balance upfront,
    and broadcasts each chunk as a single on-chain transaction.

    After confirmation, req_ids are sent to Fragment for
    purchase finalization.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        wallet = await client.get_wallet()
        print(f"Wallet: {wallet.address}")
        print(f"Balance: {wallet.balance_ton} TON\n")

        items = [
            {
                "type": "stars",
                "username": "@alice",
                "amount": 500,
                "show_sender": True,
            },
            {
                "type": "stars",
                "username": "@bob",
                "amount": 1000,
            },
            {
                "type": "premium",
                "username": "@charlie",
                "months": 3,
                "show_sender": False,
            },
            {
                "type": "ton",
                "username": "@dave",
                "amount": 10,
            },
            {
                "type": "stars",
                "username": "@eve",
                "amount": 250,
            },
        ]

        try:
            result = await client.batch_purchase(
                items=items,
                payment_method="ton",
            )
        except ConfigError as exc:
            print(f"Configuration error: {exc}")
            return
        except WalletError as exc:
            print(f"Wallet error (insufficient balance): {exc}")
            return
        except FragmentBaseError as exc:
            print(f"Fragment error: {exc}")
            return

        print(f"Batch complete: {result}")
        print(f"  Total: {result.total}")
        print(f"  Succeeded: {result.succeeded}")
        print(f"  Failed: {result.failed}")
        print(f"  Chunks sent: {result.chunks_sent}\n")

        idx = 0
        while idx < len(result.items):
            item = result.items[idx]
            if item.ok:
                print(
                    f"  OK  [{item.type}] "
                    f"@{item.username} "
                    f"amount={item.amount} "
                    f"chunk={item.chunk_index} "
                    f"tx={item.result['transaction_id'][:16]}..."
                )
            else:
                print(
                    f"  FAIL [{item.type}] "
                    f"@{item.username} "
                    f"amount={item.amount} "
                    f"chunk={item.chunk_index} "
                    f"error={item.error}"
                )
            idx += 1


if __name__ == "__main__":
    asyncio.run(main())