"""Data models for OFX report generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StatementTransaction:
    """Raw transaction data parsed from the statement HTML."""

    date: str
    time: Optional[str]
    details: str
    amount: str
    currency: str
    foreign_amount: Optional[str] = None
    exchange_rate: Optional[str] = None
    fee: Optional[str] = None


@dataclass
class Transaction:
    """Transaction representation to be written to OFX."""

    date: str
    details: str
    amount: str
    payee: Optional[str] = None
    category: Optional[str] = None


@dataclass
class OfxInfo:
    """Information describing the account for an OFX report."""

    bank: str
    account: str
    currency: Optional[str]


@dataclass
class OfxReport:
    """Container for one OFX report."""

    info: OfxInfo
    transactions: list[Transaction]
    start_balance: str
    end_balance: str

