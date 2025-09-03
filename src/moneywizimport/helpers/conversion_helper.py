from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _normalize_amount(amount: str | None) -> str:
    text = ((amount or "")
            .replace("\xa0", "") # NBSP
            .strip())

    if text.endswith("+"):
        text = text[:-1].strip()
    elif text.endswith("-"):
        text = f"-{text[:-1].strip()}"

    return text.replace(" ", "").replace(",", ".")


def parse_float_safe(value: str, default: float | None = None) -> float | None:
    try:
        normalized = _normalize_amount(value)
        return float(normalized) if normalized.strip() else default
    except (ValueError, TypeError):
        return default

def parse_datetime(raw_datetime: str) -> datetime | None:
    raw_datetime = raw_datetime.strip()
    if not raw_datetime:
        return None

    parts = raw_datetime.split()
    date = parts[0]
    time = parts[1] if len(parts) > 1 else "00:00:00"

    for fmt in (
            "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"
    ):
        try:
            return datetime.strptime(f"{date} {time}", fmt)
        except ValueError:
            continue
    return None

def parse_amount_currency(text: str, default_currency: str | None = None) -> tuple[float, str | None]:
    parts = text.strip().split(maxsplit=1)
    amount = parse_float_safe(parts[0], 0.0) if parts else 0.0
    currency = parts[1] if len(parts) > 1 else default_currency
    return amount, currency
