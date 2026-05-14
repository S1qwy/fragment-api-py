'''
Example 17: Withdraw Stars revenue to your TON wallet.

To start a Stars withdrawal, you first need to obtain the
transaction ID from Telegram using the Telethon library.
This example shows the complete flow: obtaining the withdrawal
URL from a bot, then performing the withdrawal via Fragment.
'''

import asyncio
from urllib.parse import parse_qs, urlparse

from telethon import TelegramClient, functions
from telethon.password import compute_check

from FragmentAPI import FragmentClient


# --- Telegram settings ---
API_ID = 12345678
API_HASH = "your_api_hash"
PASSWORD_2FA = "your_2fa_password"
BOT_USERNAME = "@your_bot"
WITHDRAW_AMOUNT = 1000

# --- Fragment settings ---
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


async def get_stars_withdrawal_url(
    bot_username: str,
    amount: int,
) -> str:
    '''
    Obtain the Stars withdrawal URL from Telegram.

    Uses Telethon to call GetStarsRevenueWithdrawalUrlRequest,
    which requires 2FA password confirmation.

    Args:
        bot_username: Username of your bot (e.g. "@mybot").
        amount: Number of stars to withdraw.

    Returns:
        The transaction ID extracted from the withdrawal URL.
    '''

    async with TelegramClient(
        "session",
        API_ID,
        API_HASH,
    ) as tg_client:

        # Resolve bot entity
        peer = await tg_client.get_input_entity(
            bot_username,
        )

        # Get 2FA password parameters
        pwd_info = await tg_client(
            functions.account.GetPasswordRequest()
        )

        # Compute SRP hash
        input_check_password = compute_check(
            pwd_info,
            PASSWORD_2FA,
        )

        # Request withdrawal URL from Telegram
        result = await tg_client(
            functions.payments.GetStarsRevenueWithdrawalUrlRequest(
                peer=peer,
                password=input_check_password,
                amount=amount,
                ton=False,
            )
        )

        # Extract transaction ID from URL
        # URL format: https://fragment.com/stars/withdraw?transaction=...
        parsed = urlparse(result.url)
        params = parse_qs(parsed.query)
        transaction_id = params["transaction"][0]

        print(f"Withdrawal URL: {result.url}")
        print(f"Transaction ID: {transaction_id}")

        return transaction_id


async def main():
    '''
    Complete Stars withdrawal flow:
    1. Get transaction ID from Telegram
    2. Get withdrawal state from Fragment
    3. Initialize withdrawal
    4. Confirm withdrawal
    '''

    # Step 1: Get transaction ID from Telegram
    transaction_id = await get_stars_withdrawal_url(
        bot_username=BOT_USERNAME,
        amount=WITHDRAW_AMOUNT,
    )

    async with FragmentClient(
        seed=SEED,
        cookies=COOKIES,
        wallet_version="V5R1",
    ) as client:

        # Step 2: Get withdrawal state (includes withdrawal_data)
        state = await client.get_stars_withdrawal_state(
            transaction=transaction_id,
        )
        print(f"\n=== Stars Withdrawal State ===")
        print(f"  Transaction:     {state.transaction}")
        print(f"  Withdrawal Data: {state.withdrawal_data[:40]}...")

        # Step 3: Initialize withdrawal
        init_result = await client.init_stars_withdrawal(
            transaction=state.transaction,
            withdrawal_data=state.withdrawal_data,
        )
        print(f"\n=== Init Stars Withdrawal ===")
        print(f"  OK:              {init_result.ok}")
        print(f"  Confirm Message: {init_result.confirm_message}")
        print(f"  Confirm Hash:    {init_result.confirm_hash}")

        if not init_result.ok or not init_result.confirm_hash:
            print(f"  Error: {init_result.error}")
            return

        # Step 4: Confirm withdrawal
        confirm_result = await client.confirm_stars_withdrawal(
            transaction=state.transaction,
            withdrawal_data=state.withdrawal_data,
            confirm_hash=init_result.confirm_hash,
        )
        print(f"\n=== Confirm Stars Withdrawal ===")
        print(f"  OK:          {confirm_result.ok}")
        print(f"  Mode:        {confirm_result.mode}")
        print(f"  Need Update: {confirm_result.need_update}")
        if confirm_result.error:
            print(f"  Error:       {confirm_result.error}")


if __name__ == "__main__":
    asyncio.run(main())