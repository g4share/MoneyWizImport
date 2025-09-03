from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class StatementFile:
    bank: str
    account: str
    password: Optional[bytes]
    file: Path


@dataclass
class StatementGroup:
    month: str
    items: list[StatementFile]

    def __repr__(self) -> str:
        return f"<StatementGroup month={self.month!r}, items={len(self.items)}>"

    def add(self, statement_file: StatementFile) -> None:
        self.items.append(statement_file)