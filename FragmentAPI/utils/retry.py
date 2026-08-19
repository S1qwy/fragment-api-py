"""
Retry utilities with exponential backoff for Fragment HTTP requests.

Provides a decorator that automatically retries failed HTTP operations
with configurable delay, jitter, and status code filtering.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
from typing import Any, Callable, TypeVar

from FragmentAPI.exceptions import (
    FragmentPageError,
    RetryExhaustedError,
)
from FragmentAPI.types.constants import (
    RETRY_BASE_DELAY,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_DELAY,
    RETRY_MULTIPLIER,
    RETRY_STATUS_CODES,
)

logger = logging.getLogger("FragmentAPI")

F = TypeVar("F", bound=Callable[..., Any])


def _should_retry_exception(exc: Exception) -> bool:
    """Determine if an exception warrants a retry."""
    if isinstance(exc, FragmentPageError):
        msg = str(exc)
        for code in RETRY_STATUS_CODES:
            if f"HTTP {code}" in msg:
                return True
    exc_str = str(exc).lower()
    retry_indicators = ("timeout", "connection", "reset", "broken pipe", "429", "too many requests")
    return any(indicator in exc_str for indicator in retry_indicators)


def with_retry(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    multiplier: float = RETRY_MULTIPLIER,
    context: str = "operation",
) -> Callable[[F], F]:
    """Decorator that retries an async function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including initial).
        base_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay between retries.
        multiplier: Delay multiplier after each retry.
        context: Human-readable operation name for logging.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            delay = base_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc

                    if not _should_retry_exception(exc) or attempt == max_attempts:
                        raise

                    jitter = random.uniform(0, delay * 0.3)
                    sleep_time = min(delay + jitter, max_delay)

                    logger.warning(
                        "Retry %d/%d for %s in %.1fs: %s",
                        attempt, max_attempts, context, sleep_time, exc,
                    )
                    await asyncio.sleep(sleep_time)
                    delay *= multiplier

            raise RetryExhaustedError(
                RetryExhaustedError.EXHAUSTED.format(
                    attempts=max_attempts,
                    context=context,
                    last_error=str(last_exc),
                )
            )
        return wrapper
    return decorator