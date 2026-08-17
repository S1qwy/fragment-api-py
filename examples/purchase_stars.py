"""
Stars purchase examples.

Demonstrates buying Telegram Stars for users including
recipient resolution, single purchases, and different payment methods.
"""

import asyncio
from FragmentAPI import FragmentClient, EvmPaymentResult, PurchaseResult


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
    "stel_ton_token": "your_ton_token",
}
SEED = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24"
API_KEY = "your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx"


async def check_recipient_first():
    """Verify that a user exists on Fragment before purchasing Stars."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    recipient = await client.get_stars_recipient("durov")
    if recipient:
        print(f"Found: {recipient.name} (recipient ID: {recipient.recipient[:20]}...)")
        print(f"Photo: {recipient.photo_url}")
        print(f"Is myself: {recipient.myself}")
    else:
        print("User not found on Fragment")


async def purchase_stars_gram():
    """Buy Stars for a user using GRAM payment method."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase_stars(
        username="durov",
        amount=100,
        show_sender=True,
        payment_method="gram",
    )

    if isinstance(result, PurchaseResult):
        print(f"Stars sent successfully!")
        print(f"  Transaction: {result.transaction_id}")
        print(f"  Type: {result.type}")
        print(f"  To: {result.username}")
        print(f"  Amount: {result.amount} stars")
        print(f"  Payment: {result.payment_method}")


async def purchase_stars_ton_alias():
    """Buy Stars using 'ton' payment method (alias for 'gram')."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase_stars(
        username="durov",
        amount=50,
        payment_method="ton",
    )
    print(f"Result: {result}")


async def purchase_stars_hide_sender():
    """Buy Stars anonymously without revealing sender name."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase_stars(
        username="durov",
        amount=100,
        show_sender=False,
    )
    print(f"Anonymous Stars purchase: {result}")


async def purchase_stars_via_unified_api():
    """Buy Stars using the unified purchase() method."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase(
        "stars",
        username="durov",
        amount=100,
        payment_method="gram",
    )
    print(f"Unified purchase result: {result}")


async def purchase_stars_dict_format():
    """Buy Stars using dict format with unified purchase() method."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    result = await client.purchase({
        "type": "stars",
        "username": "durov",
        "amount": 100,
        "show_sender": True,
    })
    print(f"Dict format result: {result}")


async def purchase_stars_evm():
    """Buy Stars using EVM payment method (returns invoice, not transaction).

    When using EVM payment methods, Fragment returns an invoice
    that must be paid on-chain via the specified EVM network.
    """
    client = FragmentClient(
        cookies={
            "stel_ssid": "your_ssid",
            "stel_dt": "-180",
            "stel_token": "your_token",
        },
    )

    result = await client.purchase_stars(
        username="durov",
        amount=100,
        payment_method="usdt_eth",
    )

    if isinstance(result, EvmPaymentResult):
        invoice = result.invoice
        print(f"EVM Invoice generated:")
        print(f"  Chain:    {invoice.invoice_chain_name}")
        print(f"  Token:    {invoice.token_symbol}")
        print(f"  Address:  {invoice.invoice_address}")
        print(f"  Amount:   {invoice.invoice_amount} {invoice.token_symbol}")
        print(f"  Hex:      {invoice.invoice_amount_hex}")
        print(f"  Expires:  {invoice.expires_at}")


if __name__ == "__main__":
    asyncio.run(purchase_stars_gram())