"""
NFT transfer and withdrawal examples.

Demonstrates transferring gifts to other users and
withdrawing NFTs/Stars to external wallets.
"""

import asyncio
from FragmentAPI import FragmentClient


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}
SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx"


async def transfer_nft_to_user():
    """Transfer an NFT gift to another Telegram user."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    recipient = await client.search_nft_transfer_recipient("target_user")
    if not recipient:
        print("Transfer recipient not found")
        return

    print(f"Recipient: {recipient.name} (myself={recipient.myself})")

    transfer_req = await client.init_nft_transfer(
        slug="my-gift-42",
        recipient=recipient.recipient,
    )
    print(f"Transfer request created:")
    print(f"  Req ID:  {transfer_req.req_id}")
    print(f"  Title:   {transfer_req.item_title}")
    print(f"  Content: {transfer_req.content}")
    print(f"  Button:  {transfer_req.button}")

    tx_result = await client.transfer_nft(
        req_id=transfer_req.req_id,
        show_sender=True,
    )
    print(f"Transfer completed: tx={tx_result.tx_hash}, confirmed={tx_result.confirmed}")


async def withdraw_nft_to_wallet():
    """Withdraw an NFT to an external wallet (two-step confirmation)."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    transaction_id = "some_transaction_id_from_fragment"

    state = await client.get_nft_withdrawal_state(transaction_id)
    print(f"Withdrawal state: {state}")

    init_result = await client.init_nft_withdrawal(
        transaction=transaction_id,
        keep_gift=False,
    )

    if not init_result.ok:
        print(f"Init failed: {init_result.error}")
        return

    print(f"Confirm message: {init_result.confirm_message}")
    print(f"Confirm button:  {init_result.confirm_button}")

    confirm_result = await client.confirm_nft_withdrawal(
        transaction=transaction_id,
        confirm_hash=init_result.confirm_hash,
        keep_gift=False,
    )
    print(f"Withdrawal confirmed: ok={confirm_result.ok}, mode={confirm_result.mode}")


async def withdraw_stars_to_wallet():
    """Withdraw Stars revenue to an external wallet (two-step confirmation)."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    transaction_id = "some_stars_transaction_id"

    state = await client.get_stars_withdrawal_state(transaction_id)
    print(f"Stars withdrawal state:")
    print(f"  Transaction: {state.transaction}")
    print(f"  Data: {state.withdrawal_data}")

    init_result = await client.init_stars_withdrawal(
        transaction=state.transaction,
        withdrawal_data=state.withdrawal_data,
    )

    if not init_result.ok:
        print(f"Init failed: {init_result.error}")
        return

    print(f"Confirm message: {init_result.confirm_message}")

    confirm_result = await client.confirm_stars_withdrawal(
        transaction=state.transaction,
        withdrawal_data=state.withdrawal_data,
        confirm_hash=init_result.confirm_hash,
    )
    print(f"Stars withdrawal: ok={confirm_result.ok}, mode={confirm_result.mode}")


if __name__ == "__main__":
    asyncio.run(transfer_nft_to_user())