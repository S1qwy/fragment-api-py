"""
EVM payment automation examples (EXPERIMENTAL).

WARNING: These examples use web3.py for on-chain EVM transactions.
This functionality has NOT been tested in production. Use at your own risk.
Always verify contract addresses and amounts before executing transactions.

Requirements:
    pip install web3

Demonstrates how to take an EvmInvoice from Fragment and
execute the corresponding EVM transaction to complete payment.
"""

import asyncio
from FragmentAPI import FragmentClient, EvmPaymentResult


COOKIES = {
    "stel_ssid": "your_ssid",
    "stel_dt": "-180",
    "stel_token": "your_token",
}


async def purchase_stars_usdt_eth():
    """Purchase Stars with USDT on Ethereum and pay the EVM invoice.

    WARNING: EXPERIMENTAL — NOT TESTED IN PRODUCTION.
    This example shows the general flow for paying an EVM invoice.
    Always verify amounts and addresses before signing transactions.
    """
    client = FragmentClient(cookies=COOKIES)

    result = await client.purchase_stars(
        username="target_user",
        amount=100,
        payment_method="usdt_eth",
    )

    if not isinstance(result, EvmPaymentResult):
        print("Expected EVM payment result")
        return

    invoice = result.invoice
    print(f"EVM Invoice received:")
    print(f"  Chain:   {invoice.invoice_chain_name} (ID: {invoice.invoice_chain_id})")
    print(f"  Token:   {invoice.token_symbol} ({invoice.invoice_token})")
    print(f"  To:      {invoice.invoice_address}")
    print(f"  Amount:  {invoice.invoice_amount} {invoice.token_symbol}")
    print(f"  Raw:     {invoice.invoice_amount_raw}")
    print(f"  Hex:     {invoice.invoice_amount_hex}")
    print(f"  Expires: {invoice.expires_at}")

    try:
        from web3 import Web3

        ETH_RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"
        PRIVATE_KEY = "0xYOUR_PRIVATE_KEY"

        w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
        account = w3.eth.account.from_key(PRIVATE_KEY)

        ERC20_ABI = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"},
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function",
            }
        ]

        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(invoice.invoice_token),
            abi=ERC20_ABI,
        )

        tx = token_contract.functions.transfer(
            Web3.to_checksum_address(invoice.invoice_address),
            invoice.invoice_amount_raw,
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": invoice.invoice_chain_id,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"\nTransaction sent!")
        print(f"  Hash: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"  Status: {'Success' if receipt.status == 1 else 'Failed'}")
        print(f"  Block: {receipt.blockNumber}")

    except ImportError:
        print("\nweb3 not installed. Run: pip install web3")
    except Exception as e:
        print(f"\nEVM transaction failed: {e}")


async def purchase_usdc_base():
    """Purchase Stars with USDC on Base network.

    WARNING: EXPERIMENTAL — NOT TESTED IN PRODUCTION.
    Base network uses lower gas fees than Ethereum mainnet.
    """
    client = FragmentClient(cookies=COOKIES)

    result = await client.purchase_stars(
        username="target_user",
        amount=500,
        payment_method="usdc_base",
    )

    if isinstance(result, EvmPaymentResult):
        invoice = result.invoice
        print(f"Base network invoice:")
        print(f"  Amount: {invoice.invoice_amount} {invoice.token_symbol}")
        print(f"  Chain: {invoice.invoice_chain_name}")


async def premium_usdt_polygon():
    """Gift Premium with USDT on Polygon.

    WARNING: EXPERIMENTAL — NOT TESTED IN PRODUCTION.
    Polygon offers very low gas fees for USDT transfers.
    """
    client = FragmentClient(cookies=COOKIES)

    result = await client.purchase_premium(
        username="target_user",
        months=3,
        payment_method="usdt_pol",
    )

    if isinstance(result, EvmPaymentResult):
        invoice = result.invoice
        print(f"Polygon invoice:")
        print(f"  Amount: {invoice.invoice_amount} USDT")
        print(f"  Address: {invoice.invoice_address}")
        print(f"  Expires: {invoice.expires_at}")


if __name__ == "__main__":
    asyncio.run(purchase_stars_usdt_eth())