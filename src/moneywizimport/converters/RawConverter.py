from abc import ABC, abstractmethod
from pathlib import Path

from moneywizimport.model import RawStatementConfig, StatementInfo


class RawConverter(ABC):

    def __init__(self, file_path: Path) -> None:
        self.file_path: Path = file_path

    @abstractmethod
    def extract_statement(self, config: RawStatementConfig, raw_statement_path: Path) -> StatementInfo:
        pass


    @abstractmethod
    def convert(
        self,
        config: RawStatementConfig,
        statement_info: StatementInfo,
        raw_statement_path: Path,
        destination_dir: Path,
    ) -> None:
        pass
