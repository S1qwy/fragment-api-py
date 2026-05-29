'''
Lightweight anonymous statistics collector for Fragment API library.

Collects minimal usage data (method names, error types, library version)
to help improve the library. Runs in background with negligible overhead.
Can be disabled via FragmentClient(stats_enabled=False).

NO sensitive data is ever sent:
  - No seeds, no cookies, no api keys
  - No usernames, no recipient IDs
  - No transaction hashes, no wallet addresses
  - No amounts, no IP addresses (server-side)

Sent fields:
  - library version
  - wallet version (V4R2 / V5R1)
  - method name (purchase_stars, get_wallet, ...)
  - status (ok / error)
  - error class name (if error)
  - error message snippet (first 200 chars, scrubbed)
  - duration_ms
  - anonymous session id (random UUID per client instance)
'''

from __future__ import annotations

import asyncio
import os
import re
import time
import uuid
from typing import (
    Any,
    TYPE_CHECKING,
)

import httpx

from FragmentAPI.types.constants import STATS_ENDPOINT

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient

LIBRARY_VERSION = "v7.0.0"

SCRUB_PATTERNS = [
    (re.compile(r"\b[A-Fa-f0-9]{40,}\b"), "<hash>"),
    (re.compile(r"\b0x[A-Fa-f0-9]{40}\b"), "<eth_addr>"),
    (re.compile(r"\bEQ[A-Za-z0-9_-]{46}\b"), "<ton_addr>"),
    (re.compile(r"\bUQ[A-Za-z0-9_-]{46}\b"), "<ton_addr>"),
    (re.compile(r"@[A-Za-z0-9_]{3,32}"), "<username>"),
    (re.compile(r"\+?\d{8,15}"), "<phone>"),
    (re.compile(
        r"\b(?:seed|mnemonic|cookie|token|api[_-]?key)\b[^,;\n]{0,200}",
        re.IGNORECASE,
    ), "<sensitive>"),
]


def _scrub(text: str) -> str:
    '''Remove potentially sensitive substrings from a string.'''
    if not text:
        return ""
    s = str(text)[:200]
    for pattern, replacement in SCRUB_PATTERNS:
        s = pattern.sub(replacement, s)
    return s


class StatsCollector:
    '''
    Background anonymous statistics collector.

    One instance per FragmentClient. Fires off events asynchronously
    via httpx.AsyncClient with short timeout and never blocks the
    main code path. All errors during stat submission are silently
    swallowed.
    '''

    def __init__(
        self,
        enabled: bool = True,
        wallet_version: str = "V5R1",
    ) -> None:
        self.enabled = enabled and os.environ.get(
            "FRAGMENT_DISABLE_STATS",
            "",
        ).strip() not in ("1", "true", "True", "yes")

        self.session_id = uuid.uuid4().hex[:16]
        self.wallet_version = wallet_version
        self.client_start = time.time()
        self._tasks: set[asyncio.Task] = set()

    def _build_payload(
        self,
        method: str,
        status: str,
        duration_ms: int,
        error_class: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        '''Build a sanitized stats payload.'''
        return {
            "v": LIBRARY_VERSION,
            "sid": self.session_id,
            "wv": self.wallet_version,
            "m": method,
            "s": status,
            "d": duration_ms,
            "ec": error_class or "",
            "em": _scrub(error_message or ""),
            "ts": int(time.time()),
        }

    async def _send(self, payload: dict[str, Any]) -> None:
        '''Send a single stats event with short timeout.'''
        try:
            async with httpx.AsyncClient(timeout=3.0) as session:
                await session.post(
                    STATS_ENDPOINT,
                    json=payload,
                    headers={"user-agent": f"fragment-api-py/{LIBRARY_VERSION}"},
                )
        except Exception:
            pass

    def record(
        self,
        method: str,
        status: str,
        duration_ms: int,
        error_class: str | None = None,
        error_message: str | None = None,
    ) -> None:
        '''
        Schedule a stats event for background submission.

        Never raises, never blocks.
        '''
        if not self.enabled:
            return

        try:
            payload = self._build_payload(
                method=method,
                status=status,
                duration_ms=duration_ms,
                error_class=error_class,
                error_message=error_message,
            )

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return

            task = loop.create_task(self._send(payload))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        except Exception:
            pass

    def record_lifecycle(self, event: str) -> None:
        '''Record client lifecycle events (open / close).'''
        if not self.enabled:
            return
        try:
            duration_ms = int((time.time() - self.client_start) * 1000)
            self.record(
                method=f"_lifecycle.{event}",
                status="ok",
                duration_ms=duration_ms,
            )
        except Exception:
            pass


def tracked(method_name: str):
    '''
    Decorator that records method invocation stats for FragmentClient.

    Wraps async client methods to measure duration and report
    success/failure to the background stats collector. Never alters
    return values or exception propagation.
    '''
    def decorator(fn):
        async def wrapper(self: "FragmentClient", *args, **kwargs):
            stats = getattr(self, "_stats", None)
            start = time.time()
            try:
                result = await fn(self, *args, **kwargs)
                if stats is not None:
                    stats.record(
                        method=method_name,
                        status="ok",
                        duration_ms=int((time.time() - start) * 1000),
                    )
                return result
            except Exception as exc:
                if stats is not None:
                    stats.record(
                        method=method_name,
                        status="error",
                        duration_ms=int((time.time() - start) * 1000),
                        error_class=type(exc).__name__,
                        error_message=str(exc),
                    )
                raise
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper
    return decorator