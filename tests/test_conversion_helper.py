"""Unit tests for conversion helper utilities."""

from datetime import datetime

import pytest

from moneywizimport.helpers.conversion_helper import parse_amount_currency, parse_datetime, parse_float_safe


@pytest.mark.parametrize(
    ("raw", "default", "expected"),
    [
        (None, 0.0, 0.0),
        (" 1 234,56 ", None, 1234.56),
        ("not-a-number", -1.0, -1.0),
        (" 7 890,12- ", None, -7890.12),
        ("0 +", None, 0.0),
    ],
)
def test_parse_float_safe(raw: str | None, default: float | None, expected: float | None) -> None:
    assert parse_float_safe(raw, default=default) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("01-02-2025 10:11:12", datetime(2025, 2, 1, 10, 11, 12)),
        ("2025-02-01", datetime(2025, 2, 1, 0, 0, 0)),
        ("", None),
        ("bad-format", None),
    ],
)
def test_parse_datetime(raw: str, expected: datetime | None) -> None:
    assert parse_datetime(raw) == expected


@pytest.mark.parametrize(
    ("text", "default_currency", "expected_amount", "expected_currency"),
    [
        ("123.45 USD", "", 123.45, "USD"),
        ("99", "EUR", 99.0, "EUR"),
        ("10", None, 10.0, None),
    ],
)
def test_parse_amount_currency(
    text: str, default_currency: str | None, expected_amount: float, expected_currency: str | None
) -> None:
    amount, currency = parse_amount_currency(text, default_currency=default_currency)
    assert amount == expected_amount
    assert currency == expected_currency
