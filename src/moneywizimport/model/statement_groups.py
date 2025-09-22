"""Models describing grouped statement archives."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StatementFile:
    """A single statement archive entry."""

    bank: str
    account: str
    password: Optional[bytes]
    file: Path


@dataclass
class StatementGroup:
    """A collection of ``StatementFile`` entries for a single month."""

    month: str
    items: list[StatementFile] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<StatementGroup month={self.month!r}, items={len(self.items)}>"

    def add(self, statement_file: StatementFile) -> None:
        self.items.append(statement_file)

