"""
Asynchronous Fragment API client (extra)

Async client for Fragment.com API with full async/await support.
Install with: pip install fragment-api-py[async]
"""

from __future__ import annotations

import json
from typing import Any, cast

import httpx

from FragmentAPI.exceptions import ConfigError, CookieError
from FragmentAPI.methods.giveaway_premium import giveaway_premium
from FragmentAPI.methods.giveaway_stars import giveaway_stars
from FragmentAPI.methods.purchase_premium import purchase_premium
from FragmentAPI.methods.purchase_stars import purchase_stars
from FragmentAPI.methods.search import (
    search_gifts,
    search_numbers,
    search_usernames,
)
from FragmentAPI.methods.topup_ton import topup_ton
from FragmentAPI.types.constants import (
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
    REQUIRED_COOKIE_KEYS,
    SUPPORTED_WALLET_VERSIONS,
    WalletVersionType,
    TONAPI_DEFAULT_KEY,
)
from FragmentAPI.types.results import (
    AdsTopupResult,
    GiftsResult,
    GiveawayPremiumResult,
    GiveawayStarsResult,
    NumbersResult,
    PremiumResult,
    StarsResult,
    UsernamesResult,
    WalletInfo,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)
from FragmentAPI.utils.wallet import fetch_wallet_info


