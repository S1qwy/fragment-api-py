'''
Synchronous Fragment API client with all methods
'''

from __future__ import annotations

import json
import re
from typing import Any, cast

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    CookieError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
)
from FragmentAPI.methods.giveaway_premium import giveaway_premium_sync
from FragmentAPI.methods.giveaway_stars import giveaway_stars_sync
from FragmentAPI.methods.place_bid import place_bid_sync
from FragmentAPI.methods.purchase_premium import purchase_premium_sync
from FragmentAPI.methods.purchase_stars import purchase_stars_sync
from FragmentAPI.methods.search import (
    search_gifts_sync,
    search_numbers_sync,
    search_usernames_sync,
)
from FragmentAPI.methods.topup_ton import topup_ton_sync
from FragmentAPI.types.constants import (
    DEFAULT_TIMEOUT,
    FRAGMENT_BASE_URL,
    NUMBERS_PAGE,
    GIFTS_PAGE,
    PREMIUM_PAGE,
    PREMIUM_HISTORY_PAGE,
    PROFILE_PAGE,
    REQUIRED_COOKIE_KEYS,
    SESSIONS_PAGE,
    STARS_PAGE,
    STARS_HISTORY_PAGE,
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
    UsernameInfo,
    UsernamesResult,
    WalletInfo,
)
from FragmentAPI.utils.auth import authenticate_sync
from FragmentAPI.utils.html import (
    parse_auction_info,
    parse_bid_history,
    parse_gift_attributes,
    parse_gift_issued,
    parse_item_status,
    parse_owner_history,
    parse_premium_history,
    parse_premium_options,
    parse_profile,
    parse_sessions,
    parse_sold_owner,
    parse_stars_history,
    parse_stars_packages,
    parse_stars_price_from_html,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash_sync,
    fetch_page_ajax_sync,
    post_FragmentAPI_sync,
)
from FragmentAPI.utils.wallet import fetch_wallet_info_sync


