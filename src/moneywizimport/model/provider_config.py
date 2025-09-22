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
    filter: re.Pattern[str] | None
    accounts: list[Account]
    zip_password: bytes | None

    def __repr__(self) -> str:
        flt = self.filter.pattern if self.filter else None
        pwd = "***" if self.zip_password else None
        return f"Provider: {self.name}, filter={flt}, password={pwd}"


