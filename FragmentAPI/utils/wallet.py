"""Offline preparation and non-replaying TON transaction execution."""

from __future__ import annotations

import base64
import asyncio
import copy
import hashlib
import inspect
import json
import secrets
import threading
import time
from typing import TYPE_CHECKING, Any

from ton_core import (
    Address,
    NetworkGlobalID,
    WalletHighloadV2Params,
    WalletHighloadV3Params,
)
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
    HIGHLOAD_WALLET_VERSIONS,
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
    PaymentConfirmation,
    PaymentRecord,
    TransactionResult,
    WalletInfo,
)
from FragmentAPI.utils.auth import derive_account
from FragmentAPI.utils.decoder import decode_boc
from FragmentAPI.utils.validation import decimal_units, normalize_payment_method

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

HIGHLOAD_QUERY_ID_SPACE = 1 << 23
HIGHLOAD_BIT_NUMBER_SPACE = 1 << 10
HIGHLOAD_BIT_NUMBER_MASK = HIGHLOAD_BIT_NUMBER_SPACE - 1

_query_id_lock = threading.Lock()
_query_id_sequence = secrets.randbits(23)


def next_highload_query_id() -> int:
    """Allocate a unique Highload v3 query id.

    The contract splits the id into a 13-bit dictionary shift and a 10-bit
    bit number, rejects the reserved bit number 1023, and refuses to run a
    second payment that reuses a pair still inside its retention window.
    """
    global _query_id_sequence
    with _query_id_lock:
        for _ in range(HIGHLOAD_BIT_NUMBER_SPACE):
            _query_id_sequence = (_query_id_sequence + 1) % HIGHLOAD_QUERY_ID_SPACE
            if _query_id_sequence & HIGHLOAD_BIT_NUMBER_MASK != HIGHLOAD_BIT_NUMBER_MASK:
                return _query_id_sequence
    raise WalletError("Highload wallet query identifiers are exhausted.")


def build_wallet_params(wallet_version: str) -> Any | None:
    """Allocate broadcast-time parameters for wallets that require them."""
    if wallet_version == "HighloadV2":
        return WalletHighloadV2Params()
    if wallet_version == "HighloadV3R1":
        return WalletHighloadV3Params(query_id=next_highload_query_id())
    if wallet_version in HIGHLOAD_WALLET_VERSIONS:
        raise WalletError(
            f"No transaction parameter builder exists for {wallet_version}."
        )
    return None


