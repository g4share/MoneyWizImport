"""Data models for OFX report generation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import cast


@dataclass
class StatementTransaction:
    """Raw transaction data parsed from the statement file."""

    date_time: datetime
    details: str
    amount: float
    currency: str | None
    foreign_amount: float | None = None
    exchange_rate: float | None = None
    fee: float | None = None


class TransactionType(str, Enum):
    FEE = ("FEE", "FEE")
    XFER = ("XFER", "XFER")
    INTRN_XFER = ("INTRN_XFER", "OTHER")
    OTHER = ("OTHER", "OTHER")

    def __new__(cls, code: str, ofx_value: str) -> "TransactionType":
        obj = cast("TransactionType", str.__new__(cls, code))
        obj._value_ = code
        obj.ofx_value = ofx_value
        return obj

@dataclass
class Transaction:
    """Transaction representation to be written to OFX."""

    date_time: datetime
    details: str
    amount: float
    type: TransactionType = TransactionType.OTHER
    payee: str | None = None

    def id(self) -> str:
        base = f"{self.date_time.isoformat()}|{self.details}|{self.amount}"
        return hashlib.md5(base.encode("utf-8")).hexdigest()


    def description(self) -> str:
        """Return description for OFX <MEMO> field."""

        if self.type == TransactionType.FEE:
            return "Fee" if self.payee else f"{self.details}: Fee"
        if self.type in (TransactionType.XFER, TransactionType.INTRN_XFER):
            return self.payee if self.payee else self.details
        return "" if self.payee else self.details

    def __repr__(self) -> str:
        return (
            f"payee: {self.payee} | "
            f"type: {self.type} | "
            f"details: {self.details} | "
            f"amount: {self.amount} | "
            f"descr: {self.description()}"
        )


@dataclass
class OfxInfo:
    """Information describing the account for an OFX report."""

    provider: str
    account: str
    currency: str | None

    def __repr__(self) -> str:
        return f"{self.provider:<15}  {self.account:<25} | {self.currency:<3}"


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
