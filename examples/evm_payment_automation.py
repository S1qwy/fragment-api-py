"""Inspect EVM invoices for an external payment integration.

This example intentionally does not sign or broadcast EVM transactions.
The SDK returns invoices; payment execution and reconciliation remain external.
"""

import time

from FragmentAPI import EvmPaymentResult, TransactionError

from _common import make_client, required, run, show_result


async def invoice(method: str) -> None:
    """Request and inspect an invoice using exact raw token units."""
    async with make_client() as client:
        result = await client.purchase_stars(
            required("FRAGMENT_TARGET"),
            100,
            payment_method=method,
        )
        if not isinstance(result, EvmPaymentResult):
            raise TransactionError("Expected an EVM invoice.")
        value = result.invoice
        if value.expires_at and value.expires_at <= int(time.time()):
            raise TransactionError("The invoice has expired.")
        show_result(result)
        print("Before external signing, verify the RPC chain ID and token contract.")
        print("Use invoice_amount_raw rather than the display float.")
        print("A successful chain receipt alone does not prove Fragment fulfillment.")


async def ethereum() -> None:
    """Request USDT on Ethereum."""
    await invoice("usdt_eth")


async def base() -> None:
    """Request USDC on Base."""
    await invoice("usdc_base")


async def polygon() -> None:
    """Request USDT on Polygon."""
    await invoice("usdt_pol")


if __name__ == "__main__":
    run({"ethereum": ethereum, "base": base, "polygon": polygon}, "base")