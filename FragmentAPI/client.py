'''
Async Fragment API client with seqno/balance confirmation and confirmReq.

Single async client for Fragment.com API.
All sync code removed. Uses httpx.AsyncClient throughout.
'''

from __future__ import annotations

import json
import re
from typing import (
    Any,
    cast,
)

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    CookieError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
)
from FragmentAPI.methods.giveaway_premium import giveaway_premium
from FragmentAPI.methods.giveaway_stars import giveaway_stars
from FragmentAPI.methods.place_bid import place_bid
from FragmentAPI.methods.purchase_premium import purchase_premium
from FragmentAPI.methods.purchase_stars import purchase_stars
from FragmentAPI.methods.search import (
    search_gifts,
    search_numbers,
    search_usernames,
)
from FragmentAPI.methods.topup_ton import topup_ton
from FragmentAPI.types.constants import (
    ADS_HISTORY_PAGE,
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
    GIFTS_PAGE,
    MY_BIDS_PAGE,
    NUMBERS_PAGE,
    PREMIUM_HISTORY_PAGE,
    PREMIUM_PAGE,
    PROFILE_PAGE,
    REQUIRED_COOKIE_KEYS,
    SESSIONS_PAGE,
    STARS_HISTORY_PAGE,
    STARS_PAGE,
    SUPPORTED_WALLET_VERSIONS,
    TONAPI_DEFAULT_KEY,
    WalletVersionType,
)
from FragmentAPI.types.results import (
    AdsTopupResult,
    BidResult,
    GiftInfo,
    GiftsResult,
    GiveawayPremiumResult,
    GiveawayStarsResult,
    LoginCodeResult,
    MyBidsResult,
    NumberInfo,
    NumbersResult,
    PremiumPrices,
    PremiumResult,
    PremiumTransaction,
    ProfileInfo,
    SessionInfo,
    StarsPrice,
    StarsPrices,
    StarsResult,
    StarsTransaction,
    TerminateSessionsResult,
    TopupTransaction,
    UsernameInfo,
    UsernamesResult,
    WalletInfo,
)
from FragmentAPI.utils.auth import authenticate
from FragmentAPI.utils.html import (
    parse_auction_info,
    parse_bid_history,
    parse_gift_attributes,
    parse_gift_issued,
    parse_item_status,
    parse_my_bids,
    parse_owner_history,
    parse_premium_history,
    parse_premium_options,
    parse_profile,
    parse_sessions,
    parse_sold_owner,
    parse_stars_history,
    parse_stars_packages,
    parse_stars_price_from_html,
    parse_topup_history,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    fetch_page_ajax,
    post_FragmentAPI,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    fetch_wallet_info,
)


