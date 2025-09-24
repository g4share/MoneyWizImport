"""Domain logic for preparing statements and generating OFX reports."""

from __future__ import annotations

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path

from moneywizimport.core.ofx_generator import generate_ofx_file
from moneywizimport.helpers import (
    copy_file,
    delete_paths,
    ensure_directory,
    unzip_archive,
)
from moneywizimport.helpers.fs_helper import exec_on_file, write_text_file
from moneywizimport.helpers.html_helper import (
    extract_balances,
    extract_transactions,
    read_account_currency,
    read_iban,
    read_statement_date,
)
from moneywizimport.model import RawStatementConfig, StatementInfo
from moneywizimport.model.ofx_models import OfxInfo, OfxReport, StatementTransaction, Transaction, TransactionType
from moneywizimport.model.payee_mapping import PayeeRule
from moneywizimport.model.provider_config import OfflineAccount
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


def _resolve_category(payee: str | None, categories: dict[str, str] | None) -> str | None:
    if not categories or not payee:
        return None
    return categories.get(payee.lower(), None)


def _prepare_archive(config: RawStatementConfig, archive_path: Path, destination_dir: Path) -> None:
    """Normalise the archive name and copy it to ``destination_dir``."""

    statement_info = _get_statement_info(config, archive_path)
    new_name = config.rename_template.format(**vars(statement_info))
    target_path = destination_dir / new_name

    if copy_file(archive_path, target_path):
        logger.info("Copied %s → %s", archive_path, target_path)


def _resolve_payee(description: str, payee_rules: list[PayeeRule]) -> str | None:
    clean_description = description.strip()
    for rule in payee_rules:
        if re.search(rule.match, clean_description, flags=re.IGNORECASE):
            return rule.name
    return None


def prepare_archives(configs: list[RawStatementConfig], prepared_dir: Path) -> None:
    """Copy matching archives into ``prepared_dir`` using the configured naming scheme."""

    ensure_directory(prepared_dir)

    for config in configs:
        input_dir = config.input_dir.expanduser()
        if not input_dir.exists():
            logger.error("Input directory not found: %s", input_dir)
            continue

        exec_on_file(input_dir, fn=lambda file: _prepare_archive(config, file, prepared_dir)
                                        if config.pattern.match(file.name) else None)


def generate_reports(
    ofx_root: Path,
    groups: list[StatementGroup],
    payee_rules: list[PayeeRule],
    category_map: dict[str, str],
    offline_accounts: list[OfflineAccount],

) -> None:
    """Generate OFX reports for each group of statements."""

    for group in groups:
        if group.month == "2025-02":
            generate_report(ofx_root, group, payee_rules, category_map, offline_accounts)


def _map_statements_to_transactions(payee_rules: list[PayeeRule],
                                    categories: dict[str, str],
                                    transactions: list[StatementTransaction],
                                    ) -> list[Transaction]:
    reports: list[Transaction] = []

    for transaction in transactions:
        payee = _resolve_payee(transaction.details, payee_rules)
        category = _resolve_category(payee, categories)

        reports.append(
            Transaction(
                date_time=transaction.date_time,
                details=transaction.details,
                amount=transaction.amount,
                payee=payee,
                category=category)
        )

        if transaction.fee:
            reports.append(
                Transaction(
                    date_time=transaction.date_time,
                    details=transaction.details,
                    amount=transaction.fee,
                    payee=payee,
                    category=category,
                    type=TransactionType.FEE,
                )
            )

    return reports


def generate_report(
    ofx_root: Path,
    group: StatementGroup,
    payee_rules: list[PayeeRule],
    category_map: dict[str, str],
    offline_accounts: list[OfflineAccount],
) -> None:
    """Generate an OFX file for one group of statement files."""

    ofx_data: list[OfxReport] = []

    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)

        for index, statement in enumerate(group.statements):
            statement_dir = ensure_directory(temp_root / str(index))
            html_file = unzip_archive(statement.file, statement_dir, password=statement.password)
            if not html_file:
                logger.warning("Skipping %s because no HTML file was extracted", statement.file)
                continue

            raw_transactions = extract_transactions(html_file)
            transactions = _map_statements_to_transactions(payee_rules, category_map, raw_transactions)

            currency = read_account_currency(html_file)
            start_balance, end_balance = extract_balances(html_file)

            ofx_data.append(
                OfxReport(
                    info=OfxInfo(provider=statement.provider, account=statement.account, currency=currency),
                    transactions=transactions,
                    start_balance=start_balance,
                    end_balance=end_balance,
                )
            )

    if not ofx_data:
        logger.warning("No OFX data generated for %s", group.month)
        return

    add_offline_transactions(ofx_data, offline_accounts)

    target_dir = ensure_directory(ofx_root)
    ofx_file_path = target_dir / f"{group.month}.ofx"

    ofx_content = generate_ofx_file(ofx_data)
    write_text_file(ofx_file_path, ofx_content)

    _log_ofx_summary(ofx_data)
    logger.info("Created OFX file: %s", ofx_file_path)


def add_offline_transactions(
    ofx_data: list[OfxReport],
    offline_accounts: list[OfflineAccount],
) -> list[OfxReport]:
    """Detect transfers to/from offline accounts and add matching reports."""

    reports_by_account = {r.info.account: r for r in ofx_data}

    def _add_transaction_to_report(_transaction: Transaction) -> None:
        offline_txn = Transaction(
            date_time=_transaction.date_time,
            details=_transaction.details,
            amount=-_transaction.amount,
            payee=_transaction.payee,
            category=_transaction.category,
            type = _transaction.type
        )
        logger.info("  %r", offline_txn)

        offline_report = reports_by_account.get(acc.name)
        if not offline_report:
            offline_report = OfxReport(
                info=OfxInfo(
                    provider="OFFLINE",
                    account=acc.name,
                    currency=report.info.currency,
                ),
                transactions=[],
                start_balance=None,
                end_balance=None,
            )
            ofx_data.append(offline_report)
            reports_by_account[acc.name] = offline_report

        offline_report.transactions.append(offline_txn)


    for report in list(ofx_data):
        for transaction in (t for t in report.transactions if t.type != TransactionType.FEE):
            for acc in offline_accounts:
                if any(re.search(pattern, transaction.details, re.IGNORECASE) for pattern in acc.match):
                    transaction.details = acc.name
                    transaction.type = TransactionType.XFER
                    _add_transaction_to_report(transaction)

    return ofx_data


def _log_ofx_summary(reports: list[OfxReport]) -> None:
    """Log a concise summary for debugging purposes."""

    for report in reports:
        logger.debug("%s", report)
        for txn in report.transactions:
            logger.debug("  %r", txn)

