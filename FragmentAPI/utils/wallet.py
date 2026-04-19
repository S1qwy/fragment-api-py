"""
TON wallet utilities for Fragment API - both sync and async
"""

from __future__ import annotations

import asyncio
import base64
import ssl
from typing import TYPE_CHECKING, Any

from ton_core import NetworkGlobalID
from tonutils.clients import TonapiClient
from tonutils.exceptions import ProviderResponseError

from FragmentAPI.exceptions import TransactionError, WalletError
from FragmentAPI.types.constants import (
    MIN_TON_BALANCE,
    TONAPI_PROXY_BASE,
    WALLET_CLASSES,
)
from FragmentAPI.types.results import WalletInfo
from FragmentAPI.utils.decoder import decode_boc_comment

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient
    from FragmentAPI.async_client import AsyncFragmentClient


def _get_tonapi_kwargs(api_key: str) -> dict[str, Any]:
    """Build kwargs for TonapiClient using our proxy.

    Args:
        api_key: API key for tonapi proxy.

    Returns:
        Dict with network, api_key, and base_url.
    """
    return {
        "network": NetworkGlobalID.MAINNET,
        "api_key": api_key,
        "base_url": TONAPI_PROXY_BASE,
    }


async def _run_transaction(
    seed: str,
    api_key: str,
    wallet_version: str,
    transaction_data: dict[str, Any],
) -> str:
    """Core async logic for signing and broadcasting a transaction.

    Args:
        seed: Wallet mnemonic phrase.
        api_key: TonAPI proxy key.
        wallet_version: Wallet version string.
        transaction_data: Raw transaction dict from Fragment API.

    Returns:
        Normalized transaction hash string.

    Raises:
        TransactionError: If payload is invalid or broadcast fails.
        WalletError: If balance is too low.
    """
    if (
        "transaction" not in transaction_data
        or "messages" not in transaction_data["transaction"]
    ):
        raise TransactionError(TransactionError.INVALID_PAYLOAD)

    message = transaction_data["transaction"]["messages"][0]
    amount_ton = int(message["amount"]) / 1_000_000_000

    async with TonapiClient(**_get_tonapi_kwargs(api_key)) as ton:
        wallet_cls = WALLET_CLASSES[wallet_version]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=seed)

        try:
            await wallet.refresh()
            balance_ton = wallet.balance / 1_000_000_000
            required = amount_ton + MIN_TON_BALANCE
            if balance_ton < required:
                raise WalletError(
                    WalletError.LOW_BALANCE.format(
                        balance=balance_ton,
                        required=required,
                        gas=MIN_TON_BALANCE,
                    )
                )
        except WalletError:
            raise
        except Exception as exc:
            raise WalletError(
                WalletError.BALANCE_FAILED.format(exc=exc)
            ) from exc

        try:
            payload = decode_boc_comment(message["payload"])

            for attempt in range(3):
                try:
                    result = await wallet.transfer(
                        destination=message["address"],
                        amount=int(message["amount"]),
                        body=payload,
                    )
                    return result.normalized_hash
                except ProviderResponseError as exc:
                    if exc.code == 429 and attempt == 0:
                        await asyncio.sleep(1)
                        continue
                    if exc.code == 406 and "seqno" in str(exc).lower():
                        if attempt < 2:
                            await asyncio.sleep(2)
                            continue
                        raise TransactionError(
                            TransactionError.DUPLICATE_SEQNO
                        ) from exc
                    raise
        except (WalletError, TransactionError):
            raise
        except Exception as exc:
            cause: BaseException | None = exc
            while cause is not None:
                if isinstance(cause, ssl.SSLError):
                    raise TransactionError(
                        TransactionError.BROADCAST_SSL_ERROR.format(exc=exc)
                    ) from exc
                cause = cause.__cause__ or cause.__context__
            raise TransactionError(
                TransactionError.BROADCAST_FAILED.format(exc=exc)
            ) from exc

    raise TransactionError(
        TransactionError.BROADCAST_FAILED.format(
            exc="transfer loop exited without result"
        )
    )


