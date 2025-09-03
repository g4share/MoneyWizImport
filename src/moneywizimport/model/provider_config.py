"""Provider configuration models."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class OfflineAccount:
    name: str
    match: list[str]

    def __repr__(self) -> str:
        return f"OfflineAccount: name={self.name}, match={','.join(self.match)})"

@dataclass
class Account:
    """Configuration entry describing a provider account."""

    name: str
    iban: str

    def __repr__(self) -> str:
        return f"Account: {self.name:15} → {self.iban}"


@dataclass
class Provider:
    """Describes how to match statement files for a specific provider."""

    name: str
    label: str | None
    filter: re.Pattern[str] | None
    zip_password: bytes | None
    accounts: list[Account]
    iban: str | None = None

    def __repr__(self) -> str:
        flt = self.filter.pattern if self.filter else None
        pwd = "***" if self.zip_password else None
        return f"Provider: {self.name}{':' + self.label if self.label else ''}, filter={flt}, password={pwd}"


