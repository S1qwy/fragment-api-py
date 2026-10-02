"""Supported aliases without implying that v13 has no breaking changes."""

from FragmentAPI import (
    ConfigError,
    ConfigurationError,
    StarsPrice,
    StarsPrices,
    StarsTransaction,
    WalletInfo,
)
from FragmentAPI.utils.validation import normalize_payment_method

from _common import run


async def aliases() -> None:
    """Verify compatibility properties and payment aliases without network access."""
    assert ConfigError is ConfigurationError
    assert normalize_payment_method("gram") == "ton"
    assert normalize_payment_method("usdt_gram") == "usdt_ton"

    price = StarsPrice(stars=100, gram_price="1.25", usd_price="2.50")
    prices = StarsPrices(packages=[price], gram_rate=2.0)
    wallet = WalletInfo(
        address="display-only",
        state="active",
        gram_balance=10.0,
        usdt_balance=None,
        balance_nanoton=10_000_000_000,
    )
    history = StarsTransaction(
        recipient="example",
        stars=100,
        price_gram="1.25",
        date="2025-01-01",
    )

    assert price.ton_price == price.gram_price
    assert prices.ton_rate == prices.gram_rate
    assert wallet.balance_ton == wallet.gram_balance
    assert wallet.balance_usdt is None
    assert history.price_ton == history.price_gram
    print("Supported compatibility aliases verified.")
    print("MarketApp integration and cross-invoice transaction batching were removed.")


if __name__ == "__main__":
    run({"aliases": aliases}, "aliases")