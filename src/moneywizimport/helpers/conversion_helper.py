from __future__ import annotations

import logging
from datetime import datetime
from typing import Tuple


logger = logging.getLogger(__name__)


def parse_float_safe(value: str, default: float | None = None) -> float | None:
    try:
        return float(value.strip()) if value.strip() else default
    except (ValueError, TypeError):
        return default


def parse_datetime(raw_datetime: str) -> datetime | None:
    raw_datetime = raw_datetime.strip()
    if not raw_datetime:
        return None

    parts = raw_datetime.split()
    date = parts[0]
    time = parts[1] if len(parts) > 1 else "00:00:00"

    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M"):
        try:
            return datetime.strptime(f"{date} {time}", fmt)
        except ValueError:
            continue
    return None


def parse_amount_currency(text: str, default_currency: str = "") -> Tuple[float, str]:
    parts = text.strip().split(maxsplit=1)
    amount = parse_float_safe(parts[0], 0.0) if parts else 0.0
    currency = parts[1] if len(parts) > 1 else default_currency
    return amount, currency
