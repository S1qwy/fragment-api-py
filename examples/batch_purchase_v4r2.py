'''
Example: Batch purchase with V4R2 wallet (4 messages per chunk).

Demonstrates automatic chunking when the wallet version limits
the number of inline messages per transaction. With V4R2 each
chunk holds at most 4 messages, so 7 items produce 2 on-chain
transactions (4 + 3).
'''

import asyncio
from FragmentAPI import (
    FragmentClient,
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
    Send 7 Stars purchases via a V4R2 wallet.

    V4R2 supports at most 4 outgoing messages per transaction,
    so the library will split the 7 items into 2 chunks:
      - Chunk 0: items 0-3 (4 messages, 1 on-chain tx)
      - Chunk 1: items 4-6 (3 messages, 1 on-chain tx)

    Each chunk is confirmed independently by seqno+balance.
    '''

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V4R2",
    ) as client:

        items = [
            {"type": "stars", "username": "@user1", "amount": 100},
            {"type": "stars", "username": "@user2", "amount": 200},
            {"type": "stars", "username": "@user3", "amount": 300},
            {"type": "premium", "username": "@user4", "months": 3},
            {"type": "ton", "username": "@user5", "amount": 5},
            {"type": "stars", "username": "@user6", "amount": 500},
            {"type": "stars", "username": "@user7", "amount": 150},
        ]

        try:
            result = await client.batch_purchase(items=items)
        except WalletError as exc:
            print(f"Insufficient balance for batch: {exc}")
            return
        except FragmentBaseError as exc:
            print(f"Error: {exc}")
            return

        print(f"Result: {result}")
        print(f"Chunks broadcast: {result.chunks_sent}")

        idx = 0
        while idx < len(result.items):
            r = result.items[idx]
            status = "OK" if r.ok else "FAIL"
            print(
                f"  [{status}] chunk={r.chunk_index} "
                f"{r.type} @{r.username} amount={r.amount}"
            )
            idx += 1


if __name__ == "__main__":
    asyncio.run(main())