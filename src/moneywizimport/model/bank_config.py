"""Bank configuration models."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Account:
    """Configuration entry describing a bank account."""

    name: str
    iban: str

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Account name={self.name!r}, iban={self.iban!r}>"

    def log(self, logger: logging.Logger, level: int = logging.DEBUG) -> None:
        logger.log(level, "    - %s → %s", self.name, self.iban)


@dataclass
class BankPattern:
    """Describes how to match statement files for a specific bank."""

    name: str
    filter: Optional[re.Pattern[str]] #TODO: Is Mandatory
    accounts: list[Account]
    zip_password: Optional[bytes]

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        password_hint = "***" if self.zip_password else None
        filter_pattern = repr(self.filter.pattern) if self.filter else None
        return (
            f"<BankPattern name={self.name!r}, filter={filter_pattern}, "
            f"accounts={len(self.accounts)}, zip_password={password_hint}>"
        )

    def log(self, logger: logging.Logger, level: int = logging.DEBUG) -> None:
        password_hint = "***" if self.zip_password else None
        logger.log(
            level,
            "%s (filter=%s, password=%s)",
            self.name,
            self.filter.pattern if self.filter else None,
            password_hint,
        )
        for account in self.accounts:
            account.log(logger, level)

