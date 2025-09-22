"""Models describing grouped statement archives."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StatementFile:
    """A single statement archive entry."""

    provider: str
    account: str
    password: bytes | None
    file: Path

    def __repr__(self) -> str:
        pwd = "***" if self.password else None
        return f"Statement: provider={self.provider}, account={self.account}, file={self.file.name}, password={pwd})"



@dataclass
class StatementGroup:
    """A collection of ``StatementFile`` entries for a single month."""

    month: str
    statements: list[StatementFile] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Group: month={self.month}"


    def add(self, statement_file: StatementFile) -> None:
        self.statements.append(statement_file)

