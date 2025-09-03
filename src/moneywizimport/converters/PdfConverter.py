import logging
from pathlib import Path

from moneywizimport.converters.RawConverter import RawConverter
from moneywizimport.helpers import zip_archive
from moneywizimport.model import RawStatementConfig, StatementInfo
from moneywizimport.resolvers.ResolverManager import create_resolver

logger = logging.getLogger(__name__)

class PdfConverter(RawConverter):

    def extract_statement(self, config: RawStatementConfig, raw_statement_path: Path) -> StatementInfo:
        resolver = create_resolver(config.label, raw_statement_path)

        date = resolver.resolve_date()
        iban = resolver.resolve_iban()

        return StatementInfo(
            year=f"{date.year:04d}",
            month=f"{date.month:02d}",
            iban=iban,
        )


    def convert(
        self,
        config: RawStatementConfig,
        statement_info: StatementInfo,
        raw_statement_path: Path,
        destination_dir: Path,
    ) -> None:
        new_name = config.rename_template.format(**vars(statement_info))
        target_path = destination_dir / new_name

        zip_archive(files=[raw_statement_path], archive_name=target_path, password=config.zip_password)
        logger.info("Created archive: %s", target_path)
