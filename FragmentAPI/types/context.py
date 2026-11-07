"""Structural contract used by client mixins and wallet operations."""

from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Protocol
from curl_cffi import requests
from ton_core import MnemonicType
from FragmentAPI.types import constants as C
from FragmentAPI.storage.payments import PaymentStorage
from FragmentAPI.types import models as M
from FragmentAPI.utils.http import FragmentTransport


class ClientContext(Protocol):
    wallet_version: str
    mnemonic_type: MnemonicType
    seed: str | None
    api_key: str | None
    api_provider: str
    sender_account: dict[str, Any] | None
    cookies: dict[str, str]
    timeout: float
    confirmation_timeout: float
    gas_reserve_nanoton: int
    payment_storage: PaymentStorage
    wallet_lock_factory: Callable[[str], AbstractAsyncContextManager[None]]
    _flow_lock: asyncio.Lock
    _wallet_lock: asyncio.Lock
    _session: requests.AsyncSession | None
    _withdrawal_submissions: set[str]

    async def _api(
        self,
        method: str,
        data: dict[str, Any] | None = None,
        page_url: str = C.FRAGMENT_BASE_URL,
    ) -> dict[str, Any]: ...
    async def _batch_purchase(
        self, items: list[dict[str, Any] | M.PurchaseItem], payment_method: str = "ton"
    ) -> M.BatchResult: ...
    async def _confirm(
        self,
        transaction: dict[str, Any],
        receipt: M.TransactionResult,
        account: dict[str, Any],
        req_id: str,
        page_url: str,
        state_method: str | None,
    ) -> M.TransactionResult: ...
    async def _ensure_auth(self) -> None: ...
    def _get_transport(self) -> FragmentTransport: ...
    async def _giveaway(
        self, kind: str, channel: str, winners: int, amount: int, payment_method: str
    ) -> (
        M.GiveawayStarsResult
        | M.GiveawayPremiumResult
        | M.PreparedTransaction
        | M.ExternalPaymentResult
    ): ...
    async def _prepare_purchase(
        self,
        kind: str,
        target: str,
        amount: int,
        *,
        payment_method: str = "ton",
        show_sender: bool = True,
        winners: int | None = None,
    ) -> (
        tuple[M.PreparedTransaction, M.PaymentConfirmation] | M.ExternalPaymentResult
    ): ...
    async def _purchase_flow(
        self,
        kind: str,
        target: str,
        amount: int,
        *,
        payment_method: str = "ton",
        show_sender: bool = True,
        winners: int | None = None,
    ) -> (
        tuple[M.TransactionResult, str]
        | M.PreparedTransaction
        | M.ExternalPaymentResult
    ): ...
    async def _recipient(
        self, method: str, query: str, page_url: str, **extra: Any
    ) -> M.RecipientInfo | None: ...
    def _require_account(self, operation: str) -> None: ...
    def _require_ton_token(self) -> None: ...
    def _require_wallet(self) -> None: ...
    async def _save_confirmation(
        self, req_id: str, receipt: M.TransactionResult
    ) -> None: ...
    async def _single_purchase(
        self,
        kind: str,
        username: str,
        amount: int,
        show_sender: bool,
        payment_method: str,
    ) -> M.PurchaseResult | M.PreparedTransaction | M.ExternalPaymentResult: ...
    async def _withdraw(
        self,
        method: str,
        transaction: str,
        confirm_hash: str | None = None,
        *,
        page_url: str = C.FRAGMENT_BASE_URL,
        **extra: Any,
    ) -> dict[str, Any]: ...
    @property
    def has_wallet(self) -> bool: ...
    async def inspect_withdrawal(self, url: str) -> M.WithdrawalInfo: ...
