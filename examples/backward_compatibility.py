"""
Backward compatibility examples.

Demonstrates that code written for v9.x continues to work
with v10.x through property aliases and method aliases.
All renamed fields (ton -> gram) have backward-compatible accessors.
"""

import asyncio
from FragmentAPI import FragmentClient, ConfigurationError

try:
    from FragmentAPI import ConfigError
    print("ConfigError alias available (backward compat)")
except ImportError:
    print("ConfigError not available")


COOKIES = "stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok"
SEED = "word " * 24
API_KEY = "x" * 48


async def ton_rate_aliases():
    """Demonstrate that ton_rate properties still work."""
    client = FragmentClient(cookies=COOKIES)

    prices = await client.get_stars_prices()
    print(f"gram_rate: {prices.gram_rate}")
    print(f"ton_rate (alias): {prices.ton_rate}")
    assert prices.gram_rate == prices.ton_rate

    for pkg in prices.packages[:2]:
        print(f"  gram_price: {pkg.gram_price}")
        print(f"  ton_price (alias): {pkg.ton_price}")
        assert pkg.gram_price == pkg.ton_price


async def wallet_balance_aliases():
    """Demonstrate that balance_ton property still works on WalletInfo."""
    client = FragmentClient(cookies=COOKIES, seed=SEED, api_key=API_KEY)

    wallet = await client.get_wallet()
    print(f"gram_balance: {wallet.gram_balance}")
    print(f"balance_ton (alias): {wallet.balance_ton}")
    assert wallet.gram_balance == wallet.balance_ton


async def topup_ton_still_works():
    """Demonstrate that topup_ton() is an alias for topup_gram()."""
    print("topup_ton() is available and delegates to topup_gram()")
    print("Both accept the same parameters and return the same result type")


async def payment_method_aliases():
    """Demonstrate that 'ton' and 'gram' payment methods are equivalent."""
    print("'gram' and 'ton' are treated identically:")
    print("  payment_method='gram'  ->  internally uses 'ton' for Fragment API")
    print("  payment_method='ton'   ->  works as before")
    print("  payment_method='usdt_gram'  ->  internally uses 'usdt_ton'")
    print("  payment_method='usdt_ton'   ->  works as before")


async def config_error_alias():
    """Demonstrate that ConfigError is an alias for ConfigurationError."""
    assert ConfigError is ConfigurationError
    print("ConfigError is ConfigurationError: True")

    try:
        raise ConfigError("test")
    except ConfigurationError:
        print("ConfigError caught as ConfigurationError")


async def history_price_aliases():
    """Demonstrate that price_ton aliases work on transaction history."""
    client = FragmentClient(cookies=COOKIES)

    transactions = await client.get_stars_history()
    if transactions:
        tx = transactions[0]
        print(f"price_gram: {tx.price_gram}")
        print(f"price_ton (alias): {tx.price_ton}")
        assert tx.price_gram == tx.price_ton


if __name__ == "__main__":
    asyncio.run(ton_rate_aliases())