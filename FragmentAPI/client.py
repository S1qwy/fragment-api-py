"""Async Fragment client with restricted wallet-auth fallback and explicit receipts."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any
from urllib.parse import quote, urlencode, urlsplit

from curl_cffi import requests

from FragmentAPI.exceptions import (
    AlreadySubscribedError,
    AnonymousNumberError,
    BroadcastUncertainError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    ParseError,
    TransactionError,
    UserNotFoundError,
)
from FragmentAPI.storage.base import SessionStorage
from FragmentAPI.types import constants as C
from FragmentAPI.types import models as M
from FragmentAPI.utils import html as H
from FragmentAPI.utils.auth import (
    auth_ton_proof,
    authenticate,
    fragment_cookies,
)
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.http import FragmentTransport, raise_api_error
from FragmentAPI.utils.proxy import build_curl_proxy_args, parse_proxy
from FragmentAPI.utils.validation import (
    decimal_units,
    integer,
    months as validate_months,
    normalize_payment_method,
    normalize_provider,
    normalize_seed,
    normalize_wallet_version,
    parse_cookies,
    recipient as normalize_recipient,
    stars_giveaway,
    validate_cookie_keys,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_prepared,
    execute_transaction,
    fetch_wallet_info,
    prepare_transaction,
)

_FLOWS = {
    "stars": (
        C.STARS_BUY_PAGE, "searchStarsRecipient", "updateStarsBuyState",
        "initBuyStarsRequest", "getBuyStarsLink",
    ),
    "premium": (
        C.PREMIUM_GIFT_PAGE, "searchPremiumGiftRecipient", "updatePremiumState",
        "initGiftPremiumRequest", "getGiftPremiumLink",
    ),
    "ton": (
        C.ADS_TOPUP_PAGE, "searchAdsTopupRecipient", "updateAdsTopupState",
        "initAdsTopupRequest", "getAdsTopupLink",
    ),
    "giveaway_stars": (
        C.STARS_GIVEAWAY_PAGE, "searchStarsGiveawayRecipient", "updateStarsGiveawayState",
        "initGiveawayStarsRequest", "getGiveawayStarsLink",
    ),
    "giveaway_premium": (
        C.PREMIUM_GIVEAWAY_PAGE, "searchPremiumGiveawayRecipient", "updatePremiumGiveawayState",
        "initGiveawayPremiumRequest", "getGiveawayPremiumLink",
    ),
    "ads_recharge": (
        C.ADS_PAY_PAGE, None, "updateAdsState",
        "initAdsRechargeRequest", "getAdsRechargeLink",
    ),
    "gateway": (
        C.GATEWAY_PAGE, None, "updateGatewayState",
        "initGatewayRechargeRequest", "getGatewayRechargeLink",
    ),
}


class FragmentClient:
    """Fragment client with cookie and restricted wallet-auth operating modes.

    Missing cookies selects wallet_auth. The shared V5R1 phrase authenticates
    the session only; it is never selected as the automatic paying wallet.
    Replace the SHARED_AUTH_SEED placeholder or pass shared_auth_seed before
    using that mode.

    A payer seed plus API key enables automatic broadcasting. Otherwise TON
    operations return PreparedTransaction. sender_account may specify the
    external signer's TON Connect account.

    Confirmation means Fragment reported a successful completed invoice.
    Broadcast acceptance alone is returned with confirmed=False.
    """

    def __init__(
        self,
        cookies: dict[str, str] | str | None = None,
        seed: str | None = None,
        api_key: str | None = None,
        api_provider: str = "tonapi",
        wallet_version: str = "V5R1",
        timeout: float = C.DEFAULT_TIMEOUT,
        proxy: str | None = None,
        session_storage: SessionStorage | None = None,
        session_id: str | None = None,
        auto_refresh_cookies: bool = False,
        *,
        shared_auth_seed: str | None = None,
        sender_account: dict[str, Any] | None = None,
        gas_reserve_nanoton: int = C.GAS_RESERVE_NANOTON,
        confirmation_timeout: float = C.CONFIRMATION_TIMEOUT,
        wallet_auth: bool | None = None,
    ) -> None:
        self.seed = normalize_seed(seed) if seed is not None else None
        self.api_key = api_key.strip() if api_key else None
        self.api_provider = normalize_provider(api_provider)
        self.wallet_version = normalize_wallet_version(wallet_version)
        if isinstance(timeout, bool) or timeout <= 0:
            raise ConfigurationError("timeout must be positive.")
        if isinstance(confirmation_timeout, bool) or confirmation_timeout <= 0:
            raise ConfigurationError("confirmation_timeout must be positive.")
        self.timeout = float(timeout)
        self.confirmation_timeout = float(confirmation_timeout)
        self.proxy = parse_proxy(proxy)["url"] if proxy else None
        self.gas_reserve_nanoton = integer(
            gas_reserve_nanoton, 0, 10 ** 18, "Invalid gas reserve."
        )
        self.cookies = parse_cookies(cookies) if cookies else {}
        inferred_wallet_auth = not bool(self.cookies)
        self._wallet_auth = inferred_wallet_auth if wallet_auth is None else bool(wallet_auth)
        if not self._wallet_auth:
            validate_cookie_keys(self.cookies, C.REQUIRED_COOKIE_KEYS)
        self.shared_auth_seed = shared_auth_seed or C.SHARED_AUTH_SEED
        self.sender_account = dict(sender_account) if sender_account else None
        if self.sender_account:
            required = {"address", "chain", "publicKey", "walletStateInit"}
            if required - self.sender_account.keys():
                raise ConfigurationError("sender_account must be a complete TON Connect account.")
            if str(self.sender_account["chain"]) != "-239":
                raise ConfigurationError("Only mainnet sender accounts are supported.")
        self._session_storage = session_storage
        self._session_id = session_id
        self._auto_refresh = auto_refresh_cookies
        self._session: requests.AsyncSession | None = None
        self._transport: FragmentTransport | None = None
        self._auth_lock = asyncio.Lock()
        self._wallet_lock = asyncio.Lock()
        self._flow_lock = asyncio.Lock()
        self._closed = False
        self._authenticated = bool(
            self.cookies.get("stel_ton_token") if self._wallet_auth else self.cookies
        )

    @property
    def wallet_auth(self) -> bool:
        """Return whether account-management access is restricted."""
        return self._wallet_auth

    @property
    def nokyc_mode(self) -> bool:
        """Compatibility alias for wallet_auth; server verification rules still apply."""
        return self.wallet_auth

    @property
    def has_wallet(self) -> bool:
        """Return whether automatic payment credentials are configured."""
        return self.seed is not None and self.api_key is not None

    @property
    def has_cookies(self) -> bool:
        """Return whether cookies currently exist."""
        return bool(self.cookies)

    @property
    def has_ton_token(self) -> bool:
        """Return whether a wallet-session cookie exists."""
        return bool(self.cookies.get("stel_ton_token"))

    @property
    def session_storage(self) -> SessionStorage | None:
        """Return the configured persistence backend."""
        return self._session_storage

    def __repr__(self) -> str:
        """Return configuration without credentials."""
        return (
            f"FragmentClient(wallet_version={self.wallet_version!r}, "
            f"wallet_auth={self.wallet_auth}, auto_pay={self.has_wallet})"
        )

    def _require_wallet(self) -> None:
        """Require automatic payment credentials."""
        if not self.seed:
            raise ConfigurationError(ConfigurationError.SEED_REQUIRED)
        if not self.api_key:
            raise ConfigurationError(ConfigurationError.API_KEY_REQUIRED)

    def _require_cookies(self) -> dict[str, str]:
        """Require an existing cookie jar."""
        if not self.cookies:
            raise ConfigurationError(ConfigurationError.COOKIES_REQUIRED)
        return self.cookies

    def _require_ton_token(self) -> None:
        """Require wallet-connected account cookies."""
        if not self.has_ton_token:
            raise ConfigurationError(ConfigurationError.TON_TOKEN_REQUIRED)

    def _require_not_nokyc(self, operation: str) -> None:
        """Compatibility guard for account-scoped operations."""
        self._require_account(operation)

    def _require_account(self, operation: str) -> None:
        """Block shared-wallet account state and destructive account actions."""
        if self.wallet_auth:
            raise ConfigurationError(
                ConfigurationError.WALLET_AUTH_UNSUPPORTED.format(operation=operation)
            )
        self._require_cookies()

    def _get_transport(self) -> FragmentTransport:
        """Lazily allocate one client-owned HTTP session."""
        if self._closed:
            raise ConfigurationError("FragmentClient is closed.")
        if self._session is None:
            self._session = requests.AsyncSession(
                cookies=self.cookies,
                timeout=self.timeout,
                impersonate="chrome",
                **build_curl_proxy_args(self.proxy),
            )
            self._transport = FragmentTransport(self._session, self.timeout)
        if self._transport is None:
            raise ConfigurationError("Transport initialization failed.")
        return self._transport

    async def _ensure_auth(self) -> None:
        """Initialize the restricted shared-wallet session once."""
        self._get_transport()
        if not self.wallet_auth or self._authenticated:
            return
        async with self._auth_lock:
            if self._authenticated:
                return
            seed = normalize_seed(self.shared_auth_seed)
            self.cookies = await auth_ton_proof(
                seed, "V5R1", self.timeout,
                proxy=self.proxy, session=self._session,
            )
            self._authenticated = True
            self._get_transport().invalidate()

    async def _save_cookies(self) -> None:
        """Persist only user-owned full-account sessions."""
        if self.wallet_auth:
            return
        if self._session is not None:
            self.cookies.update(fragment_cookies(self._session))
        if self._session_storage is not None and self._session_id and self.cookies:
            await self._session_storage.save(
                self._session_id, self.cookies, {"mode": "cookies"}
            )

    async def aclose(self) -> None:
        """Persist cookies and close the client-owned session even if persistence fails."""
        if self._closed:
            return
        try:
            await self._save_cookies()
        finally:
            self._closed = True
            session, self._session = self._session, None
            self._transport = None
            if session is not None:
                await session.close()

    async def __aenter__(self) -> FragmentClient:
        """Enter the asynchronous client context."""
        self._get_transport()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Release owned resources."""
        await self.aclose()

    @staticmethod
    async def authenticate(
        seed: str,
        wallet_version: str = "V5R1",
        phone: str | None = None,
        print_qr: bool = True,
        on_status: Any = None,
        timeout: float = C.DEFAULT_TIMEOUT,
        *,
        proxy: str | None = None,
    ) -> dict[str, str]:
        """Run explicit full-account authentication."""
        return await authenticate(
            seed, wallet_version, phone, print_qr, on_status, timeout,
            proxy=proxy,
        )

    async def refresh_cookies(self) -> dict[str, str]:
        """Refresh wallet proof without silently initiating Telegram OAuth."""
        transport = self._get_transport()
        async with self._auth_lock:
            if self.wallet_auth:
                seed, version = normalize_seed(self.shared_auth_seed), "V5R1"
            else:
                if not self.seed:
                    raise ConfigurationError(ConfigurationError.SEED_REQUIRED)
                seed, version = self.seed, self.wallet_version
            self.cookies = await auth_ton_proof(
                seed, version, self.timeout,
                proxy=self.proxy, session=self._session,
            )
            if not self.wallet_auth:
                validate_cookie_keys(self.cookies, C.REQUIRED_COOKIE_KEYS)
            self._authenticated = True
            transport.invalidate()
            await self._save_cookies()
            return dict(self.cookies)

    @classmethod
    async def from_storage(
        cls,
        session_storage: SessionStorage,
        session_id: str,
        **kwargs: Any,
    ) -> FragmentClient:
        """Load a user-owned session; perform explicit authentication if absent."""
        cookies = await session_storage.load(session_id)
        if not cookies:
            seed = kwargs.get("seed")
            if not seed:
                raise CookieError("Stored session was not found.")
            cookies = await authenticate(
                seed=seed,
                wallet_version=kwargs.get("wallet_version", "V5R1"),
                timeout=kwargs.get("timeout", C.DEFAULT_TIMEOUT),
                proxy=kwargs.get("proxy"),
            )
            await session_storage.save(session_id, cookies)
        return cls(
            cookies=cookies,
            session_storage=session_storage,
            session_id=session_id,
            **kwargs,
        )

    async def call(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        *,
        page_url: str = C.FRAGMENT_BASE_URL,
    ) -> dict[str, Any]:
        """Call an API method while enforcing wallet-auth capability restrictions."""
        method = str(method)
        if self.wallet_auth and method not in C.WALLET_AUTH_ALLOWED_METHODS:
            raise ConfigurationError(
                ConfigurationError.WALLET_AUTH_UNSUPPORTED.format(operation=method)
            )
        if self.wallet_auth:
            path = urlsplit(page_url).path
            if path.startswith("/my/") or "/withdraw" in path:
                raise ConfigurationError("Account pages are unavailable in wallet_auth mode.")
        await self._ensure_auth()
        result = await self._get_transport().call(method, data, page_url)
        error = str(result.get("error", "")).casefold()
        if self._auto_refresh and error in {"session expired", "unauthorized"}:
            await self.refresh_cookies()
            result = await self._get_transport().call(method, data, page_url)
        return result

    async def _api(
        self, method: str, data: dict[str, Any] | None = None,
        page_url: str = C.FRAGMENT_BASE_URL,
    ) -> dict[str, Any]:
        """Call and normalize Fragment application errors."""
        result = await self.call(method, data, page_url=page_url)
        raise_api_error(result)
        return result

    async def _page(self, page_url: str, *, account: bool = False) -> dict[str, Any]:
        """Fetch public or explicitly account-scoped page data."""
        if account:
            self._require_account("account page")
        await self._ensure_auth()
        result = await self._get_transport().page(page_url)
        raise_api_error(result)
        return result

    async def _recipient(
        self, method: str, query: str, page_url: str, **extra: Any,
    ) -> M.RecipientInfo | None:
        """Resolve a recipient while preserving non-recipient API failures."""
        query = normalize_recipient(query)
        result = await self.call(
            method, {"query": query, **extra}, page_url=page_url
        )
        error = str(result.get("error", "")).casefold()
        if "already subscribed" in error:
            raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
        if "assigned to a user" in error:
            raise UserNotFoundError(
                UserNotFoundError.NOT_A_USER.format(username=query)
            )
        if "no telegram users found" in error or "no telegram channels found" in error:
            return None
        raise_api_error(result)
        found = result.get("found")
        if not isinstance(found, dict) or not found.get("recipient"):
            return None
        photo = re.search(r'src=["\']([^"\']+)', str(found.get("photo", "")))
        return M.RecipientInfo(
            recipient=str(found["recipient"]),
            name=str(found.get("name", "")),
            photo_url=photo.group(1) if photo else None,
            myself=bool(found.get("myself", False)),
        )

    async def get_stars_recipient(self, username: str) -> M.RecipientInfo | None:
        """Resolve a Stars recipient."""
        return await self._recipient("searchStarsRecipient", username, C.STARS_BUY_PAGE, quantity="")

    async def get_premium_recipient(self, username: str, months: int = 3) -> M.RecipientInfo | None:
        """Resolve a Premium recipient."""
        validate_months(months)
        return await self._recipient("searchPremiumGiftRecipient", username, C.PREMIUM_GIFT_PAGE, months=months)

    async def get_ads_topup_recipient(self, username: str) -> M.RecipientInfo | None:
        """Resolve an Ads top-up recipient."""
        return await self._recipient("searchAdsTopupRecipient", username, C.ADS_TOPUP_PAGE)

    async def get_giveaway_stars_recipient(
        self, channel: str, winners: int = 1, amount: int = 500,
    ) -> M.RecipientInfo | None:
        """Resolve a channel using the original Stars package limits."""
        stars_giveaway(amount, winners)
        return await self._recipient(
            "searchStarsGiveawayRecipient", channel, C.STARS_GIVEAWAY_PAGE,
            quantity=winners, stars=amount,
        )

    async def get_giveaway_premium_recipient(
        self, channel: str, winners: int = 1, months: int = 3,
    ) -> M.RecipientInfo | None:
        """Resolve a Premium giveaway channel."""
        validate_months(months)
        integer(winners, 1, 24_000, ConfigurationError.INVALID_WINNERS_PREMIUM)
        return await self._recipient(
            "searchPremiumGiveawayRecipient", channel, C.PREMIUM_GIVEAWAY_PAGE,
            quantity=winners, months=months,
        )

    async def _confirm(
        self,
        transaction: dict[str, Any],
        receipt: M.TransactionResult,
        account: dict[str, Any],
        req_id: str,
        page_url: str,
        state_method: str | None,
    ) -> M.TransactionResult:
        """Report the signed BOC and poll only explicit successful completion."""
        if not receipt.boc:
            receipt.confirmation_error = "The wallet result did not contain a signed BOC."
            return receipt
        try:
            method = str(transaction.get("confirm_method") or "confirmReq")
            parameters = transaction.get("confirm_params") or {"id": req_id}
            if not isinstance(parameters, dict):
                raise ParseError("Invalid confirmation parameters.")
            await self._api(
                method,
                {
                    **parameters,
                    "account": json.dumps(account),
                    "device": C.DEVICE_FINGERPRINT,
                    "boc": receipt.boc,
                },
                page_url,
            )
            if state_method is None:
                return receipt
            deadline = time.monotonic() + self.confirmation_timeout
            mode = "new"
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                response = await asyncio.wait_for(
                    self._api(
                        state_method,
                        {"mode": mode, "lv": "false", "dh": str(time.time_ns())},
                        page_url,
                    ),
                    timeout=max(0.001, remaining),
                )
                mode = str(response.get("mode", mode))
                if mode == "done" and response.get("need_update") is False:
                    receipt.confirmed = True
                    receipt.status = "confirmed"
                    return receipt
                await asyncio.sleep(min(C.CONFIRMATION_INTERVAL, max(0, deadline - time.monotonic())))
            receipt.confirmation_error = "Fragment fulfillment confirmation timed out."
        except Exception as exc:
            receipt.confirmation_error = str(exc)
        return receipt

    async def _purchase_flow(
        self,
        kind: str,
        target: str,
        amount: int,
        *,
        payment_method: str = "ton",
        show_sender: bool = True,
        winners: int | None = None,
    ) -> tuple[M.TransactionResult, str] | M.PreparedTransaction | M.EvmPaymentResult:
        """Prepare, optionally broadcast, and confirm one invoice."""
        method = normalize_payment_method(payment_method)
        page, search_method, state_method, init_method, link_method = _FLOWS[kind]
        if kind in {"ton", "ads_recharge", "gateway"} and method != "ton":
            raise ConfigurationError("This operation supports native TON only.")
        async with self._flow_lock:
            await self._api(
                state_method,
                {"mode": "new", "lv": "false", "dh": str(time.time_ns())},
                page,
            )
            resolved: M.RecipientInfo | None = None
            search_extra: dict[str, Any] = {}
            if kind == "stars":
                search_extra["quantity"] = ""
            elif kind in {"premium", "giveaway_premium"}:
                search_extra["months"] = amount
            if winners is not None:
                search_extra["quantity"] = winners
            if kind == "giveaway_stars":
                search_extra["stars"] = amount
            if search_method:
                resolved = await self._recipient(
                    search_method, target, page, **search_extra
                )
                if resolved is None:
                    raise UserNotFoundError(
                        UserNotFoundError.NOT_FOUND.format(username=target)
                    )
            data: dict[str, Any] = (
                {"recipient": resolved.recipient}
                if resolved else {"account": target}
            )
            if kind == "stars":
                data["quantity"] = amount
            elif kind == "premium":
                data["months"] = amount
            elif kind == "giveaway_stars":
                data.update(quantity=winners, stars=amount)
                await self._api(
                    "updateStarsGiveawayPrices",
                    {"quantity": winners, "stars": amount}, page,
                )
            elif kind == "giveaway_premium":
                data.update(quantity=winners, months=amount)
                await self._api(
                    "updatePremiumGiveawayPrices", {"quantity": winners}, page
                )
            elif kind == "gateway":
                data["credits"] = amount
            else:
                data["amount"] = amount
            if kind not in {"ton", "ads_recharge", "gateway"}:
                data["payment_method"] = method
            initialized = await self._api(init_method, data, page)
            req_id = str(initialized.get("req_id") or "")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(context=kind)
                )

            if method in C.EVM_PAYMENT_METHODS:
                invoice = await fetch_evm_invoice(
                    self.cookies, urlsplit(page).path,
                    resolved.recipient if resolved else target,
                    method,
                    quantity=amount if kind == "stars" else winners if kind == "giveaway_stars" else None,
                    months=amount if kind in {"premium", "giveaway_premium"} else None,
                    amount=amount if kind == "giveaway_stars" else None,
                    winners=winners if kind == "giveaway_premium" else None,
                    timeout=self.timeout,
                    session=self._session,
                )
                return M.EvmPaymentResult(
                    item_kind=kind, target=target, amount=amount,
                    payment_method=method, invoice=invoice,
                )

            account = await build_account_info(self)
            transaction = await self._api(
                link_method,
                {
                    "account": json.dumps(account),
                    "device": C.DEVICE_FINGERPRINT,
                    "transaction": 1,
                    "id": req_id,
                    "show_sender": int(show_sender),
                },
                page,
            )
            if transaction.get("evm"):
                raise TransactionError(
                    "Fragment changed the selected TON payment flow to EVM."
                )

            principal: int | None = None
            usdt_units: int | None = None
            if method == "ton":
                raw_price = initialized.get("amount")
                if raw_price is None and kind in {"ton", "ads_recharge"}:
                    raw_price = amount
                if raw_price is not None:
                    principal = decimal_units(raw_price, 9)
            else:
                usdt_units = decimal_units(initialized.get("amount"), 6)

            prepared = prepare_transaction(
                transaction,
                payment_method=method,
                payment_nanoton=principal,
                wallet_version=self.wallet_version,
                item_kind=kind,
                target=target,
                amount=amount,
                req_id=req_id,
                sender_address=account["address"],
                confirm_referer=urlsplit(page).path.lstrip("/"),
                gas_reserve_nanoton=self.gas_reserve_nanoton,
            )
            if not self.has_wallet:
                return prepared
            if not self.wallet_auth:
                self._require_ton_token()
            receipt = await execute_prepared(
                self, prepared, required_usdt_units=usdt_units
            )
            receipt = await self._confirm(
                transaction, receipt, account, req_id, page, state_method
            )
            return receipt, req_id

    async def purchase_stars(
        self, username: str, amount: int,
        show_sender: bool = True, payment_method: str = "gram",
    ) -> M.PurchaseResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Purchase Stars with a fee only on native TON principal."""
        integer(amount, C.STARS_PURCHASE_MIN, C.STARS_PURCHASE_MAX, ConfigurationError.INVALID_STARS_AMOUNT)
        return await self._single_purchase("stars", username, amount, show_sender, payment_method)

    async def purchase_premium(
        self, username: str, months: int,
        show_sender: bool = True, payment_method: str = "gram",
    ) -> M.PurchaseResult | M.PreparedTransaction | M.EvmPaymentResult:
        """Gift Premium."""
        validate_months(months)
        return await self._single_purchase("premium", username, months, show_sender, payment_method)

    async def topup_gram(
        self, username: str, amount: int, show_sender: bool = True,
    ) -> M.PurchaseResult | M.PreparedTransaction:
        """Top up a recipient's Ads balance."""
        integer(amount, C.GRAM_TOPUP_MIN, C.GRAM_TOPUP_MAX, ConfigurationError.INVALID_GRAM_AMOUNT)
        return await self._single_purchase("ton", username, amount, show_sender, "ton")

    async def topup_ton(
        self, username: str, amount: int, show_sender: bool = True,
    ) -> M.PurchaseResult | M.PreparedTransaction:
        """Alias for native Ads top-up."""
        return await self.topup_gram(username, amount, show_sender)

    async def _single_purchase(
        self, kind: str, username: str, amount: int,
        show_sender: bool, payment_method: str,
    ) -> Any:
        """Normalize one purchase receipt."""
        username = normalize_recipient(username)
        result = await self._purchase_flow(
            kind, username, amount,
            payment_method=payment_method, show_sender=show_sender,
        )
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        return M.PurchaseResult(
            transaction_id=receipt.tx_hash,
            type=kind,
            username=username,
            amount=amount,
            payment_method=normalize_payment_method(payment_method),
            confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
            req_id=req_id,
            confirmation_error=receipt.confirmation_error,
        )

    async def purchase(
        self,
        items_or_type: list[Any] | dict[str, Any] | M.PurchaseItem | str,
        username: str | None = None,
        amount: int | None = None,
        months: int | None = None,
        show_sender: bool = True,
        payment_method: str = "gram",
    ) -> Any:
        """Dispatch a single purchase or an ordered multi-purchase batch."""
        if isinstance(items_or_type, list):
            return await self.batch_purchase(items_or_type, payment_method)
        if isinstance(items_or_type, M.PurchaseItem):
            item = items_or_type.model_dump()
        elif isinstance(items_or_type, dict):
            item = dict(items_or_type)
        elif isinstance(items_or_type, str):
            item = {
                "type": items_or_type, "username": username,
                "amount": amount, "months": months, "show_sender": show_sender,
            }
        else:
            raise ConfigurationError("Unsupported purchase input.")
        kind = item.get("type")
        target = item.get("username")
        sender = item.get("show_sender", True)
        if kind == "stars":
            return await self.purchase_stars(target, item.get("amount"), sender, payment_method)
        if kind == "premium":
            return await self.purchase_premium(target, item.get("months"), sender, payment_method)
        if kind in {"gram", "ton"}:
            if normalize_payment_method(payment_method) != "ton":
                raise ConfigurationError("Ads top-up requires native TON.")
            return await self.topup_gram(target, item.get("amount"), sender)
        raise ConfigurationError(f"Unsupported purchase type: {kind!r}")

    async def batch_purchase(
        self, items: list[dict[str, Any] | M.PurchaseItem],
        payment_method: str = "gram",
    ) -> M.BatchResult:
        """Execute ordered invoice transactions without splitting an invoice's messages.

        Each invoice, including its fee message, is atomic. This batch interface
        deliberately reports one broadcast per invoice rather than claiming
        cross-invoice atomicity.
        """
        method = normalize_payment_method(payment_method)
        if method not in {"ton", "usdt_ton"}:
            raise ConfigurationError("Batch purchases support TON and USDT-TON.")
        results: list[M.BatchItemResult] = []
        prepared: list[M.PreparedTransaction] = []
        sent = 0
        for index, raw in enumerate(items):
            item = raw.model_dump() if isinstance(raw, M.PurchaseItem) else raw
            kind = str(item.get("type", "")) if isinstance(item, dict) else ""
            target = str(item.get("username", "")) if isinstance(item, dict) else ""
            value = item.get("months") if kind == "premium" else item.get("amount") if isinstance(item, dict) else 0
            display = value if isinstance(value, int) and not isinstance(value, bool) else 0
            try:
                result = await self.purchase(item, payment_method=method)
                if isinstance(result, M.PreparedTransaction):
                    prepared.append(result)
                    status = "prepared"
                else:
                    sent += 1
                    status = "confirmed" if result.confirmed else "broadcast"
                results.append(M.BatchItemResult(
                    type=kind, username=target, amount=display,
                    ok=True, result=result, chunk_index=index, status=status,
                ))
            except BroadcastUncertainError as exc:
                results.append(M.BatchItemResult(
                    type=kind, username=target, amount=display,
                    ok=False, error=str(exc), chunk_index=index, status="unknown",
                ))
                for remainder_index in range(index + 1, len(items)):
                    remainder = items[remainder_index]
                    remainder = remainder.model_dump() if isinstance(remainder, M.PurchaseItem) else remainder
                    results.append(M.BatchItemResult(
                        type=str(remainder.get("type", "")) if isinstance(remainder, dict) else "",
                        username=str(remainder.get("username", "")) if isinstance(remainder, dict) else "",
                        amount=0, ok=False,
                        error="Not attempted after an unresolved broadcast.",
                        chunk_index=remainder_index,
                    ))
                break
            except Exception as exc:
                results.append(M.BatchItemResult(
                    type=kind, username=target, amount=display,
                    ok=False, error=str(exc), chunk_index=index,
                ))
        succeeded = sum(result.ok for result in results)
        model = M.NoKycBatchResult if self.wallet_auth else M.BatchResult
        return model(
            total=len(items), succeeded=succeeded, failed=len(items) - succeeded,
            chunks_sent=sent, items=results, prepared_transactions=prepared,
        )

    async def giveaway_stars(
        self, channel: str, winners: int, amount: int,
        payment_method: str = "gram",
    ) -> Any:
        """Run an original-limit total-package Stars giveaway."""
        stars_giveaway(amount, winners)
        return await self._giveaway(
            "giveaway_stars", channel, winners, amount, payment_method
        )

    async def giveaway_premium(
        self, channel: str, winners: int, months: int = 3,
        payment_method: str = "gram",
    ) -> Any:
        """Run a Premium giveaway."""
        integer(winners, 1, 24_000, ConfigurationError.INVALID_WINNERS_PREMIUM)
        validate_months(months)
        return await self._giveaway(
            "giveaway_premium", channel, winners, months, payment_method
        )

    async def _giveaway(
        self, kind: str, channel: str, winners: int, amount: int, payment_method: str,
    ) -> Any:
        """Normalize giveaway receipts."""
        channel = normalize_recipient(channel)
        result = await self._purchase_flow(
            kind, channel, amount, winners=winners, payment_method=payment_method
        )
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        model = M.GiveawayStarsResult if kind == "giveaway_stars" else M.GiveawayPremiumResult
        return model(
            transaction_id=receipt.tx_hash, channel=channel,
            winners=winners, amount=amount,
            payment_method=normalize_payment_method(payment_method),
            confirmed=receipt.confirmed, fee_nanoton=receipt.fee_nanoton,
            req_id=req_id, confirmation_error=receipt.confirmation_error,
        )

    async def recharge_ads(self, account_id: str, amount: int) -> Any:
        """Recharge a specified Ads account."""
        integer(amount, 1, C.GRAM_TOPUP_MAX, ConfigurationError.INVALID_GRAM_AMOUNT)
        result = await self._purchase_flow("ads_recharge", account_id, amount)
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        return M.AdsRechargeResult(
            transaction_id=receipt.tx_hash, account_id=account_id, amount=amount,
            req_id=req_id, confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
            confirmation_error=receipt.confirmation_error,
        )

    async def recharge_gateway(self, account_id: str, credits: int) -> Any:
        """Recharge a Gateway account."""
        integer(credits, 1, 10 ** 12, ConfigurationError.INVALID_CREDITS_AMOUNT)
        result = await self._purchase_flow("gateway", account_id, credits)
        if not isinstance(result, tuple):
            return result
        receipt, req_id = result
        return M.GatewayRechargeResult(
            transaction_id=receipt.tx_hash, account_id=account_id, credits=credits,
            req_id=req_id, confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
            confirmation_error=receipt.confirmation_error,
        )

    async def get_gateway_price(self, account_id: str, credits: int) -> M.GatewayPriceInfo:
        """Quote Gateway credits."""
        integer(credits, 1, 10 ** 12, ConfigurationError.INVALID_CREDITS_AMOUNT)
        result = await self._api(
            "updateGatewayPrices", {"account": account_id, "credits": credits}, C.GATEWAY_PAGE
        )
        if result.get("price") is None:
            raise ParseError("Gateway quote did not contain a price.")
        return M.GatewayPriceInfo(
            credits=credits, gram_price=str(result["price"]),
            usd_price=str(result["usd_price"]) if result.get("usd_price") is not None else None,
        )

    async def get_wallet(self) -> M.WalletInfo:
        """Read the configured payer wallet, never the shared authentication wallet."""
        return await fetch_wallet_info(self)

    async def get_stars_price(self, quantity: int) -> M.StarsPrice:
        """Quote a Stars quantity."""
        integer(quantity, C.STARS_PURCHASE_MIN, C.STARS_PURCHASE_MAX, ConfigurationError.INVALID_STARS_AMOUNT)
        result = await self._api(
            "updateStarsPrices", {"stars": "0", "quantity": quantity}, C.STARS_BUY_PAGE
        )
        native, usd = H.parse_stars_price_from_html(str(result.get("cur_price", "")))
        if native is None:
            raise ParseError("Stars quote did not contain a native price.")
        return M.StarsPrice(stars=quantity, gram_price=native, usd_price=usd or "0")

    async def get_stars_prices(self) -> M.StarsPrices:
        """Read Stars packages."""
        data = await self._page(C.STARS_BUY_PAGE)
        return M.StarsPrices(
            packages=H.parse_stars_packages(data.get("h", "")),
            gram_rate=data.get("s", {}).get("tonRate", 0),
        )

    async def get_premium_prices(self) -> M.PremiumPrices:
        """Read Premium duration prices."""
        data = await self._page(C.PREMIUM_GIFT_PAGE)
        return M.PremiumPrices(
            options=H.parse_premium_options(data.get("h", "")),
            gram_rate=data.get("s", {}).get("tonRate", 0),
        )

    async def _search(
        self, kind: str, page: str, query: str,
        sort: str | None, filter: str | None, **extra: Any,
    ) -> tuple[dict[str, Any], str]:
        """Fetch a listing including partial body and footer responses."""
        data: dict[str, Any] = {"type": kind, "query": query}
        if sort is not None:
            if sort not in {"price", "price_desc", "price_asc", "listed", "ending"}:
                raise ConfigurationError("Invalid auction sort.")
            data["sort"] = sort
        if filter is not None:
            if filter not in {"", "auction", "sale", "sold"}:
                raise ConfigurationError("Invalid auction filter.")
            data["filter"] = filter
        data.update({key: value for key, value in extra.items() if value is not None})
        result = await self._api("searchAuctions", data, page)
        html = result.get("html")
        if html is None:
            html = str(result.get("body") or "") + str(result.get("foot") or "")
        return result, str(html)

    async def search_usernames(
        self, query: str = "", sort: str | None = None,
        filter: str | None = None, offset_id: str | None = None,
    ) -> M.UsernamesResult:
        """Search username listings."""
        raw, html = await self._search(
            "usernames", C.FRAGMENT_BASE_URL, query, sort, filter, offset_id=offset_id
        )
        cursor = raw.get("next_offset_id") or H.parse_listing_offset(html)
        return M.UsernamesResult(
            items=H.parse_auction_rows(html),
            next_offset_id=str(cursor) if cursor is not None else None,
        )

    async def search_numbers(
        self, query: str = "", sort: str | None = None,
        filter: str | None = None, offset_id: str | None = None,
    ) -> M.NumbersResult:
        """Search anonymous-number listings."""
        raw, html = await self._search(
            "numbers", C.NUMBERS_PAGE, query, sort, filter, offset_id=offset_id
        )
        cursor = raw.get("next_offset_id") or H.parse_listing_offset(html)
        return M.NumbersResult(
            items=H.parse_auction_rows(html),
            next_offset_id=str(cursor) if cursor is not None else None,
        )

    async def search_gifts(
        self, query: str = "", collection: str | None = None,
        sort: str | None = None, filter: str | None = None,
        view: str | None = None, attr: dict[str, list[str]] | None = None,
        offset: int | None = None,
    ) -> M.GiftsResult:
        """Search gifts with JSON-encoded trait arrays."""
        extra: dict[str, Any] = {
            "collection": collection, "view": view, "offset_id": offset,
        }
        if offset is not None:
            integer(offset, 0, 2 ** 63 - 1, "Invalid gift offset.")
        for field, values in (attr or {}).items():
            name = str(field).removeprefix("attr[").removesuffix("]").strip().title()
            if name not in {"Model", "Backdrop", "Symbol"}:
                raise ConfigurationError(f"Invalid gift attribute: {field}")
            if isinstance(values, str):
                try:
                    values = json.loads(values)
                except ValueError as exc:
                    raise ConfigurationError("Gift attribute values must be JSON arrays or lists.") from exc
            if not isinstance(values, (list, tuple)) or any(not isinstance(value, str) for value in values):
                raise ConfigurationError("Gift attribute values must be arrays of strings.")
            extra[f"attr[{name}]"] = json.dumps(list(values), ensure_ascii=False)
        _, html = await self._search(
            "gifts", C.GIFTS_PAGE, query, sort, filter, **extra
        )
        items, cursor = H.parse_gift_items(html)
        return M.GiftsResult(items=items, next_offset=cursor)

    async def get_gift_filters(self, collection: str | None = None) -> M.GiftFiltersInfo:
        """Read collection and trait filters."""
        url = C.GIFTS_PAGE + (f"/{quote(collection, safe='')}" if collection else "")
        data = await self._page(url)
        collections, attributes = H.parse_gift_filters(data.get("h", ""))
        return M.GiftFiltersInfo(collections=collections, attributes=attributes)

    def _item_url(self, item_type: int, slug: str) -> str:
        """Validate item type and construct its detail URL."""
        if isinstance(item_type, bool) or item_type not in C.VALID_ITEM_TYPES:
            raise ConfigurationError(
                ConfigurationError.INVALID_ITEM_TYPE.format(item_type=item_type)
            )
        prefix = C.ITEM_TYPE_URL_PREFIX[item_type]
        slug = str(slug).strip().lstrip("@").removeprefix(f"{prefix}/")
        if not slug:
            raise ConfigurationError("Item slug is required.")
        return f"{C.FRAGMENT_BASE_URL}/{prefix}/{quote(slug, safe='')}"

    async def _item_info(self, item_type: int, slug: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
        """Read common item details."""
        data = await self._page(self._item_url(item_type, slug))
        html = str(data.get("h", ""))
        state = data.get("s", {})
        bids, bid_offset = H.parse_bid_history(html)
        owners, owner_offset = H.parse_owner_history(html)
        offers, offer_offset = H.parse_offer_history(html)
        timer = re.search(r'class="[^"]*tm-countdown-timer[^"]*"[^>]*datetime="([^"]+)"', html)
        purchased = re.search(r'Purchased on\s*<time[^>]+datetime="([^"]+)"', html)
        common = {
            "item_type": item_type,
            "status": H.parse_item_status(html),
            "gram_rate": state.get("tonRate", 0),
            "auction": H.parse_auction_info(html),
            "auction_end": timer.group(1) if timer else None,
            "owner_wallet": H.parse_sold_owner(html),
            "purchased_date": purchased.group(1) if purchased else None,
            "bid_history": bids,
            "owner_history": owners,
            "offer_history": offers,
            "bid_history_next_offset": bid_offset,
            "owner_history_next_offset": owner_offset,
            "offer_history_next_offset": offer_offset,
        }
        return common, html, state

    async def get_username_info(self, username: str) -> M.UsernameInfo:
        """Read username details."""
        common, _, state = await self._item_info(1, username)
        return M.UsernameInfo(username=state.get("username", username.lstrip("@")), **common)

    async def get_number_info(self, number: str) -> M.NumberInfo:
        """Read anonymous-number details."""
        clean = re.sub(r"[+\s-]", "", number)
        common, html, state = await self._item_info(3, clean)
        return M.NumberInfo(
            number=state.get("username", clean),
            display_number=state.get("itemTitle", f"+{clean}"),
            restricted="tm-status-restricted" in html,
            **common,
        )

    async def get_gift_info(self, slug: str) -> M.GiftInfo:
        """Read gift details."""
        common, html, state = await self._item_info(5, slug)
        image = re.search(r'src="(https://nft\.fragment\.com/gift/[^"]+)"', html)
        sticker = re.search(r'srcset="(https://nft\.fragment\.com/gift/[^"]+\.tgs)"', html)
        return M.GiftInfo(
            slug=state.get("username", slug),
            name=state.get("itemTitle", slug),
            image_url=image.group(1) if image else None,
            sticker_url=sticker.group(1) if sticker else None,
            attributes=H.parse_gift_attributes(html),
            issued=H.parse_gift_issued(html),
            **common,
        )

    async def _history_page(self, page: str, parser: Any, **query: Any) -> Any:
        """Read authenticated history."""
        data = await self._page(f"{page}?{urlencode(query)}", account=True)
        return parser(data.get("h", ""))

    async def get_stars_history(self, sort: str = "desc") -> list[M.StarsTransaction]:
        """Read account Stars history."""
        return await self._history_page(C.STARS_HISTORY_PAGE, H.parse_stars_history, sort=sort)

    async def get_premium_history(self, sort: str = "desc") -> list[M.PremiumTransaction]:
        """Read account Premium history."""
        return await self._history_page(C.PREMIUM_HISTORY_PAGE, H.parse_premium_history, sort=sort)

    async def get_topup_history(self, sort: str = "asc") -> list[M.TopupTransaction]:
        """Read account Ads top-up history."""
        return await self._history_page(C.ADS_HISTORY_PAGE, H.parse_topup_history, type="topup", sort=sort)

    async def get_profile(self) -> M.ProfileInfo:
        """Read the user-owned profile."""
        data = await self._page(C.PROFILE_PAGE, account=True)
        return H.parse_profile(str(data.get("h", "")) + str(data.get("j", "")))

    async def get_sessions(self) -> list[M.SessionInfo]:
        """List user-owned Fragment sessions."""
        data = await self._page(C.SESSIONS_PAGE, account=True)
        return H.parse_sessions(data.get("h", ""))

    async def list_sessions(self) -> list[M.SessionInfo]:
        """Alias for get_sessions."""
        return await self.get_sessions()

    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a user-owned Fragment session."""
        self._require_account("terminate_session")
        result = await self._api(
            "tonTerminateSession", {"session_id": session_id}, C.SESSIONS_PAGE
        )
        return bool(result.get("ok", False))

    async def get_my_bids(self, item_type: str = "usernames", sort: str = "desc") -> M.MyBidsResult:
        """Read user-owned bids."""
        self._require_account("get_my_bids")
        if item_type not in {"usernames", "numbers", "gifts"}:
            raise ConfigurationError("Invalid asset category.")
        data = await self._page(
            f"{C.MY_BIDS_PAGE}?{urlencode({'type': item_type, 'sort': sort})}",
            account=True,
        )
        items, total = H.parse_my_bids(data.get("h", ""), item_type)
        return M.MyBidsResult(
            items=items, total_count=total,
            gram_rate=data.get("s", {}).get("tonRate", 0),
        )

    async def get_my_assets(self, item_type: str = "usernames") -> M.MyAssetsResult:
        """Read user-owned assets."""
        self._require_account("get_my_assets")
        pages = {"usernames": C.MY_USERNAMES_PAGE, "numbers": C.MY_NUMBERS_PAGE, "gifts": C.MY_GIFTS_PAGE}
        if item_type not in pages:
            raise ConfigurationError("Invalid asset category.")
        data = await self._page(pages[item_type], account=True)
        items, total = H.parse_my_assets(data.get("h", ""), item_type)
        return M.MyAssetsResult(
            items=items, total_count=total,
            gram_rate=data.get("s", {}).get("tonRate", 0),
        )

    async def _orders(
        self, method: str, item_type: int, username: str, offset_id: str,
    ) -> dict[str, Any]:
        """Load additional public item history."""
        return await self._api(
            method,
            {"type": item_type, "username": username, "offset_id": offset_id},
            self._item_url(item_type, username),
        )

    async def get_orders_history(self, item_type: int, username: str, offset_id: str) -> dict[str, Any]:
        """Load additional bid history."""
        return await self._orders("getOrdersHistory", item_type, username, offset_id)

    async def get_owners_history(self, item_type: int, username: str, offset_id: str) -> dict[str, Any]:
        """Load additional ownership history."""
        return await self._orders("getOwnersHistory", item_type, username, offset_id)

    async def get_offers_history(self, item_type: int, username: str, offset_id: str) -> dict[str, Any]:
        """Load additional offers."""
        return await self._orders("getOffersHistory", item_type, username, offset_id)

    async def _account_transaction(
        self, method: str, data: dict[str, Any], page: str,
        payment_nanoton: int = 0,
    ) -> tuple[M.TransactionResult, dict[str, Any]]:
        """Broadcast an account-scoped transaction with an explicit native principal."""
        self._require_account(method)
        self._require_ton_token()
        self._require_wallet()
        account = await build_account_info(self)
        transaction = await self._api(
            method,
            {
                **data,
                "account": json.dumps(account),
                "device": C.DEVICE_FINGERPRINT,
                "transaction": 1,
            },
            page,
        )
        receipt = await execute_transaction(
            self, transaction, payment_nanoton=payment_nanoton
        )
        req_id = str((transaction.get("confirm_params") or {}).get("id", ""))
        if transaction.get("confirm_method"):
            receipt = await self._confirm(
                transaction, receipt, account, req_id, page, None
            )
        return receipt, transaction

    async def place_bid(self, item_type: int, slug: str, bid: int) -> M.BidResult:
        """Place a native-TON bid with its separate 0.5 percent fee."""
        integer(bid, 1, 10 ** 12, ConfigurationError.INVALID_BID_AMOUNT)
        page = self._item_url(item_type, slug)
        receipt, transaction = await self._account_transaction(
            "getBidLink", {"type": item_type, "username": slug, "bid": bid},
            page, bid * C.NANO_PER_TON,
        )
        return M.BidResult(
            transaction_id=receipt.tx_hash, item_type=item_type, slug=slug, bid=bid,
            confirm_method=transaction.get("confirm_method"),
            confirm_id=(transaction.get("confirm_params") or {}).get("id"),
            confirmed=receipt.confirmed, fee_nanoton=receipt.fee_nanoton,
        )

    async def make_offer(self, item_type: int, slug: str, amount: int) -> M.OfferResult:
        """Make a native-TON offer."""
        self._require_account("make_offer")
        integer(amount, 1, 10 ** 12, ConfigurationError.INVALID_OFFER_AMOUNT)
        page = self._item_url(item_type, slug)
        result = await self._api(
            "initOfferRequest", {"type": item_type, "username": slug}, page
        )
        req_id = str(result.get("req_id") or "")
        if not req_id:
            raise FragmentAPIError("Offer request ID was not returned.")
        receipt, _ = await self._account_transaction(
            "getOfferLink", {"id": req_id, "amount": amount},
            page, amount * C.NANO_PER_TON,
        )
        return M.OfferResult(
            transaction_id=receipt.tx_hash, item_type=item_type, slug=slug,
            amount=amount, req_id=req_id, confirmed=receipt.confirmed,
            fee_nanoton=receipt.fee_nanoton,
        )

    async def cancel_auction(self, item_type: int, slug: str) -> M.TransactionResult:
        """Cancel an auction; no percentage fee applies to gas-only operations."""
        result, _ = await self._account_transaction(
            "getCancelAuctionLink",
            {"type": item_type, "username": slug},
            self._item_url(item_type, slug),
        )
        return result

    async def _subscribe(self, item_type: int, slug: str, subscribed: bool) -> M.SubscriptionResult:
        """Change user-owned notification preferences."""
        self._require_account("subscribe" if subscribed else "unsubscribe")
        result = await self._api(
            "subscribe" if subscribed else "unsubscribe",
            {"type": item_type, "username": slug},
            self._item_url(item_type, slug),
        )
        return M.SubscriptionResult(
            ok=bool(result.get("ok", True)), subscribed=subscribed,
            item_type=item_type, slug=slug,
        )

    async def subscribe_to_item(self, item_type: int, slug: str) -> M.SubscriptionResult:
        """Subscribe to auction updates."""
        return await self._subscribe(item_type, slug, True)

    async def unsubscribe_from_item(self, item_type: int, slug: str) -> M.SubscriptionResult:
        """Unsubscribe from auction updates."""
        return await self._subscribe(item_type, slug, False)

    async def get_assign_accounts(self, item_type: int, slug: str) -> M.AssignAccountsResult:
        """Read available user-owned assignment destinations."""
        data = await self._page(self._item_url(item_type, slug), account=True)
        accounts, disable = H.parse_assign_accounts(data.get("h", ""))
        return M.AssignAccountsResult(accounts=accounts, can_disable=disable)

    async def assign_to_telegram(
        self, item_type: int, slug: str, assign_to: str | None = None,
        wait_for_bot_payment: bool = True,
    ) -> M.AssignResult:
        """Assign an asset and optionally pay an explicitly quoted assignment charge."""
        self._require_account("assign_to_telegram")
        page = self._item_url(item_type, slug)
        data: dict[str, Any] = {"type": item_type, "username": slug}
        if assign_to is not None:
            data["assign_to"] = assign_to
        result = await self._api("assignToTgAccount", data, page)
        if result.get("need_pay") and wait_for_bot_payment and self.has_wallet:
            req_id = str(result.get("req_id") or "")
            if not req_id:
                raise FragmentAPIError("Assignment payment request ID was missing.")
            principal = decimal_units(result.get("amount"), 9)
            await self._account_transaction(
                "getBotUsernameLink", {"id": req_id}, page, principal
            )
            result = await self._api("assignToTgAccount", data, page)
        return M.AssignResult(
            ok=bool(result.get("ok", result.get("need_pay", False))),
            message=result.get("msg"), need_pay=bool(result.get("need_pay")),
            req_id=result.get("req_id"),
            amount=str(result["amount"]) if result.get("amount") is not None else None,
            assign_name=result.get("assign_name"),
        )

    async def start_auction(
        self, item_type: int, slug: str, min_amount: int, max_amount: int = 0,
    ) -> M.StartAuctionResult:
        """Create a listing without charging a fee on the asking price."""
        self._require_account("start_auction")
        integer(min_amount, 1, 10 ** 12, "Invalid minimum auction price.")
        integer(max_amount, 0, 10 ** 12, "Invalid maximum auction price.")
        if max_amount and max_amount < min_amount:
            raise ConfigurationError("Maximum price must not be below minimum price.")
        page = self._item_url(item_type, slug)
        allowed = await self._api(
            "canSellItem",
            {"type": item_type, "username": slug, "auction": "true" if not max_amount else "false"},
            page,
        )
        if not allowed.get("ok"):
            return M.StartAuctionResult(ok=False)
        receipt, transaction = await self._account_transaction(
            "getStartAuctionLink",
            {"type": item_type, "username": slug, "min_amount": min_amount, "max_amount": max_amount},
            page,
        )
        return M.StartAuctionResult(
            ok=True, req_id=(transaction.get("confirm_params") or {}).get("id"),
            transaction_id=receipt.tx_hash, confirmed=receipt.confirmed,
        )

    async def sell_asset(self, item_type: int, slug: str, price: int) -> M.StartAuctionResult:
        """Create a fixed-price listing."""
        return await self.start_auction(item_type, slug, price, price)

    async def search_nft_transfer_recipient(self, query: str) -> M.NftTransferRecipient | None:
        """Resolve a destination for a user-owned NFT."""
        self._require_account("search_nft_transfer_recipient")
        result = await self._recipient(
            "searchNftTransferRecipient", query, C.FRAGMENT_BASE_URL
        )
        return M.NftTransferRecipient(**result.model_dump()) if result else None

    async def init_nft_transfer(self, slug: str, recipient: str) -> M.NftTransferRequest:
        """Initialize an NFT transfer."""
        self._require_account("init_nft_transfer")
        page = f"{self._item_url(5, slug)}/transfer"
        result = await self._api(
            "initNftTransferRequest", {"slug": slug, "recipient": recipient}, page
        )
        if not result.get("req_id"):
            raise FragmentAPIError("NFT transfer request ID was not returned.")
        return M.NftTransferRequest(**result)

    async def transfer_nft(self, req_id: str, show_sender: bool = True) -> M.TransactionResult:
        """Broadcast a gas-only NFT transfer."""
        result, _ = await self._account_transaction(
            "getNftTransferLink", {"id": req_id, "show_sender": int(show_sender)},
            C.FRAGMENT_BASE_URL,
        )
        return result

    async def get_login_code(self, number: str) -> M.LoginCodeResult:
        """Read a login code only from a user-owned number session."""
        self._require_account("get_login_code")
        result = await self._api(
            "updateLoginCodes", {"number": number.lstrip("+"), "lt": "0", "from_app": "1"},
            C.NUMBERS_PAGE,
        )
        code, count = H.parse_login_code(result.get("html", ""))
        return M.LoginCodeResult(number=number, code=code, active_sessions=count)

    async def toggle_login_codes(self, number: str, can_receive: bool) -> None:
        """Change user-owned number login-code delivery."""
        self._require_account("toggle_login_codes")
        if not isinstance(can_receive, bool):
            raise ConfigurationError("can_receive must be a boolean.")
        await self._api(
            "toggleLoginCodes", {"number": number.lstrip("+"), "can_receive": int(can_receive)},
            C.NUMBERS_PAGE,
        )

    async def terminate_sessions(self, number: str) -> M.TerminateSessionsResult:
        """Terminate Telegram sessions associated with a user-owned number."""
        self._require_account("terminate_sessions")
        data = {"number": number.lstrip("+")}
        first = await self._api("terminatePhoneSessions", data, C.NUMBERS_PAGE)
        token = first.get("terminate_hash")
        if not token:
            raise AnonymousNumberError(
                AnonymousNumberError.NOT_OWNED.format(number=number)
            )
        result = await self._api(
            "terminatePhoneSessions", {**data, "terminate_hash": token}, C.NUMBERS_PAGE
        )
        return M.TerminateSessionsResult(number=number, message=result.get("msg"))

    async def get_nft_withdrawal_state(self, transaction: str) -> dict[str, Any]:
        """Read user-owned NFT withdrawal state."""
        return await self._page(
            f"{C.NFT_WITHDRAW_PAGE}?{urlencode({'transaction': transaction})}",
            account=True,
        )

    async def get_stars_withdrawal_state(self, transaction: str) -> M.StarsWithdrawalState:
        """Read user-owned Stars withdrawal state."""
        data = await self._page(
            f"{C.STARS_WITHDRAW_PAGE}?{urlencode({'transaction': transaction})}",
            account=True,
        )
        state = data.get("s", {})
        if not state.get("transaction") or not state.get("withdrawalData"):
            raise ParseError("Stars withdrawal state was missing or expired.")
        return M.StarsWithdrawalState(
            transaction=str(state["transaction"]),
            withdrawal_data=str(state["withdrawalData"]),
        )

    async def _withdraw(
        self, method: str, transaction: str,
        confirm_hash: str | None = None, **extra: Any,
    ) -> dict[str, Any]:
        """Initialize or confirm a user-owned withdrawal to the payer account."""
        self._require_account(method)
        account = await build_account_info(self)
        data = {
            "transaction": transaction,
            "wallet_address": account["address"],
            **extra,
        }
        if confirm_hash is not None:
            data["confirm_hash"] = confirm_hash
        return await self.call(method, data)

    async def init_nft_withdrawal(self, transaction: str, keep_gift: bool = False) -> M.NftWithdrawalInitResult:
        """Initialize an NFT withdrawal."""
        result = await self._withdraw(
            "initNftWithdrawalRequest", transaction, keep_gift=int(keep_gift)
        )
        return M.NftWithdrawalInitResult(**{"ok": False, **result})

    async def confirm_nft_withdrawal(
        self, transaction: str, confirm_hash: str, keep_gift: bool = False,
    ) -> M.NftWithdrawalConfirmResult:
        """Confirm an NFT withdrawal."""
        result = await self._withdraw(
            "initNftWithdrawalRequest", transaction, confirm_hash, keep_gift=int(keep_gift)
        )
        return M.NftWithdrawalConfirmResult(**{"ok": False, **result})

    async def init_stars_withdrawal(
        self, transaction: str, withdrawal_data: str,
    ) -> M.StarsWithdrawalInitResult:
        """Initialize a Stars withdrawal."""
        result = await self._withdraw(
            "initStarsRevenueWithdrawalRequest", transaction,
            withdrawal_data=withdrawal_data,
        )
        return M.StarsWithdrawalInitResult(**{"ok": False, **result})

    async def confirm_stars_withdrawal(
        self, transaction: str, withdrawal_data: str, confirm_hash: str,
    ) -> M.StarsWithdrawalConfirmResult:
        """Confirm a Stars withdrawal."""
        result = await self._withdraw(
            "initStarsRevenueWithdrawalRequest", transaction, confirm_hash,
            withdrawal_data=withdrawal_data,
        )
        return M.StarsWithdrawalConfirmResult(**{"ok": False, **result})

    async def init_ads_withdrawal(self, transaction_id: str) -> M.AdsWithdrawalInitResult:
        """Initialize an Ads revenue withdrawal."""
        result = await self._withdraw("initAdsRevenueWithdrawalRequest", transaction_id)
        return M.AdsWithdrawalInitResult(**{"ok": False, **result})

    async def confirm_ads_withdrawal(
        self, transaction_id: str, confirm_hash: str,
    ) -> M.AdsWithdrawalConfirmResult:
        """Confirm an Ads revenue withdrawal."""
        result = await self._withdraw(
            "initAdsRevenueWithdrawalRequest", transaction_id, confirm_hash
        )
        return M.AdsWithdrawalConfirmResult(**{"ok": False, **result})

    async def confirm_request(
        self, req_id: str, boc: str, referer: str = "stars/buy",
    ) -> dict[str, Any]:
        """Report an externally signed transaction without claiming fulfillment."""
        return await self._api(
            "confirmReq", {"id": req_id, "boc": boc},
            f"{C.FRAGMENT_BASE_URL}/{referer.lstrip('/')}",
        )