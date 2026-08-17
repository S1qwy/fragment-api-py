"""
Basic client setup examples.

Demonstrates different ways to initialize FragmentClient:
- Full mode (cookies + seed + api_key)
- EVM-only mode (cookies without stel_ton_token)
- Read-only mode (cookies only)
"""

import asyncio
from FragmentAPI import FragmentClient


async def full_mode_setup():
    """Initialize client with full capabilities: wallet + cookies."""
    client = FragmentClient(
        cookies={
            "stel_ssid": "your_ssid",
            "stel_dt": "-180",
            "stel_token": "your_token",
            "stel_ton_token": "your_ton_token",
        },
        seed="word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24",
        api_key="your_tonapi_or_toncenter_api_key_here_at_least_48_chars_long_xxxxx",
        api_provider="tonapi",
        wallet_version="V5R1",
        timeout=30.0,
    )
    print(client)


async def full_mode_toncenter():
    """Initialize client with Toncenter API provider instead of Tonapi."""
    client = FragmentClient(
        cookies={
            "stel_ssid": "your_ssid",
            "stel_dt": "-180",
            "stel_token": "your_token",
            "stel_ton_token": "your_ton_token",
        },
        seed="word1 word2 ... word24",
        api_key="your_toncenter_api_key_here_at_least_48_chars_long_xxxxxxxxx",
        api_provider="toncenter",
        wallet_version="V5R1",
    )
    print(f"Using Toncenter: {client}")


async def full_mode_highload():
    """Initialize client with HighloadWalletV3 for maximum batch throughput."""
    client = FragmentClient(
        cookies={
            "stel_ssid": "your_ssid",
            "stel_dt": "-180",
            "stel_token": "your_token",
            "stel_ton_token": "your_ton_token",
        },
        seed="word1 word2 ... word24",
        api_key="your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx",
        wallet_version="HIGHLOAD_V3",
    )
    print(f"Highload wallet: max {254} messages per batch")


async def evm_only_mode():
    """Initialize client without stel_ton_token for EVM payments only.

    When stel_ton_token is absent, wallet-dependent operations
    (get_wallet, topup_gram, place_bid, etc.) are disabled.
    EVM payment methods (usdt_eth, usdc_base, etc.) still work
    for Stars and Premium purchases.
    """
    client = FragmentClient(
        cookies={
            "stel_ssid": "your_ssid",
            "stel_dt": "-180",
            "stel_token": "your_token",
        },
    )
    print(f"EVM-only mode: has_wallet={client.has_wallet}, has_ton_token={client.has_ton_token}")


async def cookies_from_string():
    """Initialize client using a cookie string instead of a dict."""
    cookie_string = "stel_ssid=abc123; stel_dt=-180; stel_token=xyz789; stel_ton_token=tok456"
    client = FragmentClient(cookies=cookie_string)
    print(f"From string: {client}")


async def cookies_from_json():
    """Initialize client using a JSON cookie string."""
    import json
    cookie_json = json.dumps({
        "stel_ssid": "abc123",
        "stel_dt": "-180",
        "stel_token": "xyz789",
        "stel_ton_token": "tok456",
    })
    client = FragmentClient(cookies=cookie_json)
    print(f"From JSON: {client}")


async def context_manager_usage():
    """Use FragmentClient as an async context manager."""
    async with FragmentClient(
        cookies="stel_ssid=abc; stel_dt=-180; stel_token=xyz; stel_ton_token=tok",
        seed="word1 word2 ... word24",
        api_key="your_api_key_here_at_least_48_chars_long_xxxxxxxxxxxxxxxxx",
    ) as client:
        print(f"Inside context: {client}")


if __name__ == "__main__":
    asyncio.run(full_mode_setup())