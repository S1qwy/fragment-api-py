"""Asynchronous session persistence contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SessionStorage(ABC):
    """Storage interface for user-owned Fragment cookies."""

    @abstractmethod
    async def save(
        self, session_id: str, cookies: dict[str, str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a session."""

    @abstractmethod
    async def load(self, session_id: str) -> dict[str, str] | None:
        """Read a session or return None if absent."""

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete a session."""

    async def exists(self, session_id: str) -> bool:
        """Check whether a session exists."""
        return await self.load(session_id) is not None

    async def load_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Read optional metadata."""
        return None