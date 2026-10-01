"""Compatibility user-owned anonymous-number entry points."""

from __future__ import annotations

from typing import Any


async def get_login_code(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Read a pending login code."""
    return await client.get_login_code(*args, **kwargs)


async def toggle_login_codes(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Change login-code delivery."""
    return await client.toggle_login_codes(*args, **kwargs)


async def terminate_sessions(client: Any, *args: Any, **kwargs: Any) -> Any:
    """Terminate number-associated Telegram sessions."""
    return await client.terminate_sessions(*args, **kwargs)


__all__ = ["get_login_code", "toggle_login_codes", "terminate_sessions"]