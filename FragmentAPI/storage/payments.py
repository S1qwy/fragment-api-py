"""Durable payment journal. Never stores mnemonic phrases or cookies."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path

from FragmentAPI.exceptions import SessionStorageError
from FragmentAPI.types.models import PaymentRecord


class PaymentStorage(ABC):
    """Implement this interface to share recovery state across hosts."""

    @abstractmethod
    async def save(self, record: PaymentRecord) -> None:
        """Durably replace a payment record before returning."""

    @abstractmethod
    async def get(self, operation_id: str) -> PaymentRecord | None:
        """Return a payment or None if it has never been recorded."""

    @abstractmethod
    async def list(self, sender_address: str | None = None) -> list[PaymentRecord]:
        """Return recorded operations, optionally for one canonical address."""


class SQLitePaymentStorage(PaymentStorage):
    """Process-safe local journal with transactional commits and private creation modes."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path.home() / ".fragment-api" / "payments.sqlite3"

    def _run(self, action: str, value: PaymentRecord | str | None) -> list[PaymentRecord]:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(descriptor)
        with sqlite3.connect(self.path, timeout=10) as connection:
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS payments "
                "(operation_id TEXT PRIMARY KEY, sender TEXT NOT NULL, document TEXT NOT NULL)"
            )
            if action == "save":
                assert isinstance(value, PaymentRecord)
                connection.execute(
                    "INSERT OR REPLACE INTO payments VALUES (?, ?, ?)",
                    (value.operation_id, value.sender_address, value.model_dump_json()),
                )
                return []
            if action == "get":
                rows = connection.execute("SELECT document FROM payments WHERE operation_id = ?", (value,))
            elif value is None:
                rows = connection.execute("SELECT document FROM payments ORDER BY rowid")
            else:
                rows = connection.execute("SELECT document FROM payments WHERE sender = ? ORDER BY rowid", (value,))
            return [PaymentRecord.model_validate(json.loads(row[0])) for row in rows]

    async def _call(self, action: str, value: PaymentRecord | str | None) -> list[PaymentRecord]:
        try:
            return await asyncio.to_thread(self._run, action, value)
        except Exception as exc:
            raise SessionStorageError(f"Payment journal {action} failed: {exc}") from exc

    async def save(self, record: PaymentRecord) -> None:
        await self._call("save", record)

    async def get(self, operation_id: str) -> PaymentRecord | None:
        records = await self._call("get", operation_id)
        return records[0] if records else None

    async def list(self, sender_address: str | None = None) -> list[PaymentRecord]:
        return await self._call("list", sender_address)