class FragmentClient:
    '''Synchronous client for the Fragment.com API.'''

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
                    raise CookieError(
                        CookieError.PARSE_FAILED.format(exc=exc)
                    ) from exc
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

    def __enter__(self) -> "FragmentClient":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"FragmentClient(wallet_version='{self.wallet_version}', "
            f"cookies={len(self.cookies)} keys)"
        )

    @staticmethod
    def authenticate(
        seed: str,
        wallet_version: str = "V4R2",
        telegram_auth_data: str | None = None,
        telegram_phone: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, str]:
        '''Authenticate with Fragment and return session cookies.'''
        return authenticate_sync(seed, wallet_version, telegram_auth_data, telegram_phone, timeout)

    def purchase_premium(
        self,
        username: str,
        months: int,
        show_sender: bool = True,
        payment_method: str = "ton",
    ) -> PremiumResult:
        '''Gift Telegram Premium to a user.'''
        return purchase_premium_sync(self, username, months, show_sender, payment_method)

    def purchase_stars(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
        payment_method: str = "ton",
    ) -> StarsResult:
        '''Send Telegram Stars to a user.'''
        return purchase_stars_sync(self, username, amount, show_sender, payment_method)

    def topup_ton(
        self,
        username: str,
        amount: int,
        show_sender: bool = True,
    ) -> AdsTopupResult:
        '''Top up TON to a recipient Telegram Ads balance.'''
        return topup_ton_sync(self, username, amount, show_sender)

    def giveaway_stars(
        self,
        channel: str,
        winners: int,
        amount: int,
        payment_method: str = "ton",
    ) -> GiveawayStarsResult:
        '''Run a Telegram Stars giveaway for a channel.'''
        return giveaway_stars_sync(self, channel, winners, amount, payment_method)

    def giveaway_premium(
        self,
        channel: str,
        winners: int,
        months: int = 3,
        payment_method: str = "ton",
    ) -> GiveawayPremiumResult:
        '''Run a Telegram Premium giveaway for a channel.'''
        return giveaway_premium_sync(self, channel, winners, months, payment_method)

    def place_bid(
        self,
        item_type: int,
        slug: str,
        bid: int,
    ) -> BidResult:
        '''Place a bid or buy-now on a Fragment marketplace item.

        Args:
            item_type: Item type - 1 (username), 3 (number), 5 (gift).
            slug: Item identifier (username without @, number without +, gift slug).
            bid: Bid amount in TON (integer). Must be >= minimum bid or == buy-now price.

        Returns:
            BidResult with transaction_id, item_type, slug, bid, and confirm info.
        '''
        return place_bid_sync(self, item_type, slug, bid)

    def get_wallet(self) -> WalletInfo:
        '''Return the address, state, TON and USDT balance of the wallet.'''
        return fetch_wallet_info_sync(self)

    def search_usernames(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> UsernamesResult:
        '''Search Fragment marketplace for Telegram usernames.'''
        return search_usernames_sync(
            self, query, sort=sort, filter=filter, offset_id=offset_id
        )

    def search_numbers(
        self,
        query: str = "",
        sort: str | None = None,
        filter: str | None = None,
        offset_id: str | None = None,
    ) -> NumbersResult:
        '''Search Fragment marketplace for anonymous Telegram numbers.'''
        return search_numbers_sync(
            self, query, sort=sort, filter=filter, offset_id=offset_id
        )

    def search_gifts(
        self,
        query: str = "",
        collection: str | None = None,
        sort: str | None = None,
        filter: str | None = None,
        view: str | None = None,
        attr: dict[str, list[str]] | None = None,
        offset: int | None = None,
    ) -> GiftsResult:
        '''Search Fragment gifts marketplace.'''
        return search_gifts_sync(
            self, query,
            collection=collection, sort=sort, filter=filter,
            view=view, attr=attr, offset=offset,
        )

    def get_username_info(self, username: str) -> UsernameInfo:
        '''Get detailed information about a Fragment username.'''
        try:
            url = f"{FRAGMENT_BASE_URL}/username/{username.lstrip('@')}"
            headers = build_headers(url)
            data = fetch_page_ajax_sync(self.cookies, headers, url, self.timeout)

            html = data.get("h", "")
            state = data.get("s", {})

            status = parse_item_status(html)
            auction = parse_auction_info(html)
            bids, bid_offset = parse_bid_history(html)
            owners, owner_offset = parse_owner_history(html)

            timer_m = re.search(r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"', html)
            auction_end = timer_m.group(1) if timer_m else None

            owner_wallet = parse_sold_owner(html)
            purchased_m = re.search(r'Purchased on\s*<time[^>]+datetime="([^"]+)"', html)
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_number_info(self, number: str) -> NumberInfo:
        '''Get detailed information about a Fragment number.'''
        try:
            clean = number.replace("+", "").replace(" ", "").replace("-", "")
            url = f"{FRAGMENT_BASE_URL}/number/{clean}"
            headers = build_headers(url)
            data = fetch_page_ajax_sync(self.cookies, headers, url, self.timeout)

            html = data.get("h", "")
            state = data.get("s", {})

            status = parse_item_status(html)
            restricted = bool(re.search(r'tm-status-restricted', html))
            auction = parse_auction_info(html)
            bids, bid_offset = parse_bid_history(html)
            owners, owner_offset = parse_owner_history(html)

            timer_m = re.search(r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"', html)
            auction_end = timer_m.group(1) if timer_m else None

            owner_wallet = parse_sold_owner(html)
            purchased_m = re.search(r'Purchased on\s*<time[^>]+datetime="([^"]+)"', html)
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_gift_info(self, slug: str) -> GiftInfo:
        '''Get detailed information about a Fragment gift.'''
        try:
            url = f"{FRAGMENT_BASE_URL}/gift/{slug}"
            headers = build_headers(url)
            data = fetch_page_ajax_sync(self.cookies, headers, url, self.timeout)

            html = data.get("h", "")
            state = data.get("s", {})

            status = parse_item_status(html)
            auction = parse_auction_info(html)
            bids, bid_offset = parse_bid_history(html)
            owners, owner_offset = parse_owner_history(html)
            attributes = parse_gift_attributes(html)
            issued = parse_gift_issued(html)

            timer_m = re.search(r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"', html)
            auction_end = timer_m.group(1) if timer_m else None

            owner_wallet = parse_sold_owner(html)
            purchased_m = re.search(r'Purchased on\s*<time[^>]+datetime="([^"]+)"', html)
            purchased_date = purchased_m.group(1) if purchased_m else None

            image_m = re.search(r'<img\s+src="(https://nft\.fragment\.com/gift/[^"]+)"', html)
            image_url = image_m.group(1) if image_m else None

            sticker_m = re.search(r'srcset="(https://nft\.fragment\.com/gift/[^"]+\.tgs)"', html)
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_stars_prices(self) -> StarsPrices:
        '''Get all available Telegram Stars package prices.'''
        try:
            headers = build_headers(STARS_PAGE)
            data = fetch_page_ajax_sync(self.cookies, headers, STARS_PAGE, self.timeout)
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_stars_price(self, quantity: int) -> StarsPrice:
        '''Get price for a specific quantity of Telegram Stars.'''
        try:
            headers = build_headers(STARS_PAGE)
            fragment_hash = fetch_fragment_hash_sync(
                self.cookies, headers, STARS_PAGE, self.timeout
            )
            with httpx.Client(
                cookies=self.cookies, timeout=self.timeout
            ) as session:
                result = post_FragmentAPI_sync(
                    session, fragment_hash, headers,
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_premium_prices(self) -> PremiumPrices:
        '''Get Telegram Premium subscription prices.'''
        try:
            headers = build_headers(PREMIUM_PAGE)
            data = fetch_page_ajax_sync(self.cookies, headers, PREMIUM_PAGE, self.timeout)
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_stars_history(self, sort: str = "desc") -> list[StarsTransaction]:
        '''Get Telegram Stars transaction history.'''
        try:
            url = f"{STARS_HISTORY_PAGE}?sort={sort}"
            headers = build_headers(STARS_HISTORY_PAGE)
            data = fetch_page_ajax_sync(self.cookies, headers, url, self.timeout)
            html = data.get("h", "")
            return parse_stars_history(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_premium_history(self, sort: str = "desc") -> list[PremiumTransaction]:
        '''Get Telegram Premium transaction history.'''
        try:
            url = f"{PREMIUM_HISTORY_PAGE}?sort={sort}"
            headers = build_headers(PREMIUM_HISTORY_PAGE)
            data = fetch_page_ajax_sync(self.cookies, headers, url, self.timeout)
            html = data.get("h", "")
            return parse_premium_history(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_profile(self) -> ProfileInfo:
        '''Get Fragment account profile information.'''
        try:
            headers = build_headers(PROFILE_PAGE)
            data = fetch_page_ajax_sync(self.cookies, headers, PROFILE_PAGE, self.timeout)
            html = data.get("h", "")
            js = data.get("j", "")
            return parse_profile(html + js)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_sessions(self) -> list[SessionInfo]:
        '''Get active Fragment sessions.'''
        try:
            headers = build_headers(SESSIONS_PAGE)
            data = fetch_page_ajax_sync(self.cookies, headers, SESSIONS_PAGE, self.timeout)
            html = data.get("h", "")
            return parse_sessions(html)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def terminate_session(self, session_id: str) -> bool:
        '''Terminate a Fragment session by ID.'''
        try:
            headers = build_headers(SESSIONS_PAGE)
            fragment_hash = fetch_fragment_hash_sync(
                self.cookies, headers, SESSIONS_PAGE, self.timeout
            )
            with httpx.Client(
                cookies=self.cookies, timeout=self.timeout
            ) as session:
                result = post_FragmentAPI_sync(
                    session, fragment_hash, headers,
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_orders_history(
        self,
        item_type: int,
        username: str,
        offset_id: str,
    ) -> dict[str, Any]:
        '''Load more bid/orders history for an item.'''
        try:
            url = f"{FRAGMENT_BASE_URL}/username/{username}" if item_type == 1 else (
                f"{FRAGMENT_BASE_URL}/number/{username}" if item_type == 3 else
                f"{FRAGMENT_BASE_URL}/gift/{username}"
            )
            headers = build_headers(url)
            fragment_hash = fetch_fragment_hash_sync(
                self.cookies, headers, url, self.timeout
            )
            with httpx.Client(
                cookies=self.cookies, timeout=self.timeout
            ) as session:
                result = post_FragmentAPI_sync(
                    session, fragment_hash, headers,
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc

    def get_owners_history(
        self,
        item_type: int,
        username: str,
        offset_id: str,
    ) -> dict[str, Any]:
        '''Load more ownership history for an item.'''
        try:
            url = f"{FRAGMENT_BASE_URL}/username/{username}" if item_type == 1 else (
                f"{FRAGMENT_BASE_URL}/number/{username}" if item_type == 3 else
                f"{FRAGMENT_BASE_URL}/gift/{username}"
            )
            headers = build_headers(url)
            fragment_hash = fetch_fragment_hash_sync(
                self.cookies, headers, url, self.timeout
            )
            with httpx.Client(
                cookies=self.cookies, timeout=self.timeout
            ) as session:
                result = post_FragmentAPI_sync(
                    session, fragment_hash, headers,
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
                UnexpectedError.UNEXPECTED.format(exc=exc)
            ) from exc
    
    def get_login_code(self, number: str) -> LoginCodeResult:
        '''Fetch the current pending login code for an anonymous number.'''
        from FragmentAPI.methods.anonymous_number import get_login_code_sync
        return get_login_code_sync(self, number)

    def toggle_login_codes(self, number: str, can_receive: bool) -> None:
        '''Enable or disable login code delivery for an anonymous number.'''
        from FragmentAPI.methods.anonymous_number import toggle_login_codes_sync
        return toggle_login_codes_sync(self, number, can_receive)

    def terminate_sessions(self, number: str) -> TerminateSessionsResult:
        '''Terminate all active Telegram sessions for an anonymous number.'''
        from FragmentAPI.methods.anonymous_number import terminate_sessions_sync
        return terminate_sessions_sync(self, number)
    
    def call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        *,
        page_url: str = FRAGMENT_BASE_URL,
    ) -> dict[str, Any]:
        '''Send a raw request to the Fragment API.'''
        headers = build_headers(page_url)
        with httpx.Client(
            cookies=self.cookies, timeout=self.timeout
        ) as session:
            fragment_hash = fetch_fragment_hash_sync(
                self.cookies, headers, page_url, self.timeout
            )
            return post_FragmentAPI_sync(
                session,
                fragment_hash,
                headers,
                {"method": method, **(data or {})},
            )