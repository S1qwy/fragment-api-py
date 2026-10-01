"""Opt-in retry support for idempotent operations only."""

from __future__ import annotations

import asyncio
import functools
import random
from typing import Any, Callable

from FragmentAPI.exceptions import RetryExhaustedError


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    multiplier: float = 2.0,
    context: str = "operation",
    retry_if: Callable[[Exception], bool] | None = None,
) -> Callable:
    """Retry only failures explicitly classified by the caller."""
    if isinstance(max_attempts, bool) or max_attempts < 1:
        raise ValueError("max_attempts must be positive.")

    def decorate(function: Callable) -> Callable:
        """Wrap an asynchronous idempotent function."""
        @functools.wraps(function)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Execute bounded classified attempts."""
            delay = base_delay
            for attempt in range(max_attempts):
                try:
                    return await function(*args, **kwargs)
                except Exception as exc:
                    if retry_if is None or not retry_if(exc):
                        raise
                    if attempt + 1 == max_attempts:
                        raise RetryExhaustedError(
                            f"{context} exhausted {max_attempts} attempts."
                        ) from exc
                    await asyncio.sleep(min(max_delay, delay + random.uniform(0, delay * 0.3)))
                    delay *= multiplier
        return wrapped
    return decorate