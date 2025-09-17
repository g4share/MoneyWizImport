from dataclasses import dataclass
from typing import Optional


@dataclass
class StatementTransaction:
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
    date: str
    details: str
    amount: str
    payee: Optional[str] = None
    category: Optional[str] = None


@dataclass
class OfxInfo:
    bank: str
    account: str
    currency: str


@dataclass
class OfxReport:
    info: OfxInfo
    transactions: list[Transaction]
    start_balance: str
    end_balance: str
