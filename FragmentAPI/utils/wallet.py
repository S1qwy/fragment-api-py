"""
TON wallet utilities for transaction execution and wallet info retrieval.

Handles wallet creation, balance checking, transaction signing/broadcasting,
and seqno/balance confirmation. Supports Tonapi and Toncenter providers,
and V4R2, V5R1, and HighloadWalletV3 wallet versions.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import ssl
from typing import (
    TYPE_CHECKING,
    Any,
)

from ton_core import Cell, NetworkGlobalID
from tonutils.clients import TonapiClient, ToncenterClient
from tonutils.contracts.jetton import get_wallet_address_get_method, get_wallet_data_get_method
from tonutils.exceptions import ProviderResponseError

from FragmentAPI.exceptions import (
    ConfirmationTimeout,
    SeqnoError,
    TransactionError,
    WalletError,
)
from FragmentAPI.types.constants import (
    CONFIRMATION_INTERVAL,
    CONFIRMATION_MAX_ATTEMPTS,
    MIN_GRAM_BALANCE,
    MIN_USDT_BALANCE,
    SUPPORTED_API_PROVIDERS,
    TONAPI_BASE_URL,
    USDT_GRAM_MASTER_ADDRESS,
    WALLET_CLASSES,
)
from FragmentAPI.types.results import (
    TransactionResult,
    WalletInfo,
)
from FragmentAPI.utils.decoder import decode_boc_comment

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

logger = logging.getLogger("FragmentAPI")


def _make_ton_client(client: "FragmentClient") -> Any:
    """Create the appropriate tonutils client based on configured api_provider.

    Args:
        client: FragmentClient instance with api_key and api_provider set.

    Returns:
        TonapiClient or ToncenterClient context manager.
    """
    if client.api_provider == "toncenter":
        logger.debug("Using ToncenterClient with API key")
        return ToncenterClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key)
    logger.debug("Using TonapiClient with API key")
    return TonapiClient(network=NetworkGlobalID.MAINNET, api_key=client.api_key)


async def _get_usdt_balance(ton: Any, wallet_address: str) -> float:
    """Fetch USDT jetton balance for a wallet address.

    Args:
        ton: Active tonutils client (Tonapi or Toncenter).
        wallet_address: TON wallet address string.

    Returns:
        USDT balance as float, or 0.0 if no jetton wallet found.
    """
    try:
        jetton_wallet_address = await get_wallet_address_get_method(
            client=ton,
            address=USDT_GRAM_MASTER_ADDRESS,
            owner_address=wallet_address,
        )
        wallet_data = await get_wallet_data_get_method(client=ton, address=jetton_wallet_address)
        raw_balance = int(wallet_data[0]) if wallet_data else 0
        return float(raw_balance) / 1_000_000.0
    except ProviderResponseError as exc:
        if exc.code == 404:
            logger.debug("No USDT jetton wallet found for '%s', treating balance as 0", wallet_address)
            return 0.0
        logger.error("Failed to load USDT balance for '%s': %s", wallet_address, exc)
        raise WalletError(WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error loading USDT balance for '%s': %s", wallet_address, exc)
        raise WalletError(WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)) from exc


async def _wait_confirmation(
    wallet: Any,
    initial_seqno: int,
    initial_balance: float,
) -> tuple[bool, int | None, float | None]:
    """Wait for transaction confirmation by checking seqno and balance.

    Polls every CONFIRMATION_INTERVAL seconds for up to
    CONFIRMATION_MAX_ATTEMPTS attempts.

    Confirmation conditions (both must be true):
    1. seqno has incremented (network accepted the transaction)
    2. balance has decreased (GRAM were actually spent)

    Args:
        wallet: Active tonutils wallet instance.
        initial_seqno: Seqno before transaction was sent.
        initial_balance: GRAM balance before transaction.

    Returns:
        Tuple of (confirmed, current_seqno, current_balance_gram).
    """
    for attempt in range(CONFIRMATION_MAX_ATTEMPTS):
        await asyncio.sleep(CONFIRMATION_INTERVAL)

        try:
            await wallet.refresh()
            current_seqno = await wallet.seqno()
            current_balance = wallet.balance / 1_000_000_000

            if current_seqno > initial_seqno and current_balance < initial_balance:
                logger.info(
                    "Transaction confirmed: seqno %d -> %d, balance %.4f -> %.4f GRAM",
                    initial_seqno, current_seqno, initial_balance, current_balance,
                )
                return True, current_seqno, current_balance
        except Exception:
            logger.debug("Confirmation poll attempt %d failed, retrying", attempt + 1)
            continue

    return False, None, None


def _parse_messages(
    messages: list[dict[str, Any]],
) -> tuple[list[str], list[int], list[Any]]:
    """Parse Fragment transaction messages into parallel lists.

    Converts Fragment's message format into destinations, amounts, and
    body payloads suitable for wallet.transfer().

    Args:
        messages: List of message dicts from Fragment transaction payload.

    Returns:
        Tuple of (destinations, amounts, bodies).
    """
    destinations: list[str] = []
    amounts: list[int] = []
    bodies: list[Any] = []

    for msg in messages:
        destinations.append(msg["address"])
        amounts.append(int(msg["amount"]))

        raw_boc = msg.get("payload", "")
        if raw_boc:
            try:
                payload = decode_boc_comment(raw_boc)
            except Exception:
                s = raw_boc.strip().replace("-", "+").replace("_", "/")
                s += "=" * (-len(s) % 4)
                payload = Cell.one_from_boc(base64.b64decode(s))
        else:
            payload = ""

        bodies.append(payload)

    return destinations, amounts, bodies


async def _broadcast_with_retry(
    wallet: Any,
    destinations: list[str],
    amounts: list[int],
    bodies: list[Any],
) -> Any:
    """Broadcast a transaction with retry logic for rate limits and seqno conflicts.

    Supports both single and batch transfers across different tonutils versions.

    Args:
        wallet: Active tonutils wallet instance.
        destinations: List of destination addresses.
        amounts: List of amounts in nanograms.
        bodies: List of message body payloads.

    Returns:
        Transaction result from tonutils.

    Raises:
        TransactionError: If broadcast fails after all retries.
    """
    for attempt in range(6):
        try:
            await wallet.refresh()

            if len(destinations) > 1:
                result = await _batch_transfer(wallet, destinations, amounts, bodies)
            else:
                result = await _single_transfer(wallet, destinations[0], amounts[0], bodies[0])

            return result

        except ProviderResponseError as exc:
            exc_str = str(exc).lower()
            should_retry = (
                exc.code == 429
                or (exc.code == 400 and "duplicate message" in exc_str)
                or (exc.code == 406 and any(x in exc_str for x in ["seqno", "current state", "unpack account state"]))
                or exc.code == 500
            )
            if should_retry and attempt < 5:
                delay = 2 + random.uniform(0, 1)
                logger.warning(
                    "Broadcast attempt %d failed (code=%d), retrying in %.1fs: %s",
                    attempt + 1, exc.code, delay, exc,
                )
                await asyncio.sleep(delay)
                continue

            if exc.code == 406 and "seqno" in exc_str:
                raise TransactionError(TransactionError.DUPLICATE_SEQNO) from exc
            raise

    raise TransactionError(
        TransactionError.BROADCAST_FAILED.format(exc="transfer loop exited without result")
    )


async def _single_transfer(wallet: Any, destination: str, amount: int, body: Any) -> Any:
    """Execute a single wallet transfer.

    Tries modern tonutils API first, falls back to legacy.
    """
    if hasattr(wallet, "transfer_message"):
        try:
            from tonutils.contracts import TONTransferBuilder
            from ton_core import Address
            builder = TONTransferBuilder(
                destination=Address(destination) if isinstance(destination, str) else destination,
                amount=amount,
                body=body,
            )
            return await wallet.transfer_message(builder)
        except ImportError:
            pass

    return await wallet.transfer(destination=destination, amount=amount, body=body)


async def _batch_transfer(
    wallet: Any,
    destinations: list[str],
    amounts: list[int],
    bodies: list[Any],
) -> Any:
    """Execute a batch wallet transfer with multiple messages.

    Tries multiple tonutils API versions for compatibility.
    """
    result = None

    if hasattr(wallet, "batch_transfer_message"):
        try:
            from tonutils.contracts import TONTransferBuilder
            from ton_core import Address

            builders = []
            for d, a, b in zip(destinations, amounts, bodies):
                builders.append(
                    TONTransferBuilder(
                        destination=Address(d) if isinstance(d, str) else d,
                        amount=a,
                        body=b,
                    )
                )
            result = await wallet.batch_transfer_message(builders)
        except ImportError:
            pass

    if result is None:
        batch_msgs = []
        try:
            from tonutils.wallet.messages import TransferMessage
            for d, a, b in zip(destinations, amounts, bodies):
                batch_msgs.append(TransferMessage(destination=d, amount=a / 1e9, body=b))
        except ImportError:
            try:
                from tonutils.wallet.data import TransferData
                for d, a, b in zip(destinations, amounts, bodies):
                    batch_msgs.append(TransferData(destination=d, amount=a / 1e9, body=b))
            except ImportError:
                pass

        if batch_msgs:
            if hasattr(wallet, "batch_transfer_messages"):
                result = await wallet.batch_transfer_messages(messages=batch_msgs)
            elif hasattr(wallet, "batch_transfer"):
                try:
                    result = await wallet.batch_transfer(messages=batch_msgs)
                except TypeError:
                    result = await wallet.batch_transfer(data_list=batch_msgs)

    if result is None:
        raise TransactionError("Wallet does not support batch transfers in this tonutils version.")

    return result


def _extract_tx_result(result: Any) -> tuple[str, str | None]:
    """Extract transaction hash and BOC from tonutils result.

    Args:
        result: Return value from wallet.transfer or batch_transfer.

    Returns:
        Tuple of (tx_hash, boc_base64).
    """
    if isinstance(result, str):
        return result, None

    tx_hash = getattr(result, "normalized_hash", None)
    if not tx_hash and hasattr(result, "hash"):
        tx_hash = result.hash

    boc_b64 = None
    if hasattr(result, "as_b64"):
        boc_b64 = result.as_b64
    else:
        try:
            if hasattr(result, "boc"):
                boc_b64 = base64.b64encode(result.boc).decode("utf-8")
            elif hasattr(result, "to_boc"):
                boc_b64 = base64.b64encode(result.to_boc()).decode("utf-8")
        except Exception:
            pass

    return str(tx_hash or ""), boc_b64


async def _run_transaction(
    client: "FragmentClient",
    transaction_data: dict[str, Any],
    skip_balance_check: bool = False,
) -> TransactionResult:
    """Execute a TON transaction with seqno/balance confirmation.

    Steps:
    1. Parse Fragment transaction payload (addresses, amounts, comments)
    2. Check wallet balance is sufficient (amount + gas) unless skip_balance_check
    3. Record initial seqno and balance
    4. Send the transfer
    5. Wait for seqno increment + balance decrease
    6. Return TransactionResult with BOC for confirmReq

    Args:
        client: FragmentClient with seed and api_key configured.
        transaction_data: Raw Fragment transaction payload.
        skip_balance_check: If True, skip upfront balance validation.

    Returns:
        TransactionResult with tx_hash, boc, and confirmation data.

    Raises:
        TransactionError: If payload is invalid or broadcast fails.
        WalletError: If balance is insufficient.
        ConfirmationTimeout: If transaction not confirmed in time.
    """
    if (
        "transaction" not in transaction_data
        or not transaction_data["transaction"].get("messages")
    ):
        raise TransactionError(TransactionError.INVALID_PAYLOAD)

    messages = transaction_data["transaction"]["messages"]

    total_amount_gram = sum(int(msg["amount"]) for msg in messages) / 1_000_000_000

    async with _make_ton_client(client) as ton:
        wallet_cls = WALLET_CLASSES[client.wallet_version]
        wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)

        if not skip_balance_check:
            try:
                await wallet.refresh()
                balance_gram = wallet.balance / 1_000_000_000
                required = total_amount_gram + MIN_GRAM_BALANCE

                if balance_gram < required:
                    raise WalletError(
                        WalletError.LOW_GRAM_BALANCE.format(
                            balance=balance_gram,
                            required=required,
                            gas=MIN_GRAM_BALANCE,
                        )
                    )
            except WalletError:
                raise
            except Exception as exc:
                logger.error("Failed to check wallet balance: %s", exc)
                raise WalletError(
                    WalletError.GRAM_BALANCE_CHECK_FAILED.format(exc=exc)
                ) from exc

        destinations, amounts, bodies = _parse_messages(messages)

        try:
            await wallet.refresh()
            initial_seqno = await wallet.seqno()
            initial_balance = wallet.balance / 1_000_000_000
        except Exception as exc:
            raise SeqnoError(SeqnoError.FETCH_FAILED.format(exc=exc)) from exc

        logger.info(
            "Broadcasting transaction: %d message(s), total %.4f GRAM, seqno=%d",
            len(messages), total_amount_gram, initial_seqno,
        )

        try:
            result = await _broadcast_with_retry(wallet, destinations, amounts, bodies)
            tx_hash, boc_b64 = _extract_tx_result(result)
        except (TransactionError, WalletError):
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

        confirmed, final_seqno, final_balance = await _wait_confirmation(
            wallet, initial_seqno, initial_balance,
        )

        if not confirmed:
            raise ConfirmationTimeout(
                ConfirmationTimeout.TIMEOUT.format(
                    seconds=int(CONFIRMATION_INTERVAL * CONFIRMATION_MAX_ATTEMPTS),
                    seqno_before=initial_seqno,
                    balance_before=initial_balance,
                )
            )

        return TransactionResult(
            tx_hash=tx_hash,
            boc=boc_b64,
            seqno_before=initial_seqno,
            seqno_after=final_seqno,
            balance_before=initial_balance,
            balance_after=final_balance,
            confirmed=confirmed,
        )


async def execute_transaction(
    client: "FragmentClient",
    transaction_data: dict[str, Any],
) -> TransactionResult:
    """Execute a TON transaction with full balance check and confirmation.

    Public entry point for single-item transactions.

    Args:
        client: FragmentClient with seed and api_key.
        transaction_data: Raw Fragment transaction payload.

    Returns:
        TransactionResult with tx_hash and BOC for confirmReq.
    """
    return await _run_transaction(client, transaction_data, skip_balance_check=False)


async def execute_batch_transaction(
    client: "FragmentClient",
    transaction_data: dict[str, Any],
) -> TransactionResult:
    """Execute a batched TON transaction with multiple inline messages.

    Balance is NOT checked here — the caller must verify it upfront
    for the entire batch. Seqno increments by 1 for the whole chunk.

    Args:
        client: FragmentClient with seed and api_key.
        transaction_data: Transaction payload with multiple messages.

    Returns:
        TransactionResult with tx_hash and BOC.
    """
    return await _run_transaction(client, transaction_data, skip_balance_check=True)


async def build_account_info(client: "FragmentClient") -> dict[str, Any]:
    """Build wallet account info dict for Fragment API requests.

    Fragment needs the wallet address, public key, chain ID, and
    state init to prepare transaction payloads.

    Args:
        client: FragmentClient with seed configured.

    Returns:
        Account info dict with address, publicKey, chain, walletStateInit.

    Raises:
        WalletError: If account info cannot be built.
    """
    async with _make_ton_client(client) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, pub_key, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            boc = wallet.state_init.serialize().to_boc()
            return {
                "address": wallet.address.to_str(False, False),
                "publicKey": pub_key.as_hex,
                "chain": "-239",
                "walletStateInit": base64.b64encode(boc).decode(),
            }
        except Exception as exc:
            logger.error("Failed to build wallet account info: %s", exc)
            raise WalletError(
                WalletError.ACCOUNT_INFO_FAILED.format(exc=exc)
            ) from exc


async def fetch_wallet_info(client: "FragmentClient") -> WalletInfo:
    """Fetch full wallet information including GRAM and USDT balances.

    Args:
        client: FragmentClient with seed and api_key.

    Returns:
        WalletInfo with address, state, gram_balance, usdt_balance.

    Raises:
        WalletError: If wallet info cannot be retrieved.
    """
    async with _make_ton_client(client) as ton:
        try:
            wallet_cls = WALLET_CLASSES[client.wallet_version]
            wallet, _, _, _ = wallet_cls.from_mnemonic(client=ton, mnemonic=client.seed)
            await wallet.refresh()

            wallet_address = wallet.address.to_str(False, False)
            gram_balance = round(wallet.balance / 1_000_000_000, 4)
            usdt_balance = await _get_usdt_balance(ton, wallet_address)

            logger.info(
                "Wallet info: %s, state=%s, %.4f GRAM, %.4f USDT",
                wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
                wallet.state.value,
                gram_balance,
                usdt_balance,
            )

            return WalletInfo(
                address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
                state=wallet.state.value,
                gram_balance=gram_balance,
                usdt_balance=round(usdt_balance, 4),
            )
        except WalletError:
            raise
        except Exception as exc:
            logger.error("Failed to fetch wallet info: %s", exc)
            raise WalletError(
                WalletError.WALLET_INFO_FAILED.format(exc=exc)
            ) from exc