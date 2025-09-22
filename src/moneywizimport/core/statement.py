"""Domain logic for preparing statements and generating OFX reports."""

from __future__ import annotations

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path

from moneywizimport.core.ofx_generator import write_ofx_file
from moneywizimport.helpers import (
    copy_file,
    delete_paths,
    ensure_directory,
    unzip_archive,
)
from moneywizimport.helpers.html_helper import (
    extract_balances,
    extract_transactions,
    read_account_currency,
    read_iban,
    read_statement_date,
)
from moneywizimport.model import RawStatementConfig, StatementInfo
from moneywizimport.model.ofx_models import OfxInfo, OfxReport, StatementTransaction, Transaction
from moneywizimport.model.payee_mapping import PayeeRule
from moneywizimport.model.statement_groups import StatementGroup

logger = logging.getLogger(__name__)


def _get_statement_info(config: RawStatementConfig, archive_path: Path) -> StatementInfo:
    """Extract metadata from a statement archive."""

    temp_dir = Path(tempfile.mkdtemp(prefix="mwz_"))
    try:
        html_file = unzip_archive(archive_path, temp_dir, password=config.zip_password)
        if not html_file:
            raise ValueError(f"Could not extract HTML from {archive_path}")

        date_str = read_statement_date(html_file)
        parsed_date = datetime.strptime(date_str, "%d-%m-%Y")
        iban = read_iban(html_file)

        return StatementInfo(
            year=f"{parsed_date.year:04d}",
            month=f"{parsed_date.month:02d}",
            day=f"{parsed_date.day:02d}",
            iban=iban,
        )
    finally:
        delete_paths([temp_dir])


def _resolve_category(payee: str, categories: dict[str, str] | None) -> str:
    if not categories:
        return ": UNKNOWN"
    return categories.get(payee.lower(), ": UNKNOWN")


def _prepare_archive(config: RawStatementConfig, archive_path: Path, destination_dir: Path) -> None:
    """Normalise the archive name and copy it to ``destination_dir``."""

    statement_info = _get_statement_info(config, archive_path)
    new_name = config.rename_template.format(**vars(statement_info))
    target_path = destination_dir / new_name

    if copy_file(archive_path, target_path):
        logger.info("Copied %s → %s", archive_path, target_path)


def _resolve_payee(description: str, payee_rules: list[PayeeRule]) -> str:
    clean_description = description.strip()
    for rule in payee_rules:
        if re.search(rule.match, clean_description, flags=re.IGNORECASE):
            return rule.name
    return ": UNKNOWN"


def _map_statement_to_transaction(
    statement_txn: StatementTransaction,
    payee_rules: list[PayeeRule],
    categories: dict[str, str],
) -> Transaction:
    payee = _resolve_payee(statement_txn.details, payee_rules)
    return Transaction(
        date=f"{statement_txn.date} {statement_txn.time}" if statement_txn.time else statement_txn.date,
        details=statement_txn.details,
        amount=statement_txn.amount,
        payee=payee,
        category=_resolve_category(payee, categories),
    )


def prepare_archives(configs: list[RawStatementConfig], prepared_dir: Path) -> None:
    """Copy matching archives into ``prepared_dir`` using the configured naming scheme."""

    ensure_directory(prepared_dir)

    for config in configs:
        input_dir = config.input_dir.expanduser()
        if not input_dir.exists():
            logger.error("Input directory not found: %s", input_dir)
            continue

        for file_path in sorted(p for p in input_dir.iterdir() if p.is_file()):
            if config.pattern.match(file_path.name):
                _prepare_archive(config, file_path, prepared_dir)


def generate_reports(
    ofx_root: Path,
    groups: list[StatementGroup],
    payee_rules: list[PayeeRule],
    category_map: dict[str, str],
) -> None:
    """Generate OFX reports for each group of statements."""

    for group in groups:
        generate_report(ofx_root, group, payee_rules, category_map)


def generate_report(
    ofx_root: Path,
    group: StatementGroup,
    payee_rules: list[PayeeRule],
    category_map: dict[str, str],
) -> None:
    """Generate an OFX file for one group of statement files."""

    ofx_data: list[OfxReport] = []

    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)

        for index, entry in enumerate(group.items):
            statement_dir = ensure_directory(temp_root / str(index))
            html_file = unzip_archive(entry.file, statement_dir, password=entry.password)
            if not html_file:
                logger.warning("Skipping %s because no HTML file was extracted", entry.file)
                continue

            raw_transactions = extract_transactions(html_file)
            transactions = [
                _map_statement_to_transaction(statement_txn, payee_rules, category_map)
                for statement_txn in raw_transactions
            ]

            currency = read_account_currency(html_file)
            start_balance, end_balance = extract_balances(html_file)

            ofx_data.append(
                OfxReport(
                    info=OfxInfo(bank=entry.bank, account=entry.account, currency=currency),
                    transactions=transactions,
                    start_balance=start_balance,
                    end_balance=end_balance,
                )
            )

    if not ofx_data:
        logger.warning("No OFX data generated for %s", group.month)
        return

    target_dir = ensure_directory(ofx_root / group.month)
    target_path = target_dir / f"{group.month}.ofx"
    output_file = write_ofx_file(ofx_data, target_path)
    _log_ofx_summary(output_file, ofx_data)


def _log_ofx_summary(ofx_path: Path, reports: list[OfxReport]) -> None:
    """Log a concise summary for debugging purposes."""

    logger.info("Created OFX file: %s", ofx_path)

    for report in reports:
        logger.debug(
            "Account: %s (%s) currency=%s", report.info.account, report.info.bank, report.info.currency
        )
        logger.debug("  Start balance: %s", report.start_balance)
        logger.debug("  End balance:   %s", report.end_balance)
        for txn in report.transactions:
            logger.debug(
                "    %s | %s | %s | %s",
                txn.date,
                txn.amount,
                (txn.payee or "UNKNOWN"),
                (txn.category or "-"),
            )

