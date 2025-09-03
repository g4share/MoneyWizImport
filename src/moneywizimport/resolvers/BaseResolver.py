import datetime
from abc import ABC, abstractmethod
from pathlib import Path

from moneywizimport.model import StatementTransaction


class BaseResolver(ABC):

    def __init__(self, file_path: Path) -> None:
        self.file_path: Path = file_path

    @abstractmethod
    def resolve_balances(self) -> tuple[float | None, float | None]:
        pass

    @abstractmethod
    def resolve_date(self) -> datetime.date:
        pass

    @abstractmethod
    def resolve_currency(self) -> str:
        pass

    @abstractmethod
    def resolve_iban(self) -> str:
        pass

    @abstractmethod
    def resolve_transactions(self) -> list[StatementTransaction]:
        pass
