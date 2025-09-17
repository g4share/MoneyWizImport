from dataclasses import dataclass


@dataclass
class StatementInfo:
    year: str
    month: str
    day: str
    iban: str

    def __str__(self) -> str:
        """Return canonical filename representation (generic)."""
        return f"{self.year}-{self.month}-{self.day}_{self.iban}.zip"
