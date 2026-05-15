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
    UserNotFoundError,
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
    ADS_TOPUP_PAGE,
    DEFAULT_TIMEOUT,
    DEVICE_FINGERPRINT,
    FRAGMENT_BASE_URL,
    GIFTS_PAGE,
    MY_BIDS_PAGE,
    MY_GIFTS_PAGE,
    MY_NUMBERS_PAGE,
    MY_USERNAMES_PAGE,
    NFT_WITHDRAW_PAGE,
    NUMBERS_PAGE,
    PREMIUM_GIFT_PAGE,
    PREMIUM_GIVEAWAY_PAGE,
    PREMIUM_HISTORY_PAGE,
    PREMIUM_PAGE,
    PROFILE_PAGE,
    REQUIRED_COOKIE_KEYS,
    SESSIONS_PAGE,
    STARS_GIVEAWAY_PAGE,
    STARS_HISTORY_PAGE,
    STARS_PAGE,
    STARS_WITHDRAW_PAGE,
    SUPPORTED_WALLET_VERSIONS,
    TONAPI_DEFAULT_KEY,
    WalletVersionType,
)
from FragmentAPI.types.results import (
    AdsTopupResult,
    AssignResult,
    AssignAccountsResult,
    BidResult,
    GiftInfo,
    GiftsResult,
    GiveawayPremiumResult,
    GiveawayStarsResult,
    LoginCodeResult,
    MyAssetsResult,
    MyBidsResult,
    NftTransferRecipient,
    NftTransferRequest,
    NftWithdrawalInitResult,
    NftWithdrawalConfirmResult,
    NumberInfo,
    NumbersResult,
    PremiumPrices,
    PremiumResult,
    PremiumTransaction,
    ProfileInfo,
    RecipientInfo,
    SessionInfo,
    StarsPrice,
    StarsPrices,
    StarsResult,
    StarsTransaction,
    StarsWithdrawalState,
    StarsWithdrawalInitResult,
    StarsWithdrawalConfirmResult,
    StartAuctionResult,
    TerminateSessionsResult,
    TopupTransaction,
    TransactionResult,
    UsernameInfo,
    UsernamesResult,
    WalletInfo,
)
from FragmentAPI.utils.auth import authenticate
from FragmentAPI.utils.html import (
    parse_assign_accounts,
    parse_auction_info,
    parse_bid_history,
    parse_gift_attributes,
    parse_gift_issued,
    parse_item_status,
    parse_my_assets,
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
    execute_transaction,
    fetch_wallet_info,
)


