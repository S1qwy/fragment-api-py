"""
File-based session cookie storage using JSON files.

Each session is stored as a separate JSON file in a configurable directory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

from FragmentAPI.exceptions import SessionStorageError
from FragmentAPI.storage.base import SessionStorage

logger = logging.getLogger("FragmentAPI")


class FileSessionStorage(SessionStorage):
    """Store session cookies as JSON files on the local filesystem.

    Args:
        directory: Path to directory for session files. Created if missing.
        file_extension: Extension for session files.
    """

    def __init__(self, directory: str | Path = ".fragment_sessions", file_extension: str = ".json") -> None:
        self._directory = Path(directory)
        self._extension = file_extension
        self._directory.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Build the file path for a session."""
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self._directory / f"{safe_id}{self._extension}"

    async def save(self, session_id: str, cookies: dict[str, str], metadata: dict[str, Any] | None = None) -> None:
        """Save cookies and optional metadata to a JSON file."""
        try:
            data = {"cookies": cookies, "metadata": metadata or {}}
            path = self._session_path(session_id)
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.debug("Session '%s' saved to %s", session_id, path)
        except Exception as exc:
            raise SessionStorageError(SessionStorageError.SAVE_FAILED.format(exc=exc)) from exc

    async def load(self, session_id: str) -> dict[str, str] | None:
        """Load cookies from a JSON file. Returns None if file does not exist."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
            data = json.loads(content)
            return data.get("cookies")
        except Exception as exc:
            raise SessionStorageError(SessionStorageError.LOAD_FAILED.format(exc=exc)) from exc

    async def delete(self, session_id: str) -> None:
        """Delete a session file if it exists."""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            logger.debug("Session '%s' deleted from %s", session_id, path)

    async def load_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Load metadata from the session JSON file."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
            data = json.loads(content)
            return data.get("metadata")
        except Exception:
            return None