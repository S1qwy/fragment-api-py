"""Offline preparation and non-replaying TON transaction execution."""

from __future__ import annotations

import base64
import copy
import inspect
import time
from typing import TYPE_CHECKING, Any

from ton_core import Address, NetworkGlobalID
from tonutils.clients import TonapiClient, ToncenterClient
from tonutils.contracts.jetton import (
    get_wallet_address_get_method,
    get_wallet_data_get_method,
)
from tonutils.exceptions import ProviderResponseError, RunGetMethodError

from FragmentAPI.exceptions import (
    BroadcastUncertainError,
    ConfigurationError,
    TransactionError,
    WalletError,
)
from FragmentAPI.types.constants import (
    BASIS_POINTS_DENOMINATOR,
    FEE_ADDRESS,
    FEE_BASIS_POINTS,
    GAS_RESERVE_NANOTON,
    NANO_PER_TON,
    TVM_EXIT_ACCOUNT_NOT_FOUND,
    USDT_TON_MASTER_ADDRESS,
    USDT_UNITS,
    WALLET_CLASSES,
    WALLET_MAX_MESSAGES,
)
from FragmentAPI.types.models import (
    PreparedTransaction,
    PreparedTransactionMessage,
    TransactionResult,
    WalletInfo,
)
from FragmentAPI.utils.auth import derive_account
from FragmentAPI.utils.decoder import decode_boc
from FragmentAPI.utils.validation import decimal_units, normalize_payment_method

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


def native_fee(payment_nanoton: int) -> int:
    """Calculate ceil(payment_nanoton * 50 / 10000), with zero fee for zero principal."""
    if isinstance(payment_nanoton, bool) or not isinstance(payment_nanoton, int) or payment_nanoton < 0:
        raise ConfigurationError("Payment principal must be nonnegative integer nanotons.")
    return (
        payment_nanoton * FEE_BASIS_POINTS + BASIS_POINTS_DENOMINATOR - 1
    ) // BASIS_POINTS_DENOMINATOR


def _make_ton_client(client: FragmentClient) -> Any:
    """Construct the configured tonutils blockchain provider."""
    provider = ToncenterClient if client.api_provider == "toncenter" else TonapiClient
    return provider(network=NetworkGlobalID.MAINNET, api_key=client.api_key)


def _raw_address(value: str) -> str:
    """Canonicalize a TON address."""
    return Address(value).to_str(is_user_friendly=False)


async def build_account_info(client: FragmentClient) -> dict[str, Any]:
    """Derive the paying account locally without a network balance request."""
    if client.sender_account is not None:
        return dict(client.sender_account)
    if client.seed:
        return derive_account(client.seed, client.wallet_version)
    if client.wallet_auth:
        return derive_account(client.shared_auth_seed, "V5R1")
    raise ConfigurationError(
        "A seed or sender_account is required to prepare a TON transaction."
    )


async def _get_usdt_units(ton: Any, owner: str) -> int:
    """Fetch raw jetton units, treating only known undeployed-wallet errors as zero."""
    try:
        address = await get_wallet_address_get_method(
            client=ton,
            address=USDT_TON_MASTER_ADDRESS,
            owner_address=owner,
        )
        data = await get_wallet_data_get_method(client=ton, address=address)
        if not data:
            raise WalletError("USDT wallet data was empty.")
        return int(data[0])
    except ProviderResponseError as exc:
        if exc.code == 404:
            return 0
        raise WalletError(
            WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)
        ) from exc
    except RunGetMethodError as exc:
        if exc.exit_code == TVM_EXIT_ACCOUNT_NOT_FOUND:
            return 0
        raise WalletError(
            WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)
        ) from exc
    except WalletError:
        raise
    except Exception as exc:
        raise WalletError(
            WalletError.USDT_BALANCE_CHECK_FAILED.format(exc=exc)
        ) from exc


async def fetch_wallet_info(client: FragmentClient) -> WalletInfo:
    """Read actual provider state instead of wallet.refresh fallback state."""
    client._require_wallet()
    async with _make_ton_client(client) as ton:
        wallet, _, _, _ = WALLET_CLASSES[client.wallet_version].from_mnemonic(
            client=ton, mnemonic=client.seed
        )
        try:
            state = await ton.get_info(wallet.address)
            balance = int(state.balance)
        except Exception as exc:
            raise WalletError(
                WalletError.WALLET_INFO_FAILED.format(exc=exc)
            ) from exc
        owner = wallet.address.to_str(is_user_friendly=False)
        try:
            usdt = await _get_usdt_units(ton, owner) / USDT_UNITS
        except WalletError:
            usdt = None
        state_name = getattr(state.state, "value", str(state.state))
        return WalletInfo(
            address=wallet.address.to_str(is_user_friendly=True, is_bounceable=False),
            state=state_name,
            gram_balance=balance / NANO_PER_TON,
            usdt_balance=usdt,
            balance_nanoton=balance,
        )


