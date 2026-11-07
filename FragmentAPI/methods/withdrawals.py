"""Revenue withdrawal links with read-only inspection and explicit confirmation."""
from __future__ import annotations

from FragmentAPI.types.context import ClientContext

import hashlib
from typing import Literal
from urllib.parse import parse_qs, urlencode, urlsplit

from selectolax.lexbor import LexborHTMLParser

from FragmentAPI.exceptions import ConfigurationError, FragmentAPIError, KycRequiredError, ParseError
from FragmentAPI.types.models import WithdrawalInfo, WithdrawalRequest, WithdrawalConfirmResult
from FragmentAPI.utils.auth import embedded_object
from FragmentAPI.utils.http import validate_page_url, raise_api_error
from FragmentAPI.utils.wallet import build_account_info

_PATHS: dict[str, tuple[Literal["stars", "ads"], str]] = {"/stars/withdraw": ("stars", "initStarsRevenueWithdrawalRequest"),
          "/ads/withdraw": ("ads", "initAdsRevenueWithdrawalRequest")}


def parse_withdrawal_url(url: str) -> tuple[Literal["stars", "ads"], str, str]:
    """Validate before sending cookies; canonicalize to the supported route/token."""
    try:
        if not isinstance(url, str) or any(ord(c) < 32 for c in url):
            raise ValueError
        validate_page_url(url)
        parsed = urlsplit(url)
        values = parse_qs(parsed.query, keep_blank_values=True).get("transaction", [])
        if parsed.path not in _PATHS or parsed.fragment or len(values) != 1 or not values[0].strip():
            raise ValueError
        token = values[0]
        if any(ord(c) < 32 for c in token):
            raise ValueError
    except (ValueError, TypeError, FragmentAPIError) as exc:
        raise ConfigurationError("Use an HTTPS fragment.com/stars/withdraw or /ads/withdraw URL with one transaction parameter.") from exc
    canonical = "https://fragment.com" + parsed.path + "?" + urlencode({"transaction": token})
    return _PATHS[parsed.path][0], token, canonical


class WithdrawalMixin:
    async def inspect_withdrawal(self: ClientContext, url: str) -> WithdrawalInfo:
        """Read a revenue link without initializing or confirming a withdrawal."""
        kind, transaction, canonical = parse_withdrawal_url(url)
        self._require_account("inspect_withdrawal")
        await self._ensure_auth()
        html = await self._get_transport().get_text(canonical)
        initial = embedded_object(html, "ajInit(")
        state = initial.get("state", {})
        if not isinstance(state, dict) or state.get("transaction") != transaction:
            raise ParseError("Withdrawal link is missing, expired, or belongs to a different transaction.")
        tree = LexborHTMLParser(html)
        def field(name: str) -> str | None:
            node = tree.css_first(f'.js-withdraw-form input[name="{name}"]')
            return node.attributes.get("value") or None if node is not None else None
        opaque = state.get("withdrawalData") or field("withdrawal_data")
        if kind == "stars" and not state.get("need_verify") and (not isinstance(opaque, str) or not opaque):
            raise ParseError("Stars withdrawal link does not contain valid withdrawal data.")
        amount = field("amount")
        currency = field("currency")
        return WithdrawalInfo(
            kind=kind, url=canonical, transaction=transaction, withdrawal_data=opaque,
            destination=field("wallet_address"), amount=amount, currency=currency,
            source=field("source"), mode=str(state.get("mode", "unknown")),
            kyc_required=bool(state["need_verify"]) if "need_verify" in state else None,
        )

    async def prepare_withdrawal(self: ClientContext, url: str) -> WithdrawalRequest:
        """Initialize with Fragment to request a challenge; this is a state-changing call.

        Some server responses may have no challenge. Such results are returned
        for inspection and must not be automatically repeated or confirmed.
        """
        async with self._flow_lock:
            info = await self.inspect_withdrawal(url)
            if info.kyc_required:
                raise KycRequiredError("Complete KYC on Fragment before withdrawing monetization rewards.")
            if info.mode in {"processing", "done"}:
                raise ConfigurationError("This withdrawal is already processing or done; inspect the original status.")
            account = await build_account_info(self)
            method = _PATHS[urlsplit(info.url).path][1]
            extra = {"withdrawal_data": info.withdrawal_data} if info.kind == "stars" else {}
            result = await self._withdraw(method, info.transaction, page_url=info.url, **extra)
            raise_api_error(result)
            token = result.get("confirm_hash")
            message = result.get("confirm_message")
            if token is not None and (not isinstance(token, str) or not token):
                raise ParseError("Fragment returned an invalid withdrawal challenge.")
            return WithdrawalRequest(
                info=info, destination=account["address"],
                confirm_message=message, confirm_button=result.get("confirm_button"),
                confirm_hash=token, confirmation_required=bool(token and message), server_response=result,
            )

    async def confirm_withdrawal(self: ClientContext, request: WithdrawalRequest) -> WithdrawalConfirmResult:
        """Submit one reviewed challenge; uncertain submissions are never auto-replayed."""
        if not isinstance(request, WithdrawalRequest) or not request.confirmation_required or not request.confirm_hash:
            raise ConfigurationError("A reviewed WithdrawalRequest with a server confirmation challenge is required.")
        kind, transaction, canonical = parse_withdrawal_url(request.info.url)
        if kind != request.info.kind or transaction != request.info.transaction or canonical != request.info.url:
            raise ConfigurationError("Withdrawal request does not match its source link.")
        if kind == "stars" and not request.info.withdrawal_data:
            raise ConfigurationError("Stars withdrawal data is missing.")
        self._require_account("confirm_withdrawal")
        async with self._flow_lock:
            account = await build_account_info(self)
            if account["address"] != request.destination:
                raise ConfigurationError("Withdrawal destination changed after preparation.")
            key = hashlib.sha256((transaction + "\0" + request.confirm_hash).encode()).hexdigest()
            if key in self._withdrawal_submissions:
                raise ConfigurationError("This withdrawal challenge was already submitted; inspect its status before retrying.")
            self._withdrawal_submissions.add(key)
            method = _PATHS[urlsplit(canonical).path][1]
            extra = {"withdrawal_data": request.info.withdrawal_data} if kind == "stars" else {}
            result = await self._withdraw(method, transaction, request.confirm_hash, page_url=canonical, **extra)
            raise_api_error(result)
            return WithdrawalConfirmResult(**{"ok": False, **result})