class AsyncFragmentClient:
    """
    Asynchronous client for the Fragment.com API.

    Args:
        seed: 24-word mnemonic phrase for the TON wallet.
        api_key: API key for TON blockchain interactions.
        cookies: Fragment session cookies as a dict or JSON string.
        wallet_version: Wallet contract version - "V4R2" or "V5R1" (default).
        timeout: HTTP request timeout in seconds. Defaults to 30.0.

    Raises:
        ConfigError: If seed, api_key, or wallet_version are missing or invalid.
        CookieError: If cookies cannot be parsed or are missing required keys.

    Example::

        async with AsyncFragmentClient(
            seed="word1 word2 ...",
            api_key="your-api-key",
            cookies={"stel_ssid": "...", "stel_dt": "...", ...},
        ) as client:
            print(await client.get_wallet())
            result = await client.purchase_premium("@username", months=6)
            print(result.transaction_id)
    """

    def __init__(
        self,
        seed: str,
        cookies: dict | str,
        api_key: str | None = None,
        wallet_version: str = "V5R1",
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        missing = [
            name
            for name, val in (("seed", seed),)
            if not val or not str(val).strip()
        ]
        if missing:
            raise ConfigError(
                ConfigError.MISSING_PARAMS.format(keys=", ".join(missing))
            )

        word_count = len(seed.split())
        if word_count not in (12, 18, 24):
            raise ConfigError(
                ConfigError.BAD_MNEMONIC.format(count=word_count)
            )

        if api_key and len(api_key.strip()) < 48:
            raise ConfigError(
                ConfigError.BAD_API_KEY.format(length=len(api_key.strip()))
            )

        if isinstance(cookies, str):
            cookies_str = cookies.strip()
            if cookies_str.startswith('{'):
                try:
                    cookies = json.loads(cookies_str)
                except Exception as exc:
                    raise CookieError(CookieError.PARSE_FAILED.format(exc=exc)) from exc
            else:
                parsed_cookies = {}
                for item in cookies_str.split(';'):
                    if '=' in item:
                        k, v = item.strip().split('=', 1)
                        parsed_cookies[k] = v
                cookies = parsed_cookies

        missing_keys = [
            k
            for k in REQUIRED_COOKIE_KEYS
            if not str(cast(dict, cookies).get(k, "")).strip()
        ]
        if missing_keys:
            raise CookieError(
                CookieError.MISSING_KEYS.format(keys=", ".join(missing_keys))
            )

        version = wallet_version.strip().upper()
        if version not in SUPPORTED_WALLET_VERSIONS:
            raise ConfigError(
                ConfigError.BAD_WALLET_VERSION.format(
                    version=version,
                    supported=", ".join(sorted(SUPPORTED_WALLET_VERSIONS)),
                )
            )

        self.seed: str = seed.strip()
        self.api_key: str = (api_key or TONAPI_DEFAULT_KEY).strip()
        self.cookies: dict = cast(dict, cookies)
        self.wallet_version: WalletVersionType = version  # type: ignore[assignment]
        self.timeout: float = timeout

    async def __aenter__(self) -> "AsyncFragmentClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"AsyncFragmentClient(wallet_version='{self.wallet_version}', "
            f"cookies={len(self.cookies)} keys)"
        )

    async def purchase_premium(
        self,
        username: str,
        months: int,
        show_sender: bool = True,
    ) -> PremiumResult:
        """Gift Telegram Premium to a user.

        Args:
            username: Recipient's Telegram username (with or without @).
            months: Duration - 3, 6, or 12.
            show_sender: Show your name as the sender. Defaults to True.

        Returns:
            PremiumResult with transaction_id, username, and amount.
        """
        return await purchase_premium(self, username, months, show_sender)

    async def purchase_stars(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
    ) -> StarsResult:
        """Send Telegram Stars to a user.

        Args:
            username: Recipient's Telegram username (with or without @).
            amount: Number of stars - integer from 50 to 1 000 000.
            show_sender: Show your name as the gift sender. Defaults to True.

        Returns:
            StarsResult with transaction_id, username, and amount.
        """
        return await purchase_stars(self, username, amount, show_sender)

    async def topup_ton(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
    ) -> AdsTopupResult:
        """Top up TON to a recipient's Telegram Ads balance.

        Args:
            username: Recipient's Telegram username (with or without @).
            amount: Amount in TON - integer from 1 to 1 000 000 000.
            show_sender: Show your name as the sender. Defaults to True.

        Returns:
            AdsTopupResult with transaction_id, username, and amount.
        """
        return await topup_ton(self, username, amount, show_sender)

    async def giveaway_stars(
        self,
        channel: str,
        winners: int,
        amount: int,
    ) -> GiveawayStarsResult:
        """Run a Telegram Stars giveaway for a channel.

        Args:
            channel: Channel username (with or without @).
            winners: Number of winners - integer from 1 to 5.
            amount: Stars each winner receives - 500 to 1 000 000.

        Returns:
            GiveawayStarsResult with transaction_id, channel, winners, and amount.
        """
        return await giveaway_stars(self, channel, winners, amount)

    async def giveaway_premium(
        self,
        channel: str,
        winners: int,
        months: int = 3,
    ) -> GiveawayPremiumResult:
        """Run a Telegram Premium giveaway for a channel.

        Args:
            channel: Channel username (with or without @).
            winners: Number of winners - positive integer up to 24 000.
            months: Premium duration per winner - 3, 6, or 12. Defaults to 3.

        Returns:
            GiveawayPremiumResult with transaction_id, channel, winners, and amount.
        """
        return await giveaway_premium(self, channel, winners, months)

    async def get_wallet(self) -> WalletInfo:
        """Return the address, state and balance of the TON wallet.

        Returns:
            WalletInfo with address, state, and balance in TON.
        """
        return await fetch_wallet_info(self)

    async def search_usernames(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        """Search Fragment marketplace for Telegram usernames.

        Args:
            query: Search text. Empty string browses all.
            sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
            filter: Filter - "auction", "sale", "sold", or "" (available).
            offset_id: Pagination cursor from previous result.

        Returns:
            UsernamesResult with items and next_offset_id.
        """
        return await search_usernames(
            self, query, sort=sort, filter=filter, offset_id=offset_id
        )

    async def search_numbers(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        """Search Fragment marketplace for anonymous Telegram numbers.

        Args:
            query: Search text. Empty string browses all.
            sort: Sort order - "price_desc", "price_asc", "listed", or "ending".
            filter: Filter - "auction", "sale", "sold", or "" (available).
            offset_id: Pagination cursor from previous result.

        Returns:
            NumbersResult with items and next_offset_id.
        """
        return await search_numbers(
            self, query, sort=sort, filter=filter, offset_id=offset_id
        )

    async def search_gifts(
        self,
        query: str = "",
        collection: str | None = None,
        sort: str | None = None,
        filter: str | None = None,
        view: str | None = None,
        attr: dict[str, list[str]] | None = None,
        offset: int | None = None,
    ) -> GiftsResult:
        """Search Fragment gifts marketplace.

        Args:
            query: Search text. Empty string browses all.
            collection: Gift collection slug.
            sort: Sort order.
            filter: Filter value.
            view: Active attribute tab name.
            attr: Attribute filters.
            offset: Page offset from previous result.

        Returns:
            GiftsResult with items and next_offset.
        """
        return await search_gifts(
            self,
            query,
            collection=collection,
            sort=sort,
            filter=filter,
            view=view,
            attr=attr,
            offset=offset,
        )

    async def call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        *,
        page_url: str = FRAGMENT_BASE_URL,
    ) -> dict[str, Any]:
        """Send a raw request to the Fragment API.

        Useful for accessing undocumented or future Fragment API methods.

        Args:
            method: Fragment API method name.
            data: Additional form-data fields.
            page_url: Fragment page URL for API hash derivation.

        Returns:
            Raw parsed JSON response as dict.

        Example::

            result = await client.call(
                "searchPremiumGiftRecipient",
                {"query": "@username", "months": 3},
                page_url="https://fragment.com/premium/gift",
            )
        """
        headers = build_headers(page_url)
        async with httpx.AsyncClient(
            cookies=self.cookies, timeout=self.timeout
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                self.cookies, headers, page_url, self.timeout
            )
            return await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {"method": method, **(data or {})},
            )