def prepare_transaction(
    transaction_data: dict[str, Any],
    *,
    payment_method: str,
    payment_nanoton: int | None,
    wallet_version: str,
    item_kind: str,
    target: str,
    amount: int,
    req_id: str = "",
    sender_address: str | None = None,
    confirm_referer: str | None = None,
    gas_reserve_nanoton: int = GAS_RESERVE_NANOTON,
) -> PreparedTransaction:
    """Build immutable-intent messages and append a fee only to native principal.

    payment_nanoton must describe the actual native payment, excluding attached
    gas and service messages. Native invoices without a known principal are
    rejected instead of estimating a fee from arbitrary message values.
    """
    method = normalize_payment_method(payment_method)
    if method not in {"ton", "usdt_ton"}:
        raise ConfigurationError("EVM payments are prepared as EVM invoices.")
    if isinstance(gas_reserve_nanoton, bool) or not isinstance(gas_reserve_nanoton, int) or gas_reserve_nanoton < 0:
        raise ConfigurationError("Gas reserve must be nonnegative integer nanotons.")
    raw = copy.deepcopy(transaction_data)
    inner = raw.get("transaction")
    if not isinstance(inner, dict) or not isinstance(inner.get("messages"), list) or not inner["messages"]:
        raise TransactionError(TransactionError.INVALID_PAYLOAD)

    messages: list[PreparedTransactionMessage] = []
    for message in inner["messages"]:
        if not isinstance(message, dict):
            raise TransactionError(TransactionError.INVALID_PAYLOAD)
        value = decimal_units(message.get("amount"), 0)
        address = message.get("address")
        if not isinstance(address, str):
            raise TransactionError("A transaction message has no address.")
        _raw_address(address)
        messages.append(PreparedTransactionMessage(
            address=address,
            amount=str(value),
            payload=message.get("payload"),
            stateInit=message.get("stateInit", message.get("state_init")),
        ))

    principal = 0
    fee = 0
    if method == "ton":
        if payment_nanoton is None:
            raise TransactionError("Native invoice does not expose an exact payment principal.")
        principal = payment_nanoton
        fee = native_fee(principal)
        if principal > sum(int(message.amount) for message in messages):
            raise TransactionError("Invoice principal exceeds the attached native value.")
        if fee:
            messages.append(PreparedTransactionMessage(
                address=FEE_ADDRESS,
                amount=str(fee),
            ))

    if len(messages) > WALLET_MAX_MESSAGES[wallet_version]:
        raise TransactionError(
            f"{wallet_version} permits at most {WALLET_MAX_MESSAGES[wallet_version]} messages including the fee."
        )

    valid_until = inner.get("validUntil", inner.get("valid_until", int(time.time()) + 300))
    if isinstance(valid_until, bool):
        raise TransactionError("Invalid transaction expiration.")
    valid_until = int(valid_until)
    if valid_until <= int(time.time()):
        raise TransactionError("Fragment transaction has expired.")

    transaction_sender = inner.get("from") or sender_address
    if inner.get("from") and sender_address:
        if _raw_address(str(inner["from"])) != _raw_address(sender_address):
            raise TransactionError("Fragment transaction sender differs from the requested account.")

    required = sum(int(message.amount) for message in messages) + gas_reserve_nanoton
    return PreparedTransaction(
        req_id=req_id,
        item_kind=item_kind,
        target=target,
        amount=amount,
        valid_until=valid_until,
        messages=messages,
        raw=raw,
        sender_address=transaction_sender,
        confirm_referer=confirm_referer,
        payment_method=method,
        payment_nanoton=principal,
        fee_nanoton=fee,
        gas_reserve_nanoton=gas_reserve_nanoton,
        required_nanoton=required,
    )


def _builder(message: PreparedTransactionMessage) -> Any:
    """Construct a tonutils transfer builder without converting nanotons to floats."""
    from tonutils.contracts import TONTransferBuilder

    arguments: dict[str, Any] = {
        "destination": Address(message.address),
        "amount": int(message.amount),
        "body": decode_boc(message.payload) if message.payload else None,
    }
    if message.state_init:
        parameters = inspect.signature(TONTransferBuilder).parameters
        if "state_init" not in parameters:
            raise TransactionError(
                "Installed TONTransferBuilder cannot preserve state_init."
            )
        from ton_core import StateInit

        arguments["state_init"] = StateInit.deserialize(
            decode_boc(message.state_init).begin_parse()
        )
    return TONTransferBuilder(**arguments)


async def _transfer(wallet: Any, prepared: PreparedTransaction) -> Any:
    """Use available tonutils message APIs, selecting the API before broadcasting."""
    single = getattr(wallet, "transfer_message", None)
    batch = getattr(wallet, "batch_transfer_message", None)
    if len(prepared.messages) == 1 and callable(single):
        return await single(_builder(prepared.messages[0]))
    if callable(batch):
        builders = [_builder(message) for message in prepared.messages]
        return await batch(builders)

    if len(prepared.messages) == 1:
        message = prepared.messages[0]
        if message.state_init:
            raise TransactionError("This wallet transfer API cannot preserve state_init.")
        transfer = getattr(wallet, "transfer", None)
        if callable(transfer):
            return await transfer(
                destination=message.address,
                amount=int(message.amount),
                body=decode_boc(message.payload) if message.payload else None,
            )
    raise TransactionError(
        "Installed tonutils wallet does not expose the required atomic multi-message API."
    )


