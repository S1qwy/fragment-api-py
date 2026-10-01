"""Strict validation regression tests."""

import pytest

from FragmentAPI.exceptions import ConfigurationError
from FragmentAPI.utils.validation import (
    decimal_units,
    integer,
    months,
    normalize_payment_method,
    stars_giveaway,
)
from FragmentAPI.utils.wallet import native_fee


@pytest.mark.parametrize(
    ("principal", "expected"),
    [(0, 0), (1, 1), (199, 1), (200, 1), (201, 2), (1_000_000_000, 5_000_000)],
)
def test_fee_rounding(principal: int, expected: int) -> None:
    """Round fee fractions upward using integer arithmetic."""
    assert native_fee(principal) == expected


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_strict_integer(value: object) -> None:
    """Reject booleans and implicit numeric conversions."""
    with pytest.raises(ConfigurationError):
        integer(value, 1, 100, "Invalid amount.")


@pytest.mark.parametrize("value", [True, False, 3.0, "3"])
def test_strict_months(value: object) -> None:
    """Require an actual integer duration."""
    with pytest.raises(ConfigurationError):
        months(value)


def test_original_giveaway_limits() -> None:
    """Preserve total-package limits instead of imposing five winners globally."""
    stars_giveaway(500, 5)
    stars_giveaway(1_000_000, 10_000)
    with pytest.raises(ConfigurationError):
        stars_giveaway(500, 6)
    with pytest.raises(ConfigurationError):
        stars_giveaway(501, 1)
    with pytest.raises(ConfigurationError):
        stars_giveaway(500, True)


def test_exact_decimal_units() -> None:
    """Convert currency decimals without floating-point rounding."""
    assert decimal_units("1,000.000000001", 9) == 1_000_000_000_001
    with pytest.raises(ConfigurationError):
        decimal_units("0.0000000001", 9)
    with pytest.raises(ConfigurationError):
        decimal_units(True, 9)


def test_payment_aliases() -> None:
    """Normalize native and jetton aliases independently."""
    assert normalize_payment_method("gram") == "ton"
    assert normalize_payment_method("usdt_gram") == "usdt_ton"