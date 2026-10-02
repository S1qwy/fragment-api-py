"""Shared configuration and guarded execution for the v13 examples."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

from FragmentAPI import (
    BatchResult,
    BroadcastUncertainError,
    ConfigurationError,
    EvmPaymentResult,
    FragmentClient,
    FragmentError,
    PreparedTransaction,
)

_EXECUTE = False


def required(name: str) -> str:
    """Read a required environment variable without exposing its value."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Set the {name} environment variable.")
    return value


def setting(name: str, default: str) -> str:
    """Read an optional non-secret setting."""
    return os.getenv(name, default).strip()


def require_execution() -> None:
    """Require explicit command-line approval for a state-changing operation."""
    if not _EXECUTE:
        raise ConfigurationError(
            "This action changes account state or may spend funds. Add --execute."
        )


def make_client(
    *,
    mode: str = "read",
    account: bool = False,
    **overrides: Any,
) -> FragmentClient:
    """Create a client using environment settings and an explicit payment mode."""
    cookies = os.getenv("FRAGMENT_COOKIES")
    if account and not cookies:
        raise ConfigurationError("Set FRAGMENT_COOKIES for account operations.")

    options: dict[str, Any] = {
        "cookies": cookies,
        "wallet_version": setting("TON_WALLET_VERSION", "V5R1"),
        "api_provider": setting("TON_API_PROVIDER", "tonapi"),
        "proxy": os.getenv("FRAGMENT_PROXY") or None,
        "shared_auth_seed": os.getenv("FRAGMENT_SHARED_AUTH_SEED") or None,
    }

    if mode == "pay":
        require_execution()
        options["seed"] = required("TON_SEED")
        options["api_key"] = required("TON_API_KEY")
    elif mode == "wallet":
        options["seed"] = required("TON_SEED")
        options["api_key"] = required("TON_API_KEY")
    elif mode == "prepare":
        sender = os.getenv("TON_SENDER_ACCOUNT")
        if sender:
            try:
                options["sender_account"] = json.loads(sender)
            except ValueError as exc:
                raise ConfigurationError("TON_SENDER_ACCOUNT must be JSON.") from exc
        else:
            options["seed"] = required("TON_SEED")
    elif mode != "read":
        raise ConfigurationError(f"Unknown example client mode: {mode}")

    options.update(overrides)
    return FragmentClient(**options)


def show_result(result: Any) -> None:
    """Display lifecycle information without exposing cookies, seeds, or BOCs."""
    if isinstance(result, BatchResult):
        print(
            f"Items={result.total}, accepted={result.succeeded}, "
            f"failed={result.failed}, broadcasts={result.chunks_sent}"
        )
        for item in result.items:
            print(
                f"{item.chunk_index}: {item.type} -> {item.username}: "
                f"{item.status}"
            )
            if item.error:
                print(item.error)
        return

    if isinstance(result, PreparedTransaction):
        print("Prepared only: no transaction was broadcast.")
        print(f"Request: {result.req_id}")
        print(f"Sender: {result.sender_address}")
        print(f"Messages: {len(result.messages)}")
        print(f"Required nanotons: {result.required_nanoton}")
        print(f"Valid until: {result.valid_until}")
        return

    if isinstance(result, EvmPaymentResult):
        invoice = result.invoice
        print("Invoice only: external payment is required.")
        print(f"Request: {invoice.req_id}")
        print(f"Chain ID: {invoice.invoice_chain_id}")
        print(f"Token contract: {invoice.invoice_token}")
        print(f"Destination: {invoice.invoice_address}")
        print(f"Raw token amount: {invoice.invoice_amount_raw}")
        print(f"Token decimals: {invoice.token_decimals}")
        print(f"Expires: {invoice.expires_at}")
        return

    identifier = getattr(result, "transaction_id", None) or getattr(
        result, "tx_hash", None
    )
    if identifier is not None:
        print(f"Broadcast identifier: {identifier}")
        print(f"Fragment confirmed: {getattr(result, 'confirmed', False)}")
        error = getattr(result, "confirmation_error", None)
        if error:
            print(f"Confirmation note: {error}")
        return

    if hasattr(result, "model_dump_json"):
        print(result.model_dump_json(indent=2))
    else:
        print(result)


def run(
    actions: dict[str, Callable[[], Awaitable[None]]],
    default: str,
) -> None:
    """Run a selected example action once without automatically retrying payments."""
    global _EXECUTE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=list(actions), default=default)
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args()
    _EXECUTE = arguments.execute
    try:
        asyncio.run(actions[arguments.action]())
    except BroadcastUncertainError:
        print(
            "Broadcast outcome is unknown. Reconcile the invoice and wallet "
            "before attempting another payment."
        )
        raise SystemExit(2) from None
    except FragmentError as exc:
        print(f"{type(exc).__name__}: {exc}")
        raise SystemExit(1) from None