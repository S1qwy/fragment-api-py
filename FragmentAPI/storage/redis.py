"""Optional Redis session persistence."""

from __future__ import annotations

import json
from typing import Any

from FragmentAPI.exceptions import SessionStorageError
from FragmentAPI.storage.base import SessionStorage
from FragmentAPI.utils.validation import parse_cookies


class RedisSessionStorage(SessionStorage):
    """Persist cookies and metadata in Redis with an optional expiration."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "fragment:session:",
        ttl: int | None = None,
    ) -> None:
        if ttl is not None and (isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0):
            raise ValueError("ttl must be a positive integer.")
        self._url = redis_url
        self._prefix = prefix
        self._ttl = ttl
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        """Lazily create a Redis client."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
            except ImportError as exc:
                raise SessionStorageError("Install the redis extra to use RedisSessionStorage.") from exc
            self._redis = redis.from_url(self._url, decode_responses=True)
        return self._redis

    def _key(self, session_id: str) -> str:
        """Construct a namespaced key."""
        return f"{self._prefix}{session_id}"

    async def _read(self, session_id: str) -> dict[str, Any] | None:
        """Read one session document."""
        try:
            raw = await (await self._get_redis()).get(self._key(session_id))
            if raw is None:
                return None
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Session document must be an object.")
            return data
        except Exception as exc:
            raise SessionStorageError(
                SessionStorageError.LOAD_FAILED.format(exc=exc)
            ) from exc

    async def save(
        self, session_id: str, cookies: dict[str, str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist one session."""
        try:
            retained = {}
            if metadata is None:
                retained = (await self._read(session_id) or {}).get("metadata", {})
            document = json.dumps({
                "cookies": parse_cookies(cookies),
                "metadata": metadata if metadata is not None else retained,
            })
            await (await self._get_redis()).set(
                self._key(session_id), document, ex=self._ttl
            )
        except Exception as exc:
            raise SessionStorageError(
                SessionStorageError.SAVE_FAILED.format(exc=exc)
            ) from exc

    async def load(self, session_id: str) -> dict[str, str] | None:
        """Read validated cookies."""
        data = await self._read(session_id)
        if data is None:
            return None
        try:
            return parse_cookies(data["cookies"])
        except Exception as exc:
            raise SessionStorageError(
                SessionStorageError.LOAD_FAILED.format(exc=exc)
            ) from exc

    async def delete(self, session_id: str) -> None:
        """Delete a stored session."""
        try:
            await (await self._get_redis()).delete(self._key(session_id))
        except Exception as exc:
            raise SessionStorageError(f"Session delete failed: {exc}") from exc

    async def exists(self, session_id: str) -> bool:
        """Check existence without treating an outage as absence."""
        try:
            return bool(await (await self._get_redis()).exists(self._key(session_id)))
        except Exception as exc:
            raise SessionStorageError(f"Session existence check failed: {exc}") from exc

    async def load_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Read session metadata."""
        data = await self._read(session_id)
        return data.get("metadata") if data is not None else None

    async def aclose(self) -> None:
        """Release the Redis connection pool."""
        client, self._redis = self._redis, None
        if client is not None:
            await client.aclose()

    async def close(self) -> None:
        """Compatibility alias for aclose."""
        await self.aclose()