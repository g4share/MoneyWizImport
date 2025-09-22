"""Metadata extracted from statement archives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StatementInfo:
    """Statement metadata used for naming prepared archives."""

    year: str
    month: str
    day: str
    iban: str

    def __str__(self) -> str:
        """Return canonical filename representation."""

        return f"{self.year}-{self.month}-{self.day}_{self.iban}.zip"