async def _get_account_info_async(
    seed: str, api_key: str, wallet_version: str
) -> dict[str, Any]:
    """Fetch wallet address, public key, and state-init (async core).

    Args:
        seed: Wallet mnemonic phrase.
        api_key: TonAPI proxy key.
        wallet_version: Wallet version string.

    Returns:
        Dict with address, publicKey, chain, walletStateInit.

    Raises:
        WalletError: If account info cannot be retrieved.
    """
    async with TonapiClient(**_get_tonapi_kwargs(api_key)) as ton:
        try:
            wallet_cls = WALLET_CLASSES[wallet_version]
            wallet, pub_key, _, _ = wallet_cls.from_mnemonic(
                client=ton, mnemonic=seed
            )
            boc = wallet.state_init.serialize().to_boc()
            return {
                "address": wallet.address.to_str(False, False),
                "publicKey": pub_key.as_hex,
                "chain": "-239",
                "walletStateInit": base64.b64encode(boc).decode(),
            }
        except Exception as exc:
            raise WalletError(
                WalletError.ACCOUNT_INFO_FAILED.format(exc=exc)
            ) from exc


async def _get_wallet_info_async(
    seed: str, api_key: str, wallet_version: str
) -> WalletInfo:
    """Fetch wallet address, state, and balance (async core).

    Args:
        seed: Wallet mnemonic phrase.
        api_key: TonAPI proxy key.
        wallet_version: Wallet version string.

    Returns:
        WalletInfo with address, state, and balance.

    Raises:
        WalletError: If wallet state cannot be fetched.
    """
    async with TonapiClient(**_get_tonapi_kwargs(api_key)) as ton:
        try:
            wallet_cls = WALLET_CLASSES[wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(
                client=ton, mnemonic=seed
            )
            await wallet.refresh()
            return WalletInfo(
                address=wallet.address.to_str(
                    is_user_friendly=True, is_bounceable=False
                ),
                state=wallet.state.value,
                balance=round(wallet.balance / 1_000_000_000, 4),
            )
        except Exception as exc:
            raise WalletError(
                WalletError.WALLET_INFO_FAILED.format(exc=exc)
            ) from exc


def _run_async(coro):
    """Run an async coroutine synchronously.

    Creates a new event loop, runs the coroutine, and cleans up.

    Args:
        coro: Coroutine to execute.

    Returns:
        Result of the coroutine.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def execute_transaction(
    client: "AsyncFragmentClient",
    transaction_data: dict[str, Any],
) -> str:
    """Sign and broadcast a Fragment transaction (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.
        transaction_data: Raw transaction dict from Fragment API.

    Returns:
        Normalized transaction hash string.
    """
    return await _run_transaction(
        client.seed, client.api_key, client.wallet_version, transaction_data
    )


def execute_transaction_sync(
    client: "FragmentClient",
    transaction_data: dict[str, Any],
) -> str:
    """Sign and broadcast a Fragment transaction (sync).

    Args:
        client: Authenticated FragmentClient instance.
        transaction_data: Raw transaction dict from Fragment API.

    Returns:
        Normalized transaction hash string.
    """
    return _run_async(
        _run_transaction(
            client.seed,
            client.api_key,
            client.wallet_version,
            transaction_data,
        )
    )


async def build_account_info(
    client: "AsyncFragmentClient",
) -> dict[str, Any]:
    """Build account info for Fragment API requests (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.

    Returns:
        Dict with wallet address, publicKey, chain, walletStateInit.
    """
    return await _get_account_info_async(
        client.seed, client.api_key, client.wallet_version
    )


def build_account_info_sync(
    client: "FragmentClient",
) -> dict[str, Any]:
    """Build account info for Fragment API requests (sync).

    Args:
        client: Authenticated FragmentClient instance.

    Returns:
        Dict with wallet address, publicKey, chain, walletStateInit.
    """
    return _run_async(
        _get_account_info_async(
            client.seed, client.api_key, client.wallet_version
        )
    )


async def fetch_wallet_info(
    client: "AsyncFragmentClient",
) -> WalletInfo:
    """Fetch wallet info (async).

    Args:
        client: Authenticated AsyncFragmentClient instance.

    Returns:
        WalletInfo with address, state, and balance.
    """
    return await _get_wallet_info_async(
        client.seed, client.api_key, client.wallet_version
    )


def fetch_wallet_info_sync(
    client: "FragmentClient",
) -> WalletInfo:
    """Fetch wallet info (sync).

    Args:
        client: Authenticated FragmentClient instance.

    Returns:
        WalletInfo with address, state, and balance.
    """
    return _run_async(
        _get_wallet_info_async(
            client.seed, client.api_key, client.wallet_version
        )
    )