class FragmentClient:
    '''
    Async client for the Fragment.com API.

    All operations are async/await.
    Supports seqno/balance transaction confirmation and confirmReq.

    Args:
        seed: 24-word mnemonic phrase for the TON wallet.
        cookies: Fragment session cookies as a dict or JSON string.
        api_key: API key for TON blockchain interactions (optional).
        wallet_version: Wallet contract version — "V4R2" or "V5R1" (default).
        timeout: HTTP request timeout in seconds. Defaults to 30.0.

    Raises:
        ConfigError: If seed or wallet_version are missing or invalid.
        CookieError: If cookies cannot be parsed or are missing required keys.

    Example::

        async with FragmentClient(
            seed="word1 word2 ...",
            cookies={"stel_ssid": "...", "stel_dt": "...", ...},
        ) as client:
            wallet = await client.get_wallet()
            print(wallet)
            result = await client.purchase_stars("@username", 500)
            print(result.transaction_id)
    '''

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
                ConfigError.MISSING_PARAMS.format(
                    keys=", ".join(missing),
                )
            )

        word_count = len(seed.split())
        if word_count not in (12, 18, 24):
            raise ConfigError(
                ConfigError.BAD_MNEMONIC.format(
                    count=word_count,
                )
            )

        if api_key and len(api_key.strip()) < 48:
            raise ConfigError(
                ConfigError.BAD_API_KEY.format(
                    length=len(api_key.strip()),
                )
            )

        if isinstance(cookies, str):
            cookies_str = cookies.strip()
            if cookies_str.startswith("{"):
                try:
                    cookies = json.loads(cookies_str)
                except Exception as exc:
                    raise CookieError(
                        CookieError.PARSE_FAILED.format(exc=exc),
                    ) from exc
            else:
                parsed_cookies: dict[str, str] = {}
                for item in cookies_str.split(";"):
                    if "=" in item:
                        k, v = item.strip().split("=", 1)
                        parsed_cookies[k] = v
                cookies = parsed_cookies

        missing_keys = [
            k
            for k in REQUIRED_COOKIE_KEYS
            if not str(cast(dict, cookies).get(k, "")).strip()
        ]
        if missing_keys:
            raise CookieError(
                CookieError.MISSING_KEYS.format(
                    keys=", ".join(missing_keys),
                )
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

    async def __aenter__(self) -> "FragmentClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"FragmentClient("
            f"wallet_version='{self.wallet_version}', "
            f"cookies={len(self.cookies)} keys"
            f")"
        )

    @staticmethod
    async def authenticate(
        seed: str,
        wallet_version: str = "V4R2",
        telegram_auth_data: str | None = None,
        telegram_phone: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, str]:
        '''
        Authenticate with Fragment and return session cookies.
        '''
        return await authenticate(
            seed,
            wallet_version,
            telegram_auth_data,
            telegram_phone,
            timeout,
        )

    async def purchase_premium(
        self,
        username: str,
        months: int,
        show_sender: bool = True,
        payment_method: str = "ton",
    ) -> PremiumResult:
        '''
        Gift Telegram Premium to a user.

        Args:
            username: Recipient Telegram username (with or without @).
            months: Duration — 3, 6, or 12.
            show_sender: Show your name as the sender.
            payment_method: "ton" or "usdt_ton".

        Returns:
            PremiumResult with transaction_id, username, and amount.
        '''
        return await purchase_premium(
            self,
            username,
            months,
            show_sender,
            payment_method,
        )

    async def purchase_stars(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
        payment_method: str = "ton",
    ) -> StarsResult:
        '''
        Send Telegram Stars to a user.

        Args:
            username: Recipient Telegram username (with or without @).
            amount: Number of stars — integer from 50 to 10_000_000.
            show_sender: Show your name as the gift sender.
            payment_method: "ton" or "usdt_ton".

        Returns:
            StarsResult with transaction_id, username, and amount.
        '''
        return await purchase_stars(
            self,
            username,
            amount,
            show_sender,
            payment_method,
        )

    async def topup_ton(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
    ) -> AdsTopupResult:
        '''
        Top up TON to a recipient Telegram Ads balance.

        Args:
            username: Recipient Telegram username.
            amount: Amount in TON — integer from 1 to 1_000_000_000.
            show_sender: Show your name as the sender.

        Returns:
            AdsTopupResult with transaction_id, username, and amount.
        '''
        return await topup_ton(
            self,
            username,
            amount,
            show_sender,
        )

    async def giveaway_stars(
        self,
        channel: str,
        winners: int,
        amount: int,
        payment_method: str = "ton",
    ) -> GiveawayStarsResult:
        '''
        Run a Telegram Stars giveaway for a channel.
        '''
        return await giveaway_stars(
            self,
            channel,
            winners,
            amount,
            payment_method,
        )

    async def giveaway_premium(
        self,
        channel: str,
        winners: int,
        months: int = 3,
        payment_method: str = "ton",
    ) -> GiveawayPremiumResult:
        '''
        Run a Telegram Premium giveaway for a channel.
        '''
        return await giveaway_premium(
            self,
            channel,
            winners,
            months,
            payment_method,
        )

    async def place_bid(
        self,
        item_type: int,
        slug: str,
        bid: int,
    ) -> BidResult:
        '''
        Place a bid or buy-now on a Fragment marketplace item.

        Args:
            item_type: 1 (username), 3 (number), 5 (gift).
            slug: Item identifier.
            bid: Bid amount in TON (integer).

        Returns:
            BidResult with transaction details.
        '''
        return await place_bid(
            self,
            item_type,
            slug,
            bid,
        )

    async def get_wallet(self) -> WalletInfo:
        '''
        Return address, state, TON and USDT balance of the wallet.
        '''
        return await fetch_wallet_info(self)

    async def search_usernames(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        '''
        Search Fragment marketplace for Telegram usernames.
        '''
        return await search_usernames(
            self,
            query,
            sort=sort,
            filter=filter,
            offset_id=offset_id,
        )

    async def search_numbers(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        '''
        Search Fragment marketplace for anonymous Telegram numbers.
        '''
        return await search_numbers(
            self,
            query,
            sort=sort,
            filter=filter,
            offset_id=offset_id,
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
        '''
        Search Fragment gifts marketplace.
        '''
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

    async def get_username_info(
        self,
        username: str,
    ) -> UsernameInfo:
        '''
        Get detailed information about a Fragment username.
        '''
        try:
            url = f"{FRAGMENT_BASE_URL}/username/{username.lstrip('@')}"
            headers = build_headers(url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            html = data.get("h", "")
            state = data.get("s", {})

            status = parse_item_status(html)
            auction = parse_auction_info(html)
            bids, bid_offset = parse_bid_history(html)
            owners, owner_offset = parse_owner_history(html)

            timer_m = re.search(
                r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"',
                html,
            )
            auction_end = timer_m.group(1) if timer_m else None

            owner_wallet = parse_sold_owner(html)
            purchased_m = re.search(
                r'Purchased on\s*<time[^>]+datetime="([^"]+)"',
                html,
            )
            purchased_date = purchased_m.group(1) if purchased_m else None

            return UsernameInfo(
                username=state.get("username", username.lstrip("@")),
                status=status,
                item_type=state.get("type", 1),
                ton_rate=state.get("tonRate", 0.0),
                auction=auction,
                auction_end=auction_end,
                owner_wallet=owner_wallet,
                purchased_date=purchased_date,
                bid_history=bids,
                owner_history=owners,
                bid_history_next_offset=bid_offset,
                owner_history_next_offset=owner_offset,
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_number_info(
        self,
        number: str,
    ) -> NumberInfo:
        '''
        Get detailed information about a Fragment number.
        '''
        try:
            clean = number.replace("+", "").replace(" ", "").replace("-", "")
            url = f"{FRAGMENT_BASE_URL}/number/{clean}"
            headers = build_headers(url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            html = data.get("h", "")
            state = data.get("s", {})

            status = parse_item_status(html)
            restricted = bool(re.search(r"tm-status-restricted", html))
            auction = parse_auction_info(html)
            bids, bid_offset = parse_bid_history(html)
            owners, owner_offset = parse_owner_history(html)

            timer_m = re.search(
                r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"',
                html,
            )
            auction_end = timer_m.group(1) if timer_m else None

            owner_wallet = parse_sold_owner(html)
            purchased_m = re.search(
                r'Purchased on\s*<time[^>]+datetime="([^"]+)"',
                html,
            )
            purchased_date = purchased_m.group(1) if purchased_m else None

            return NumberInfo(
                number=state.get("username", clean),
                display_number=state.get("itemTitle", f"+{clean}"),
                status=status,
                item_type=state.get("type", 3),
                ton_rate=state.get("tonRate", 0.0),
                restricted=restricted,
                auction=auction,
                auction_end=auction_end,
                owner_wallet=owner_wallet,
                purchased_date=purchased_date,
                bid_history=bids,
                owner_history=owners,
                bid_history_next_offset=bid_offset,
                owner_history_next_offset=owner_offset,
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_gift_info(
        self,
        slug: str,
    ) -> GiftInfo:
        '''
        Get detailed information about a Fragment gift.
        '''
        try:
            url = f"{FRAGMENT_BASE_URL}/gift/{slug}"
            headers = build_headers(url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            html = data.get("h", "")
            state = data.get("s", {})

            status = parse_item_status(html)
            auction = parse_auction_info(html)
            bids, bid_offset = parse_bid_history(html)
            owners, owner_offset = parse_owner_history(html)
            attributes = parse_gift_attributes(html)
            issued = parse_gift_issued(html)

            timer_m = re.search(
                r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"',
                html,
            )
            auction_end = timer_m.group(1) if timer_m else None

            owner_wallet = parse_sold_owner(html)
            purchased_m = re.search(
                r'Purchased on\s*<time[^>]+datetime="([^"]+)"',
                html,
            )
            purchased_date = purchased_m.group(1) if purchased_m else None

            image_m = re.search(
                r'<img\s+src="(https://nft\.fragment\.com/gift/[^"]+)"',
                html,
            )
            image_url = image_m.group(1) if image_m else None

            sticker_m = re.search(
                r'srcset="(https://nft\.fragment\.com/gift/[^"]+\.tgs)"',
                html,
            )
            sticker_url = sticker_m.group(1) if sticker_m else None

            return GiftInfo(
                slug=state.get("username", slug),
                name=state.get("itemTitle", slug),
                status=status,
                item_type=state.get("type", 5),
                ton_rate=state.get("tonRate", 0.0),
                image_url=image_url,
                sticker_url=sticker_url,
                owner_wallet=owner_wallet,
                purchased_date=purchased_date,
                auction=auction,
                auction_end=auction_end,
                attributes=attributes,
                issued=issued,
                bid_history=bids,
                owner_history=owners,
                bid_history_next_offset=bid_offset,
                owner_history_next_offset=owner_offset,
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_stars_prices(self) -> StarsPrices:
        '''
        Get all available Telegram Stars package prices.
        '''
        try:
            headers = build_headers(STARS_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                STARS_PAGE,
                self.timeout,
            )
            html = data.get("h", "")
            state = data.get("s", {})
            packages = parse_stars_packages(html)
            return StarsPrices(
                packages=packages,
                ton_rate=state.get("tonRate", 0.0),
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_stars_price(
        self,
        quantity: int,
    ) -> StarsPrice:
        '''
        Get price for a specific quantity of Telegram Stars.
        '''
        try:
            headers = build_headers(STARS_PAGE)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                STARS_PAGE,
                self.timeout,
            )
            async with httpx.AsyncClient(
                cookies=self.cookies,
                timeout=self.timeout,
            ) as session:
                result = await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    {
                        "stars": "0",
                        "quantity": str(quantity),
                        "method": "updateStarsPrices",
                    },
                )
            cur_price_html = result.get("cur_price", "")
            ton_price, usd_price = parse_stars_price_from_html(cur_price_html)
            return StarsPrice(
                stars=quantity,
                ton_price=ton_price or "0",
                usd_price=usd_price or "0",
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_premium_prices(self) -> PremiumPrices:
        '''
        Get Telegram Premium subscription prices.
        '''
        try:
            headers = build_headers(PREMIUM_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                PREMIUM_PAGE,
                self.timeout,
            )
            html = data.get("h", "")
            state = data.get("s", {})
            options = parse_premium_options(html)
            return PremiumPrices(
                options=options,
                ton_rate=state.get("tonRate", 0.0),
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_stars_history(
        self,
        sort: str = "desc",
    ) -> list[StarsTransaction]:
        '''
        Get Telegram Stars transaction history.
        '''
        try:
            url = f"{STARS_HISTORY_PAGE}?sort={sort}"
            headers = build_headers(STARS_HISTORY_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )
            html = data.get("h", "")
            return parse_stars_history(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_premium_history(
        self,
        sort: str = "desc",
    ) -> list[PremiumTransaction]:
        '''
        Get Telegram Premium transaction history.
        '''
        try:
            url = f"{PREMIUM_HISTORY_PAGE}?sort={sort}"
            headers = build_headers(PREMIUM_HISTORY_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )
            html = data.get("h", "")
            return parse_premium_history(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc
            
    async def get_topup_history(
        self,
        sort: str = "asc",
    ) -> list["TopupTransaction"]:
        '''
        Get Telegram Ads topup transaction history.

        Args:
            sort: "asc" (oldest first) or "desc" (newest first).

        Returns:
            List of TopupTransaction objects.
        '''
        try:
            url = f"{ADS_HISTORY_PAGE}?type=topup&sort={sort}"
            headers = build_headers(ADS_HISTORY_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )
            html = data.get("h", "")
            return parse_topup_history(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_profile(self) -> ProfileInfo:
        '''
        Get Fragment account profile information.
        '''
        try:
            headers = build_headers(PROFILE_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                PROFILE_PAGE,
                self.timeout,
            )
            html = data.get("h", "")
            js = data.get("j", "")
            return parse_profile(html + js)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc
            
    async def get_my_bids(
        self,
        item_type: str = "usernames",
        sort: str = "desc",
    ) -> "MyBidsResult":
        '''
        Get My Bid History from Fragment.

        Args:
            item_type: "usernames", "numbers", or "gifts".
            sort: "asc" (oldest first) or "desc" (newest first).

        Returns:
            MyBidsResult with items, ton_rate, and total_count.
        '''
        try:
            if item_type not in ("usernames", "numbers", "gifts"):
                raise ConfigError(f"Invalid item_type: {item_type}")

            params = []
            if item_type != "usernames":
                params.append(f"type={item_type}")
            if sort:
                params.append(f"sort={sort}")

            url = MY_BIDS_PAGE
            if params:
                url += "?" + "&".join(params)

            headers = build_headers(MY_BIDS_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            html = data.get("h", "")
            items, total_count = parse_my_bids(html, item_type)
            ton_rate = data.get("s", {}).get("tonRate", 0.0)

            return MyBidsResult(
                items=items,
                ton_rate=ton_rate,
                total_count=total_count,
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_sessions(self) -> list[SessionInfo]:
        '''
        Get active Fragment sessions.
        '''
        try:
            headers = build_headers(SESSIONS_PAGE)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                SESSIONS_PAGE,
                self.timeout,
            )
            html = data.get("h", "")
            return parse_sessions(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def terminate_session(
        self,
        session_id: str,
    ) -> bool:
        '''
        Terminate a Fragment session by ID.
        '''
        try:
            headers = build_headers(SESSIONS_PAGE)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                SESSIONS_PAGE,
                self.timeout,
            )
            async with httpx.AsyncClient(
                cookies=self.cookies,
                timeout=self.timeout,
            ) as session:
                result = await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    {
                        "session_id": session_id,
                        "method": "tonTerminateSession",
                    },
                )
            return result.get("ok", False)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_orders_history(
        self,
        item_type: int,
        username: str,
        offset_id: str,
    ) -> dict[str, Any]:
        '''
        Load more bid/orders history for an item.
        '''
        try:
            if item_type == 1:
                url = f"{FRAGMENT_BASE_URL}/username/{username}"
            elif item_type == 3:
                url = f"{FRAGMENT_BASE_URL}/number/{username}"
            else:
                url = f"{FRAGMENT_BASE_URL}/gift/{username}"

            headers = build_headers(url)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                url,
                self.timeout,
            )
            async with httpx.AsyncClient(
                cookies=self.cookies,
                timeout=self.timeout,
            ) as session:
                result = await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    {
                        "type": str(item_type),
                        "username": username,
                        "offset_id": offset_id,
                        "method": "getOrdersHistory",
                    },
                )
            return result
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_owners_history(
        self,
        item_type: int,
        username: str,
        offset_id: str,
    ) -> dict[str, Any]:
        '''
        Load more ownership history for an item.
        '''
        try:
            if item_type == 1:
                url = f"{FRAGMENT_BASE_URL}/username/{username}"
            elif item_type == 3:
                url = f"{FRAGMENT_BASE_URL}/number/{username}"
            else:
                url = f"{FRAGMENT_BASE_URL}/gift/{username}"

            headers = build_headers(url)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                url,
                self.timeout,
            )
            async with httpx.AsyncClient(
                cookies=self.cookies,
                timeout=self.timeout,
            ) as session:
                result = await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    {
                        "type": str(item_type),
                        "username": username,
                        "offset_id": offset_id,
                        "method": "getOwnersHistory",
                    },
                )
            return result
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_login_code(
        self,
        number: str,
    ) -> LoginCodeResult:
        '''
        Fetch the current pending login code for an anonymous number.
        '''
        from FragmentAPI.methods.anonymous_number import get_login_code
        return await get_login_code(self, number)

    async def toggle_login_codes(
        self,
        number: str,
        can_receive: bool,
    ) -> None:
        '''
        Enable or disable login code delivery for an anonymous number.
        '''
        from FragmentAPI.methods.anonymous_number import toggle_login_codes
        return await toggle_login_codes(self, number, can_receive)

    async def terminate_sessions(
        self,
        number: str,
    ) -> TerminateSessionsResult:
        '''
        Terminate all active Telegram sessions for an anonymous number.
        '''
        from FragmentAPI.methods.anonymous_number import terminate_sessions
        return await terminate_sessions(self, number)

    async def confirm_request(
        self,
        req_id: str,
        boc: str,
        referer: str = "stars/buy",
    ) -> dict[str, Any]:
        '''
        Send confirmReq to Fragment after broadcasting a TON transaction.

        Notifies Fragment that the transaction BOC has been sent,
        which speeds up Stars/Premium delivery from ~30s to ~5s.

        Args:
            req_id: Request ID from initBuyStarsRequest or similar.
            boc: Signed transaction BOC in base64 format.
            referer: Fragment page path for the referer header.

        Returns:
            Raw Fragment API response dict.
        '''
        try:
            page_url = f"{FRAGMENT_BASE_URL}/{referer}"
            headers = build_headers(page_url)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                page_url,
                self.timeout,
            )
            async with httpx.AsyncClient(
                cookies=self.cookies,
                timeout=self.timeout,
            ) as session:
                return await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    {
                        "method": "confirmReq",
                        "id": str(req_id),
                        "boc": boc,
                    },
                )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        *,
        page_url: str = FRAGMENT_BASE_URL,
    ) -> dict[str, Any]:
        '''
        Send a raw request to the Fragment API.

        Args:
            method: Fragment API method name.
            data: Additional form-data fields.
            page_url: Fragment page URL for API hash derivation.

        Returns:
            Raw parsed JSON response as dict.
        '''
        headers = build_headers(page_url)
        async with httpx.AsyncClient(
            cookies=self.cookies,
            timeout=self.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                page_url,
                self.timeout,
            )
            return await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {"method": method, **(data or {})},
            )