import logging
from pathlib import Path

from moneywizimport.converters.RawConverter import RawConverter
from moneywizimport.helpers import copy_file, unzip_archive
from moneywizimport.helpers.fs_helper import create_emp_folder, delete_paths
from moneywizimport.model import RawStatementConfig, StatementInfo
from moneywizimport.resolvers.ResolverManager import create_resolver

logger = logging.getLogger(__name__)

class ZipConverter(RawConverter):


    def extract_statement(self, config: RawStatementConfig, raw_statement_path: Path) -> StatementInfo:
        temp_dir = create_emp_folder()
        try:
            statement_file = unzip_archive(raw_statement_path, temp_dir, password=config.zip_password)
            if not statement_file:
                raise ValueError(f"Could not extract statement from {raw_statement_path}")

            resolver = create_resolver(config.label, statement_file)

            date = resolver.resolve_date()
            iban = resolver.resolve_iban()

            return StatementInfo(
                year=f"{date.year:04d}",
                month=f"{date.month:02d}",
                iban=iban,
            )
        finally:
            delete_paths([temp_dir])


    def convert(self, config: RawStatementConfig, statement_info: StatementInfo,
                raw_statement_path: Path, destination_dir: Path) -> None:
        new_name = config.rename_template.format(**vars(statement_info))
        target_path = destination_dir / new_name

        if copy_file(raw_statement_path, target_path):
            logger.info("Copied %s → %s", raw_statement_path, target_path)
