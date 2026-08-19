"""
Abstract base class for session cookie storage.

Implementations must provide async save/load/delete methods.
"""

from __future__ import annotations

import abc
from typing import Any


class SessionStorage(abc.ABC):
    """Abstract interface for persisting Fragment session cookies."""

    @abc.abstractmethod
    async def save(self, session_id: str, cookies: dict[str, str], metadata: dict[str, Any] | None = None) -> None:
        """Persist cookies for a given session identifier."""

    @abc.abstractmethod
    async def load(self, session_id: str) -> dict[str, str] | None:
        """Load cookies for a given session identifier. Returns None if not found."""

    @abc.abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete stored cookies for a given session identifier."""

    async def exists(self, session_id: str) -> bool:
        """Check whether a session exists in storage."""
        return (await self.load(session_id)) is not None

    async def load_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Load metadata for a session. Override in subclasses that support metadata."""
        return None