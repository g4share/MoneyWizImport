from dataclasses import dataclass
import logging
import re
from typing import Optional


@dataclass
class Account:
    name: str
    iban: str

    def __repr__(self) -> str:
        return f"<Account name={self.name!r}, iban={self.iban!r}>"

    def log(self, logger: logging.Logger, level: int = logging.DEBUG) -> None:
        logger.log(level, "    - %s → %s (%s)", self.name, self.iban)


@dataclass
class BankPattern:
    name: str
    filter: Optional[re.Pattern]
    accounts: list[Account]
    zip_password: Optional[bytes]

    def __repr__(self) -> str:
        pwd = "***" if self.zip_password else None
        filter_pattern = repr(self.filter.pattern) if self.filter else None
        return (
            f"<BankPattern "
            f"name={self.name!r}, "
            f"filter={filter_pattern}, "
            f"accounts={len(self.accounts)}, "
            f"zip_password={pwd}>"
        )

    def log(self, logger: logging.Logger, level: int = logging.DEBUG) -> None:
        pwd = "***" if self.zip_password else None
        logger.log(level, "%s (filter=%s, password=%s)", self.name, self.filter.pattern if self.filter else None, pwd)
        for acc in self.accounts:
            acc.log(logger, level)