def _parse_recipient_from_result(
    result: dict[str, Any],
) -> RecipientInfo | None:
    '''
    Extract RecipientInfo from a Fragment search API result.
    '''
    found = result.get("found")
    if not found or not found.get("recipient"):
        return None

    photo_html = found.get("photo", "")
    photo_match = re.search(r'src="([^"]+)"', photo_html)

    return RecipientInfo(
        recipient=found["recipient"],
        name=found.get("name", ""),
        photo_url=photo_match.group(1) if photo_match else None,
        myself=found.get("myself", False),
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

    async def get_stars_recipient(
        self,
        username: str,
    ) -> RecipientInfo | None:
        '''
        Search for a Stars gift recipient on Fragment.

        Args:
            username: Telegram username (with or without @).

        Returns:
            RecipientInfo or None if not found.
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
                        "method": "searchStarsRecipient",
                        "query": username,
                        "quantity": "",
                    },
                )
            return _parse_recipient_from_result(result)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_premium_recipient(
        self,
        username: str,
        months: int = 3,
    ) -> RecipientInfo | None:
        '''
        Search for a Premium gift recipient on Fragment.

        Args:
            username: Telegram username (with or without @).
            months: Premium duration (3, 6, or 12).

        Returns:
            RecipientInfo or None if not found.
        '''
        try:
            headers = build_headers(PREMIUM_GIFT_PAGE)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                PREMIUM_GIFT_PAGE,
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
                        "method": "searchPremiumGiftRecipient",
                        "query": username,
                        "months": months,
                    },
                )
            return _parse_recipient_from_result(result)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_ads_topup_recipient(
        self,
        username: str,
    ) -> RecipientInfo | None:
        '''
        Search for an Ads top-up recipient on Fragment.

        Args:
            username: Telegram username (with or without @).

        Returns:
            RecipientInfo or None if not found.
        '''
        try:
            headers = build_headers(ADS_TOPUP_PAGE)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                ADS_TOPUP_PAGE,
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
                        "method": "searchAdsTopupRecipient",
                        "query": username,
                    },
                )
            return _parse_recipient_from_result(result)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_giveaway_stars_recipient(
        self,
        channel: str,
        winners: int = 1,
        amount: int = 500,
    ) -> RecipientInfo | None:
        '''
        Search for a Stars giveaway channel recipient on Fragment.

        Args:
            channel: Channel username (with or without @).
            winners: Number of winners.
            amount: Total stars amount.

        Returns:
            RecipientInfo or None if not found.
        '''
        try:
            headers = build_headers(STARS_GIVEAWAY_PAGE)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                STARS_GIVEAWAY_PAGE,
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
                        "method": "searchStarsGiveawayRecipient",
                        "query": channel,
                        "quantity": winners,
                        "stars": amount,
                    },
                )
            return _parse_recipient_from_result(result)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_giveaway_premium_recipient(
        self,
        channel: str,
        winners: int = 1,
        months: int = 3,
    ) -> RecipientInfo | None:
        '''
        Search for a Premium giveaway channel recipient on Fragment.

        Args:
            channel: Channel username (with or without @).
            winners: Number of winners.
            months: Premium duration (3, 6, or 12).

        Returns:
            RecipientInfo or None if not found.
        '''
        try:
            headers = build_headers(PREMIUM_GIVEAWAY_PAGE)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                PREMIUM_GIVEAWAY_PAGE,
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
                        "method": "searchPremiumGiveawayRecipient",
                        "query": channel,
                        "quantity": winners,
                        "months": months,
                    },
                )
            return _parse_recipient_from_result(result)
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

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

    async def get_my_assets(
        self,
        item_type: str = "usernames",
    ) -> MyAssetsResult:
        '''
        Get My Assets from Fragment.

        Args:
            item_type: "usernames", "numbers", or "gifts".

        Returns:
            MyAssetsResult with items, ton_rate, and total_count.
        '''
        try:
            page_map = {
                "usernames": MY_USERNAMES_PAGE,
                "numbers": MY_NUMBERS_PAGE,
                "gifts": MY_GIFTS_PAGE,
            }

            if item_type not in page_map:
                raise ConfigError(f"Invalid item_type: {item_type}")

            url = page_map[item_type]
            headers = build_headers(url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            html = data.get("h", "")
            items, total_count = parse_my_assets(html, item_type)
            ton_rate = data.get("s", {}).get("tonRate", 0.0)

            return MyAssetsResult(
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

    async def get_assign_accounts(
        self,
        item_type: int,
        slug: str,
    ) -> "AssignAccountsResult":
        '''
        Get list of Telegram accounts available for assignment.

        Args:
            item_type: 1 (username), 5 (gift).
            slug: Item identifier.

        Returns:
            AssignAccountsResult with accounts list and can_disable flag.
        '''
        try:
            if item_type == 1:
                url = MY_USERNAMES_PAGE
            else:
                url = MY_GIFTS_PAGE

            headers = build_headers(url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            html = data.get("h", "")
            accounts, can_disable = parse_assign_accounts(html)

            return AssignAccountsResult(
                accounts=accounts,
                can_disable=can_disable,
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def assign_to_telegram(
        self,
        item_type: int,
        slug: str,
        assign_to: str | None = None,
    ) -> AssignResult:
        '''
        Assign a username or gift to a Telegram account.

        Args:
            item_type: 1 (username), 5 (gift).
            slug: Item identifier.
            assign_to: Telegram account ID or None to remove.

        Returns:
            AssignResult with status and optional payment info.
        '''
        try:
            url = f"{FRAGMENT_BASE_URL}/" + (
                f"username/{slug}" if item_type == 1 else f"gift/{slug}"
            )
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
                data = {
                    "type": str(item_type),
                    "username": slug,
                    "method": "assignToTgAccount",
                }
                if assign_to is not None:
                    data["assign_to"] = assign_to

                result = await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    data,
                )

            if result.get("error"):
                return AssignResult(ok=False, message=result["error"])

            if result.get("need_pay"):
                return AssignResult(
                    ok=True,
                    need_pay=True,
                    req_id=result.get("req_id"),
                    amount=result.get("amount"),
                )

            return AssignResult(
                ok=result.get("ok", False),
                message=result.get("msg"),
                assign_name=result.get("assign_name"),
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def start_auction(
        self,
        item_type: int,
        slug: str,
        min_amount: int,
        max_amount: int = 0,
    ) -> StartAuctionResult:
        '''
        Start an auction for a username or gift.

        Args:
            item_type: 1 (username), 5 (gift).
            slug: Item identifier.
            min_amount: Minimum bid in TON.
            max_amount: Maximum price (buy now), 0 for auction only.

        Returns:
            StartAuctionResult with req_id.
        '''
        try:
            url = f"{FRAGMENT_BASE_URL}/" + (
                f"username/{slug}" if item_type == 1 else f"gift/{slug}"
            )
            headers = build_headers(url)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                url,
                self.timeout,
            )

            can_sell = await self.call(
                "canSellItem",
                {
                    "type": str(item_type),
                    "username": slug,
                    "auction": "true" if max_amount == 0 else "false",
                },
                page_url=url,
            )

            if not can_sell.get("ok"):
                return StartAuctionResult(ok=False)

            account = await build_account_info(self)

            async with httpx.AsyncClient(
                cookies=self.cookies,
                timeout=self.timeout,
            ) as session:
                transaction = await post_FragmentAPI(
                    session,
                    fragment_hash,
                    headers,
                    {
                        "method": "getStartAuctionLink",
                        "account": json.dumps(account),
                        "device": DEVICE_FINGERPRINT,
                        "transaction": "1",
                        "type": str(item_type),
                        "username": slug,
                        "min_amount": str(min_amount),
                        "max_amount": str(max_amount),
                    },
                )

            if transaction.get("error"):
                return StartAuctionResult(ok=False)

            confirm_params = transaction.get("confirm_params", {})
            await execute_transaction(self, transaction)

            return StartAuctionResult(
                ok=True,
                req_id=confirm_params.get("id"),
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def sell_asset(
        self,
        item_type: int,
        slug: str,
        price: int,
    ) -> StartAuctionResult:
        '''
        Sell a username or gift at a fixed price.

        Args:
            item_type: 1 (username), 5 (gift).
            slug: Item identifier.
            price: Fixed price in TON.

        Returns:
            StartAuctionResult with req_id.
        '''
        return await self.start_auction(item_type, slug, price, price)

    async def search_nft_transfer_recipient(
        self,
        query: str,
    ) -> NftTransferRecipient | None:
        '''
        Search for a recipient to transfer NFT.

        Args:
            query: Telegram username.

        Returns:
            NftTransferRecipient or None if not found.
        '''
        try:
            headers = build_headers(FRAGMENT_BASE_URL)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                FRAGMENT_BASE_URL,
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
                        "method": "searchNftTransferRecipient",
                        "query": query,
                    },
                )

            if result.get("error") or not result.get("found"):
                return None

            found = result["found"]
            photo_match = re.search(r'src="([^"]+)"', found.get("photo", ""))
            return NftTransferRecipient(
                myself=found.get("myself", False),
                recipient=found.get("recipient", ""),
                name=found.get("name", ""),
                photo_url=photo_match.group(1) if photo_match else None,
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def init_nft_transfer(
        self,
        slug: str,
        recipient: str,
    ) -> NftTransferRequest:
        '''
        Initialize NFT transfer request.

        Args:
            slug: Gift slug.
            recipient: Recipient ID from search.

        Returns:
            NftTransferRequest with req_id and content.
        '''
        try:
            url = f"{FRAGMENT_BASE_URL}/gift/{slug}/transfer"
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
                        "method": "initNftTransferRequest",
                        "slug": slug,
                        "recipient": recipient,
                    },
                )

            if result.get("error"):
                raise FragmentAPIError(result["error"])

            return NftTransferRequest(
                req_id=result.get("req_id", ""),
                myself=result.get("myself", False),
                item_title=result.get("item_title", ""),
                content=result.get("content", ""),
                button=result.get("button", ""),
            )
        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def transfer_nft(
        self,
        req_id: str,
        show_sender: bool = True,
    ) -> TransactionResult:
        '''
        Execute NFT transfer.

        Args:
            req_id: Request ID from init_nft_transfer.
            show_sender: Show your name to the recipient.

        Returns:
            TransactionResult with transaction details.
        '''
        try:
            account = await build_account_info(self)

            transaction = await self.call(
                "getNftTransferLink",
                {
                    "account": json.dumps(account),
                    "device": DEVICE_FINGERPRINT,
                    "transaction": "1",
                    "id": req_id,
                    "show_sender": "1" if show_sender else "0",
                },
            )

            tx_result = await execute_transaction(self, transaction)

            if tx_result.boc and req_id:
                try:
                    await self.confirm_request(req_id, tx_result.boc)
                except Exception:
                    pass

            return tx_result
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

    async def get_nft_withdrawal_state(
        self,
        transaction: str,
    ) -> dict[str, Any]:
        '''
        Get NFT withdrawal state from Fragment page.

        Args:
            transaction: Transaction ID for withdrawal.

        Returns:
            Raw JSON response with state data.

        Raises:
            FragmentAPIError: If session expired.
        '''
        try:
            page_url = f"{NFT_WITHDRAW_PAGE}?transaction={transaction}"
            headers = build_headers(page_url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                page_url,
                self.timeout,
            )

            if data.get("mode") == "done" and "expired" in data.get("html", ""):
                raise FragmentAPIError(
                    "NFT withdrawal session has expired. "
                    "Please start the withdrawal process again."
                )

            return data

        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def init_nft_withdrawal(
        self,
        transaction: str,
        keep_gift: bool = False,
    ) -> NftWithdrawalInitResult:
        '''
        Initialize NFT withdrawal to wallet.

        Args:
            transaction: Transaction ID for withdrawal.
            keep_gift: Whether to keep gift visible in Telegram profile.

        Returns:
            NftWithdrawalInitResult with confirm_hash for next step.
        '''
        try:
            wallet_info = await self.get_wallet()
            wallet_address = wallet_info.address

            headers = build_headers(FRAGMENT_BASE_URL)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                FRAGMENT_BASE_URL,
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
                        "method": "initNftWithdrawalRequest",
                        "transaction": transaction,
                        "wallet_address": wallet_address,
                        "keep_gift": "1" if keep_gift else "0",
                    },
                )

            if result.get("error"):
                return NftWithdrawalInitResult(
                    ok=False,
                    error=result["error"],
                )

            return NftWithdrawalInitResult(
                ok=result.get("ok", False),
                confirm_message=result.get("confirm_message"),
                confirm_button=result.get("confirm_button"),
                confirm_hash=result.get("confirm_hash"),
            )

        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def confirm_nft_withdrawal(
        self,
        transaction: str,
        confirm_hash: str,
        keep_gift: bool = False,
    ) -> NftWithdrawalConfirmResult:
        '''
        Confirm NFT withdrawal after user approval.

        Args:
            transaction: Transaction ID for withdrawal.
            confirm_hash: Hash from init_nft_withdrawal response.
            keep_gift: Whether to keep gift visible in Telegram profile.

        Returns:
            NftWithdrawalConfirmResult with processing status.
        '''
        try:
            wallet_info = await self.get_wallet()
            wallet_address = wallet_info.address

            headers = build_headers(FRAGMENT_BASE_URL)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                FRAGMENT_BASE_URL,
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
                        "method": "initNftWithdrawalRequest",
                        "transaction": transaction,
                        "wallet_address": wallet_address,
                        "keep_gift": "1" if keep_gift else "0",
                        "confirm_hash": confirm_hash,
                    },
                )

            if result.get("error"):
                return NftWithdrawalConfirmResult(
                    ok=False,
                    need_update=False,
                    mode="error",
                    error=result["error"],
                )

            return NftWithdrawalConfirmResult(
                ok=result.get("ok", False),
                need_update=result.get("need_update", False),
                mode=result.get("mode", "unknown"),
                html=result.get("html"),
            )

        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def get_stars_withdrawal_state(
        self,
        transaction: str,
    ) -> StarsWithdrawalState:
        '''
        Get Stars withdrawal state from Fragment page.

        Args:
            transaction: Transaction ID for withdrawal.

        Returns:
            StarsWithdrawalState with transaction and withdrawal_data.

        Raises:
            FragmentAPIError: If session expired or state not found.
        '''
        try:
            page_url = f"{STARS_WITHDRAW_PAGE}?transaction={transaction}"
            headers = build_headers(page_url)
            data = await fetch_page_ajax(
                self.cookies,
                headers,
                page_url,
                self.timeout,
            )

            if data.get("mode") == "done" and "expired" in data.get("html", ""):
                raise FragmentAPIError(
                    "Stars withdrawal session has expired. "
                    "Please start the withdrawal process again."
                )

            state = data.get("s", {})
            tx_id = state.get("transaction")
            withdrawal_data = state.get("withdrawalData")

            if not tx_id or not withdrawal_data:
                raise FragmentAPIError(
                    "Failed to extract transaction or withdrawalData from response."
                )

            return StarsWithdrawalState(
                transaction=tx_id,
                withdrawal_data=withdrawal_data,
            )

        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def init_stars_withdrawal(
        self,
        transaction: str,
        withdrawal_data: str,
    ) -> StarsWithdrawalInitResult:
        '''
        Initialize Stars withdrawal to wallet.

        Args:
            transaction: Transaction ID for withdrawal.
            withdrawal_data: Withdrawal data from get_stars_withdrawal_state.

        Returns:
            StarsWithdrawalInitResult with confirm_hash for next step.
        '''
        try:
            wallet_info = await self.get_wallet()
            wallet_address = wallet_info.address

            headers = build_headers(FRAGMENT_BASE_URL)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                FRAGMENT_BASE_URL,
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
                        "method": "initStarsRevenueWithdrawalRequest",
                        "transaction": transaction,
                        "wallet_address": wallet_address,
                        "withdrawal_data": withdrawal_data,
                    },
                )

            if result.get("error"):
                return StarsWithdrawalInitResult(
                    ok=False,
                    error=result["error"],
                )

            return StarsWithdrawalInitResult(
                ok=result.get("ok", False),
                confirm_message=result.get("confirm_message"),
                confirm_button=result.get("confirm_button"),
                confirm_hash=result.get("confirm_hash"),
            )

        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

    async def confirm_stars_withdrawal(
        self,
        transaction: str,
        withdrawal_data: str,
        confirm_hash: str,
    ) -> StarsWithdrawalConfirmResult:
        '''
        Confirm Stars withdrawal after user approval.

        Args:
            transaction: Transaction ID for withdrawal.
            withdrawal_data: Withdrawal data from get_stars_withdrawal_state.
            confirm_hash: Hash from init_stars_withdrawal response.

        Returns:
            StarsWithdrawalConfirmResult with processing status.
        '''
        try:
            wallet_info = await self.get_wallet()
            wallet_address = wallet_info.address

            headers = build_headers(FRAGMENT_BASE_URL)
            fragment_hash = await fetch_fragment_hash(
                self.cookies,
                headers,
                FRAGMENT_BASE_URL,
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
                        "method": "initStarsRevenueWithdrawalRequest",
                        "transaction": transaction,
                        "wallet_address": wallet_address,
                        "withdrawal_data": withdrawal_data,
                        "confirm_hash": confirm_hash,
                    },
                )

            if result.get("error"):
                return StarsWithdrawalConfirmResult(
                    ok=False,
                    need_update=False,
                    mode="error",
                    error=result["error"],
                )

            return StarsWithdrawalConfirmResult(
                ok=result.get("ok", False),
                need_update=result.get("need_update", False),
                mode=result.get("mode", "unknown"),
                html=result.get("html"),
            )

        except FragmentBaseError:
            raise
        except Exception as exc:
            raise UnexpectedError(
                UnexpectedError.UNEXPECTED.format(exc=exc),
            ) from exc

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