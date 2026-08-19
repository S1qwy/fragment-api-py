"""
Redis-based session cookie storage.

Uses redis.asyncio for non-blocking operations with optional TTL.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from FragmentAPI.exceptions import SessionStorageError
from FragmentAPI.storage.base import SessionStorage

logger = logging.getLogger("FragmentAPI")


class RedisSessionStorage(SessionStorage):
    """Store session cookies in Redis with optional TTL.

    Args:
        redis_url: Redis connection URL (e.g. "redis://localhost:6379/0").
        prefix: Key prefix for session entries.
        ttl: Time-to-live in seconds for session keys. None means no expiry.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "fragment:session:",
        ttl: int | None = None,
    ) -> None:
        self._redis_url = redis_url
        self._prefix = prefix
        self._ttl = ttl
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        """Lazily create and return the Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
            except ImportError:
                raise SessionStorageError(
                    "redis package is required for RedisSessionStorage. "
                    "Install it with: pip install redis"
                )
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _key(self, session_id: str) -> str:
        """Build the Redis key for a session."""
        return f"{self._prefix}{session_id}"

    async def save(self, session_id: str, cookies: dict[str, str], metadata: dict[str, Any] | None = None) -> None:
        """Save cookies and metadata to Redis."""
        try:
            r = await self._get_redis()
            data = json.dumps({"cookies": cookies, "metadata": metadata or {}})
            if self._ttl:
                await r.setex(self._key(session_id), self._ttl, data)
            else:
                await r.set(self._key(session_id), data)
            logger.debug("Session '%s' saved to Redis", session_id)
        except Exception as exc:
            raise SessionStorageError(SessionStorageError.SAVE_FAILED.format(exc=exc)) from exc

    async def load(self, session_id: str) -> dict[str, str] | None:
        """Load cookies from Redis. Returns None if key does not exist."""
        try:
            r = await self._get_redis()
            raw = await r.get(self._key(session_id))
            if raw is None:
                return None
            data = json.loads(raw)
            return data.get("cookies")
        except Exception as exc:
            raise SessionStorageError(SessionStorageError.LOAD_FAILED.format(exc=exc)) from exc

    async def delete(self, session_id: str) -> None:
        """Delete a session from Redis."""
        try:
            r = await self._get_redis()
            await r.delete(self._key(session_id))
            logger.debug("Session '%s' deleted from Redis", session_id)
        except Exception:
            pass

    async def exists(self, session_id: str) -> bool:
        """Check whether a session key exists in Redis."""
        try:
            r = await self._get_redis()
            return bool(await r.exists(self._key(session_id)))
        except Exception:
            return False

    async def load_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Load metadata from Redis session entry."""
        try:
            r = await self._get_redis()
            raw = await r.get(self._key(session_id))
            if raw is None:
                return None
            data = json.loads(raw)
            return data.get("metadata")
        except Exception:
            return None

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None