"""Strict input normalization without implicit boolean or numeric coercion."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from ton_core import mnemonic_to_entropy

from FragmentAPI.exceptions import ConfigurationError, CookieError
from FragmentAPI.types.constants import (
    MNEMONIC_WORD_COUNTS_VALID,
    PREMIUM_MONTHS_VALID,
    STARS_GIVEAWAY_PACKAGES,
    SUPPORTED_API_PROVIDERS,
    SUPPORTED_WALLET_VERSIONS,
    VALID_PAYMENT_METHODS,
)


def normalize_seed(seed: str) -> str:
    """Validate a basic TON mnemonic and return normalized words."""
    if not isinstance(seed, str):
        raise ConfigurationError(ConfigurationError.INVALID_MNEMONIC_PHRASE)
    words = seed.lower().split()
    if len(words) not in MNEMONIC_WORD_COUNTS_VALID:
        raise ConfigurationError(
            ConfigurationError.INVALID_MNEMONIC.format(count=len(words))
        )
    try:
        mnemonic_to_entropy(words)
    except Exception as exc:
        raise ConfigurationError(
            ConfigurationError.INVALID_MNEMONIC_PHRASE
        ) from exc
    return " ".join(words)


def normalize_wallet_version(version: str) -> str:
    """Resolve wallet names case-insensitively."""
    if isinstance(version, str):
        for candidate in SUPPORTED_WALLET_VERSIONS:
            if candidate.casefold() == version.strip().casefold():
                return candidate
    raise ConfigurationError(
        ConfigurationError.UNSUPPORTED_VERSION.format(
            version=version, supported=", ".join(sorted(SUPPORTED_WALLET_VERSIONS))
        )
    )


def normalize_provider(provider: str) -> str:
    """Normalize the blockchain provider."""
    value = provider.strip().lower() if isinstance(provider, str) else ""
    if value not in SUPPORTED_API_PROVIDERS:
        raise ConfigurationError(
            ConfigurationError.UNSUPPORTED_PROVIDER.format(
                provider=provider, supported=", ".join(sorted(SUPPORTED_API_PROVIDERS))
            )
        )
    return value


def normalize_payment_method(method: str) -> str:
    """Normalize native and jetton aliases."""
    value = method.strip().lower() if isinstance(method, str) else ""
    if value not in VALID_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=method, supported=", ".join(sorted(VALID_PAYMENT_METHODS))
            )
        )
    return {"gram": "ton", "usdt_gram": "usdt_ton"}.get(value, value)


def integer(value: Any, low: int, high: int, message: str) -> int:
    """Accept only actual integers in the inclusive range."""
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ConfigurationError(message)
    return value


def months(value: Any) -> int:
    """Validate a Premium duration."""
    if isinstance(value, bool) or not isinstance(value, int) or value not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    return value


def stars_giveaway(amount: Any, winners: Any) -> None:
    """Preserve the original total-package and package-dependent winner limits."""
    if isinstance(amount, bool) or not isinstance(amount, int) or amount not in STARS_GIVEAWAY_PACKAGES:
        raise ConfigurationError(
            ConfigurationError.INVALID_GIVEAWAY_PACKAGE.format(
                amount=amount,
                packages=", ".join(map(str, sorted(STARS_GIVEAWAY_PACKAGES))),
            )
        )
    maximum = min(max(amount // 100, 1), 10_000)
    integer(
        winners, 1, maximum,
        ConfigurationError.INVALID_GIVEAWAY_WINNERS.format(
            amount=amount, max_winners=maximum
        ),
    )


def decimal_units(value: Any, decimals: int) -> int:
    """Convert a nonnegative decimal amount to exact integer units."""
    if isinstance(value, bool) or value is None:
        raise ConfigurationError("A numeric payment amount is required.")
    try:
        amount = Decimal(str(value).replace(",", "").strip())
        scaled = amount * (10 ** decimals)
    except (InvalidOperation, ValueError) as exc:
        raise ConfigurationError("Invalid payment amount.") from exc
    if not scaled.is_finite() or scaled < 0 or scaled != scaled.to_integral_value():
        raise ConfigurationError("Payment amount is negative or exceeds supported precision.")
    return int(scaled)


def parse_cookies(value: dict[str, str] | str) -> dict[str, str]:
    """Parse JSON or a Cookie header without accepting arbitrary objects."""
    try:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("{"):
                value = json.loads(text)
            else:
                value = dict(
                    piece.strip().split("=", 1)
                    for piece in text.split(";") if "=" in piece
                )
        if not isinstance(value, dict):
            raise TypeError("Cookies must be an object.")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            raise TypeError("Cookie keys and values must be strings.")
        return dict(value)
    except Exception as exc:
        raise CookieError(CookieError.READ_FAILED.format(exc=exc)) from exc


def validate_cookie_keys(cookies: dict[str, str], required: tuple[str, ...]) -> None:
    """Require nonempty cookie values."""
    missing = [key for key in required if not cookies.get(key, "").strip()]
    if missing:
        raise CookieError(CookieError.MISSING_KEYS.format(keys=", ".join(missing)))


def recipient(value: str) -> str:
    """Normalize a username or a Telegram public link."""
    if not isinstance(value, str):
        raise ConfigurationError("Recipient must be a string.")
    value = value.strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    value = value.lstrip("@").rstrip("/")
    if not value or any(character in value for character in "/?#&"):
        raise ConfigurationError("A public Telegram username is required.")
    return value