def _extract_tx_result(result: Any) -> tuple[str, str | None]:
    """Extract the normalized external-message hash and signed BOC."""
    if isinstance(result, str):
        return result, None
    identifier = getattr(result, "normalized_hash", None) or getattr(result, "hash", None)
    boc = getattr(result, "as_b64", None)
    if callable(boc):
        boc = boc()
    if isinstance(boc, bytes):
        boc = boc.decode()
    if boc is None:
        binary = getattr(result, "boc", None)
        if isinstance(binary, bytes):
            boc = base64.b64encode(binary).decode()
    return str(identifier or ""), boc


async def execute_prepared(
    client: FragmentClient,
    prepared: PreparedTransaction,
    *,
    required_usdt_units: int | None = None,
) -> TransactionResult:
    """Broadcast exactly once under the client's wallet lock.

    Highload and ordinary wallets share Fragment fulfillment confirmation.
    A changed balance or seqno is never treated as proof of this payment.
    """
    client._require_wallet()
    async with client._wallet_lock:
        if prepared.valid_until <= int(time.time()):
            raise TransactionError("Prepared transaction has expired.")
        if len(prepared.messages) > WALLET_MAX_MESSAGES[client.wallet_version]:
            raise TransactionError("Prepared message count exceeds wallet capacity.")
        async with _make_ton_client(client) as ton:
            wallet, _, _, _ = WALLET_CLASSES[client.wallet_version].from_mnemonic(
                client=ton, mnemonic=client.seed
            )
            address = wallet.address.to_str(is_user_friendly=False)
            if prepared.sender_address and _raw_address(prepared.sender_address) != address:
                raise TransactionError("Signing wallet differs from the invoice sender.")
            try:
                state = await ton.get_info(wallet.address)
                balance = int(state.balance)
            except Exception as exc:
                raise WalletError(
                    WalletError.WALLET_INFO_FAILED.format(exc=exc)
                ) from exc
            required = sum(int(message.amount) for message in prepared.messages) + prepared.gas_reserve_nanoton
            if balance < required:
                raise WalletError(
                    WalletError.LOW_TON_BALANCE.format(
                        balance=balance / NANO_PER_TON,
                        required=required / NANO_PER_TON,
                    )
                )
            if prepared.payment_method == "usdt_ton":
                if required_usdt_units is None:
                    raise TransactionError("USDT invoice did not provide an exact token amount.")
                usdt_balance = await _get_usdt_units(ton, address)
                if usdt_balance < required_usdt_units:
                    raise WalletError(
                        WalletError.LOW_USDT_BALANCE.format(
                            balance=usdt_balance / USDT_UNITS,
                            required=required_usdt_units / USDT_UNITS,
                        )
                    )
            try:
                result = await _transfer(wallet, prepared)
            except TransactionError:
                raise
            except Exception as exc:
                raise BroadcastUncertainError(
                    "Broadcast outcome is unknown; reconcile this invoice before sending another payment."
                ) from exc
            identifier, boc = _extract_tx_result(result)
            return TransactionResult(
                tx_hash=identifier,
                boc=boc,
                status="broadcast",
                balance_before=balance / NANO_PER_TON,
                payment_nanoton=prepared.payment_nanoton,
                fee_nanoton=prepared.fee_nanoton,
            )


async def execute_transaction(
    client: FragmentClient,
    transaction_data: dict[str, Any],
    *,
    payment_method: str = "ton",
    payment_nanoton: int = 0,
    required_usdt_units: int | None = None,
) -> TransactionResult:
    """Execute a non-invoice operation with an explicit payment principal.

    The default zero principal is for gas-only administrative operations.
    Paid operations must supply their actual principal.
    """
    account = await build_account_info(client)
    prepared = prepare_transaction(
        transaction_data,
        payment_method=payment_method,
        payment_nanoton=payment_nanoton,
        wallet_version=client.wallet_version,
        item_kind="operation",
        target="",
        amount=0,
        sender_address=account["address"],
        gas_reserve_nanoton=client.gas_reserve_nanoton,
    )
    return await execute_prepared(
        client, prepared, required_usdt_units=required_usdt_units
    )


async def execute_batch_transaction(
    client: FragmentClient,
    transaction_data: dict[str, Any],
    *,
    payment_method: str = "ton",
    payment_nanoton: int = 0,
    required_usdt_units: int | None = None,
) -> TransactionResult:
    """Execute an atomic multi-message operation with a fresh balance check."""
    return await execute_transaction(
        client,
        transaction_data,
        payment_method=payment_method,
        payment_nanoton=payment_nanoton,
        required_usdt_units=required_usdt_units,
    )