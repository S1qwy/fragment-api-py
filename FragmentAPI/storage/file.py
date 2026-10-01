"""Atomic JSON session persistence using collision-resistant filenames."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from FragmentAPI.exceptions import SessionStorageError
from FragmentAPI.storage.base import SessionStorage
from FragmentAPI.utils.validation import parse_cookies


class FileSessionStorage(SessionStorage):
    """Persist JSON sessions through atomic replacement."""

    def __init__(
        self,
        directory: str | Path = ".fragment_sessions",
        file_extension: str = ".json",
    ) -> None:
        self._directory = Path(directory)
        if not file_extension.startswith(".") or any(character in file_extension for character in "/\\"):
            raise ValueError("Invalid session file extension.")
        self._extension = file_extension
        self._lock = asyncio.Lock()

    def _session_path(self, session_id: str) -> Path:
        """Map the complete identifier to a collision-resistant filename."""
        digest = hashlib.sha256(session_id.encode()).hexdigest()
        return self._directory / f"{digest}{self._extension}"

    def _read(self, session_id: str) -> dict[str, Any] | None:
        """Read and validate one JSON document."""
        try:
            text = self._session_path(session_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Session document must be an object.")
        return data

    def _write(self, session_id: str, data: dict[str, Any]) -> None:
        """Write and replace one session file atomically."""
        self._directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".session-", dir=self._directory
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._session_path(session_id))
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    async def save(
        self, session_id: str, cookies: dict[str, str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist cookies without discarding existing metadata when omitted."""
        try:
            validated = parse_cookies(cookies)
            async with self._lock:
                previous = await asyncio.to_thread(self._read, session_id)
                retained = (previous or {}).get("metadata", {})
                await asyncio.to_thread(
                    self._write, session_id,
                    {
                        "cookies": validated,
                        "metadata": metadata if metadata is not None else retained,
                    },
                )
        except Exception as exc:
            raise SessionStorageError(
                SessionStorageError.SAVE_FAILED.format(exc=exc)
            ) from exc

    async def load(self, session_id: str) -> dict[str, str] | None:
        """Read cookies."""
        try:
            data = await asyncio.to_thread(self._read, session_id)
            return parse_cookies(data["cookies"]) if data is not None else None
        except Exception as exc:
            raise SessionStorageError(
                SessionStorageError.LOAD_FAILED.format(exc=exc)
            ) from exc

    async def delete(self, session_id: str) -> None:
        """Delete a session if present."""
        try:
            await asyncio.to_thread(self._session_path(session_id).unlink, missing_ok=True)
        except Exception as exc:
            raise SessionStorageError(f"Session delete failed: {exc}") from exc

    async def load_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Read metadata while preserving backend errors."""
        try:
            data = await asyncio.to_thread(self._read, session_id)
            return data.get("metadata") if data is not None else None
        except Exception as exc:
            raise SessionStorageError(
                SessionStorageError.LOAD_FAILED.format(exc=exc)
            ) from exc