def native_fee(payment_nanoton: int) -> int:
    """Charge the service fee in basis points, rounding nanotons upward; a zero principal carries no fee."""
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
    raise ConfigurationError(
        "A payer seed or sender_account is required to prepare a TON transaction; "
        "the shared authentication wallet cannot be used as a payer."
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


def combine_prepared(invoices: list[PreparedTransaction], wallet_version: str) -> PreparedTransaction:
    """Combine complete invoices with one summed fee message and one gas reserve."""
    if not invoices:
        raise ConfigurationError("Cannot combine an empty invoice list.")
    first = invoices[0]
    messages: list[PreparedTransactionMessage] = []
    for invoice in invoices:
        if invoice.payment_method != first.payment_method or invoice.sender_address != first.sender_address:
            raise TransactionError("Batch invoices must use the same sender and payment method.")
        portion = list(invoice.messages)
        if invoice.fee_nanoton:
            if not portion or portion[-1].address != FEE_ADDRESS or int(portion[-1].amount) != invoice.fee_nanoton:
                raise TransactionError("Invoice service fee message is inconsistent.")
            portion.pop()
        messages.extend(message.model_copy(deep=True) for message in portion)
    fee = sum(invoice.fee_nanoton for invoice in invoices)
    if fee:
        messages.append(PreparedTransactionMessage(address=FEE_ADDRESS, amount=str(fee)))
    if len(messages) > WALLET_MAX_MESSAGES[wallet_version]:
        raise TransactionError(
            f"Batch needs {len(messages)} messages; {wallet_version} permits "
            f"{WALLET_MAX_MESSAGES[wallet_version]}. Nothing was broadcast; use a smaller batch or a highload wallet."
        )
    expiration = min(invoice.valid_until for invoice in invoices)
    if expiration <= int(time.time()):
        raise TransactionError("A batch invoice expired during preparation; nothing was broadcast.")
    reserve = max(invoice.gas_reserve_nanoton for invoice in invoices)
    units = None
    if first.payment_method == "usdt_ton":
        if any(invoice.required_usdt_units is None for invoice in invoices):
            raise TransactionError("Every USDT invoice needs an exact token amount.")
        units = sum(invoice.required_usdt_units for invoice in invoices)
    request_ids = [invoice.req_id for invoice in invoices]
    if not all(request_ids) or len(set(request_ids)) != len(request_ids):
        raise TransactionError("Every batch invoice must have a distinct request id.")
    return PreparedTransaction(
        req_id="batch:" + hashlib.sha256(json.dumps(request_ids).encode()).hexdigest(),
        item_kind="batch", target="", amount=len(invoices), valid_until=expiration,
        messages=messages, sender_address=first.sender_address,
        payment_method=first.payment_method, required_usdt_units=units,
        payment_nanoton=sum(invoice.payment_nanoton for invoice in invoices),
        fee_nanoton=fee, gas_reserve_nanoton=reserve,
        required_nanoton=sum(int(message.amount) for message in messages) + reserve,
        raw={"invoices": [invoice.model_dump(mode="json") for invoice in invoices]},
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


async def _transfer(wallet: Any, prepared: PreparedTransaction, params: Any = None) -> Any:
    """Use available tonutils message APIs, selecting the API before broadcasting."""
    single = getattr(wallet, "transfer_message", None)
    batch = getattr(wallet, "batch_transfer_message", None)
    if len(prepared.messages) == 1 and callable(single):
        return await single(_builder(prepared.messages[0]), params)
    if callable(batch):
        builders = [_builder(message) for message in prepared.messages]
        return await batch(builders, params)

    if len(prepared.messages) == 1:
        message = prepared.messages[0]
        if message.state_init:
            raise TransactionError("This wallet transfer API cannot preserve state_init.")
        transfer = getattr(wallet, "transfer", None)
        if callable(transfer):
            arguments: dict[str, Any] = {
                "destination": message.address,
                "amount": int(message.amount),
                "body": decode_boc(message.payload) if message.payload else None,
            }
            if "params" in inspect.signature(transfer).parameters:
                arguments["params"] = params
            return await transfer(**arguments)
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
    confirmations: list[PaymentConfirmation] | None = None,
) -> TransactionResult:
    """Broadcast exactly once under the client's wallet lock.

    Highload and ordinary wallets share Fragment fulfillment confirmation.
    A changed balance or seqno is never treated as proof of this payment.
    """
    client._require_wallet()
    account = await build_account_info(client)
    payer = _raw_address(account["address"])
    async with client._wallet_lock, client.wallet_lock_factory(payer):
        if prepared.valid_until <= int(time.time()):
            raise TransactionError("Prepared transaction has expired.")
        if len(prepared.messages) > WALLET_MAX_MESSAGES[client.wallet_version]:
            raise TransactionError("Prepared message count exceeds wallet capacity.")
        intent = prepared.req_id or json.dumps(
            [message.model_dump() for message in prepared.messages], sort_keys=True
        )
        operation_id = hashlib.sha256(f"{payer}:{intent}".encode()).hexdigest()
        previous = await client.payment_storage.get(operation_id)
        if previous is not None:
            raise BroadcastUncertainError(
                "This payment is already recorded; use reconcile_payment instead of paying again.",
                operation_id=operation_id,
            )
        requested = {context.req_id for context in confirmations or [] if context.req_id}
        for pending in await client.payment_storage.list(payer):
            existing = {context.req_id for context in pending.confirmations if context.req_id}
            if requested & existing and pending.state != "not_broadcast":
                raise BroadcastUncertainError(
                    "An invoice in this payment is already recorded; reconcile the original operation.",
                    operation_id=pending.operation_id,
                )
            if pending.state in {"sending", "unknown"} or (
                pending.state == "broadcast" and pending.receipt is not None
                and pending.receipt.seqno_before is not None and pending.receipt.seqno_after is None
            ):
                raise BroadcastUncertainError(
                    "The payer has an unresolved payment; reconcile it before sending another one.",
                    operation_id=pending.operation_id,
                )
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
                    required_usdt_units = prepared.required_usdt_units
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
            params = build_wallet_params(client.wallet_version)
            # Build and journal the signed message BEFORE crossing the network boundary.
            # Recovery then has its hash/BOC even if cancellation kills the HTTP request.
            build = getattr(wallet, "build_external_message", None)
            if not callable(build):
                raise TransactionError("Installed wallet cannot sign a message before broadcasting.")
            seqno = await wallet.seqno() if hasattr(wallet, "seqno") else None
            signed = await build([_builder(message) for message in prepared.messages], params)
            identifier, boc = _extract_tx_result(signed)
            if not identifier or not boc:
                raise TransactionError("The signed wallet message has no recoverable hash or BOC.")
            if prepared.valid_until <= int(time.time()):
                raise TransactionError("Prepared transaction expired while signing.")
            receipt = TransactionResult(
                tx_hash=identifier, boc=boc, status="unknown", operation_id=operation_id,
                seqno_before=seqno, balance_before=balance / NANO_PER_TON,
                payment_nanoton=prepared.payment_nanoton, fee_nanoton=prepared.fee_nanoton,
            )
            record = PaymentRecord(
                operation_id=operation_id, sender_address=payer, state="sending",
                prepared=prepared, receipt=receipt, confirmations=confirmations or [],
            )
            await client.payment_storage.save(record)
            try:
                await ton.send_message(signed.as_hex)
            except asyncio.CancelledError:
                record.state = "unknown"
                record.error = "Task cancelled during broadcast; inspect the recorded signed message."
                await asyncio.shield(client.payment_storage.save(record))
                raise
            except Exception as exc:
                record.state = "unknown"
                record.error = str(exc)
                await client.payment_storage.save(record)
                raise BroadcastUncertainError(
                    "Broadcast outcome is unknown; reconcile this invoice before sending another payment.",
                    operation_id=operation_id,
                    attempted=True,
                ) from exc
            receipt.status = "broadcast"
            record.state = "broadcast"
            try:
                await client.payment_storage.save(record)
            except Exception as exc:
                raise BroadcastUncertainError(
                    "Wallet accepted the message but its receipt could not be persisted; reconcile the journal entry.",
                    operation_id=operation_id,
                    attempted=True,
                ) from exc
            if seqno is not None:
                # Seqno only coordinates the next send; it never confirms fulfillment.
                try:
                    async def wait_seqno() -> int:
                        while True:
                            current = await wallet.seqno()
                            if current > seqno:
                                return current
                            await asyncio.sleep(0.5)
                    receipt.seqno_after = await asyncio.wait_for(wait_seqno(), client.timeout)
                except Exception as exc:
                    receipt.confirmation_error = f"Wallet sequence remains unresolved: {exc}"
                await client.payment_storage.save(record)
            return receipt


async def execute_transaction(
    client: FragmentClient,
    transaction_data: dict[str, Any],
    *,
    payment_method: str = "ton",
    payment_nanoton: int = 0,
    required_usdt_units: int | None = None,
    confirmation: PaymentConfirmation | None = None,
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
        req_id=confirmation.req_id if confirmation else "",
        sender_address=account["address"],
        gas_reserve_nanoton=client.gas_reserve_nanoton,
    )
    contexts = [confirmation] if confirmation is not None else []
    if not contexts and transaction_data.get("confirm_method"):
        req_id = str((transaction_data.get("confirm_params") or {}).get("id", ""))
        contexts.append(PaymentConfirmation(
            transaction=transaction_data, account=account, req_id=req_id,
            page_url=transaction_data.get("confirm_url") or "https://fragment.com",
        ))
    return await execute_prepared(
        client, prepared, required_usdt_units=required_usdt_units, confirmations=contexts,
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
