"""Data models for OFX report generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import hashlib


@dataclass
class StatementTransaction:
    """Raw transaction data parsed from the statement HTML."""

    date_time: datetime
    details: str
    amount: float
    currency: str
    foreign_amount: float | None = None
    exchange_rate: float | None = None
    fee: float | None = None


@dataclass
class Transaction:
    """Transaction representation to be written to OFX."""

    date_time: datetime
    details: str
    amount: float
    about: str = ""
    payee: str | None = None
    category: str | None = None

    def id(self) -> str:
        base = f"{self.date_time.isoformat()}|{self.details}|{self.amount}"
        return hashlib.md5(base.encode("utf-8")).hexdigest()


    def description(self) -> str:
        """Return description for OFX <MEMO> field."""
        return self.about if self.payee else f"{self.details} {self.about}"

    def __repr__(self) -> str:
        return (
            f"{self.id()} | "
            f"{self.date_time} | "
            f"{self.payee}"
        )


@dataclass
class OfxInfo:
    """Information describing the account for an OFX report."""

    provider: str
    account: str
    currency: str | None


@dataclass
class OfxReport:
    """Container for one OFX report."""

    info: OfxInfo
    transactions: list[Transaction]
    start_balance: float | None
    end_balance: float | None

    def __repr__(self) -> str:
        return (
            f"Account: name={self.info.account} ({self.info.provider}), currency={self.info.currency}, "
            f"start balance={self.start_balance}, end balance={self.end_balance})"
        )

