"""Domain logic for preparing statements and generating OFX reports."""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path

from moneywizimport.converters.RawConverterManager import create_converter
from moneywizimport.core.ofx_generator import generate_ofx_file
from moneywizimport.helpers import (
    ensure_directory,
    unzip_archive,
)
from moneywizimport.helpers.fs_helper import exec_on_file, write_text_file
from moneywizimport.logger import UnmatchedPayeeLogger
from moneywizimport.model import RawStatementConfig
from moneywizimport.model.ofx_models import OfxInfo, OfxReport, StatementTransaction, Transaction, TransactionType
from moneywizimport.model.payee_mapping import PayeeRule
from moneywizimport.model.provider_config import OfflineAccount
from moneywizimport.model.statement_groups import StatementGroup
from moneywizimport.resolvers.ResolverManager import create_resolver

logger = logging.getLogger(__name__)


def _resolve_payee(description: str, payee_rules: list[PayeeRule]) -> str | None:
    clean_description = description.strip()
    for rule in payee_rules:
        if re.search(rule.match, clean_description, flags=re.IGNORECASE):
            return rule.name
    return None


def prepare_archives(configs: list[RawStatementConfig], destination_dir: Path) -> None:
    """Copy matching archives into ``prepared_dir`` using the configured naming scheme."""

    def _convert_to_archive(raw_statement_path: Path) -> None:
        converter = create_converter(raw_statement_path)
        statement_info = converter.extract_statement(config, raw_statement_path)
        converter.convert(config, statement_info, raw_statement_path, destination_dir)

    ensure_directory(destination_dir)

    for config in configs:
        input_dir = config.input_dir.expanduser()
        if not input_dir.exists():
            logger.error("Input directory not found: %s", input_dir)
            continue

        exec_on_file(input_dir, fn=lambda file: _convert_to_archive(file)
                                    if config.pattern.match(file.name) else None)


def generate_reports(
    ofx_root: Path,
    groups: list[StatementGroup],
    payee_rules: list[PayeeRule],
    offline_accounts: list[OfflineAccount],
    log_unmatched_payees: bool
) -> None:
    """Generate OFX reports for each group of statements."""

    unmatched_logger = UnmatchedPayeeLogger()

    for group in groups:
        generate_report(ofx_root, group, payee_rules, offline_accounts, unmatched_logger)

    if log_unmatched_payees:
        unmatched_logger.log()


def _map_statements_to_transactions(payee_rules: list[PayeeRule],
                                    transactions: list[StatementTransaction],
                                    unmatched_logger: UnmatchedPayeeLogger
                                    ) -> list[Transaction]:
    reports: list[Transaction] = []

    for transaction in transactions:
        payee = _resolve_payee(transaction.details, payee_rules)

        # add unmatched payees
        if not payee:
            unmatched_logger.add(transaction.details)

        reports.append(
            Transaction(
                date_time=transaction.date_time,
                details=transaction.details,
                amount=transaction.amount,
                payee=payee)
        )

        if transaction.fee:
            reports.append(
                Transaction(
                    date_time=transaction.date_time,
                    details=transaction.details,
                    amount=transaction.fee,
                    payee=payee,
                    type=TransactionType.FEE,
                )
            )

    return reports


def generate_report(
    ofx_root: Path,
    group: StatementGroup,
    payee_rules: list[PayeeRule],
    offline_accounts: list[OfflineAccount],
    unmatched_logger: UnmatchedPayeeLogger
) -> None:
    """Generate an OFX file for one group of statement files."""

    ofx_data: list[OfxReport] = []

    with (tempfile.TemporaryDirectory() as tmp):
        temp_root = Path(tmp)

        for index, statement in enumerate(group.statements):
            statement_dir = ensure_directory(temp_root / str(index))
            statement_file = unzip_archive(statement.file, statement_dir, password=statement.password)

            resolver = create_resolver(statement.provider.get_label(), statement_file)
            account_currency = resolver.resolve_currency()
            start_balance, end_balance = resolver.resolve_balances()
            raw_transactions = resolver.resolve_transactions()

            calculate_exchange_rate(raw_transactions, account_currency)

            transactions = _map_statements_to_transactions(payee_rules, raw_transactions, unmatched_logger)

            ofx_report = OfxReport(
                info=OfxInfo(provider=statement.provider.name,
                             account=statement.account,
                             currency=account_currency),
                transactions=transactions,
                start_balance=start_balance,
                end_balance=end_balance,
            )

            logger.debug(f"{group.month} {ofx_report.info} → start: {start_balance:>10}, end: {end_balance:>10}")

            ofx_data.append(ofx_report)

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
            type = _transaction.type
        )

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
                    transaction.type = TransactionType.INTRN_XFER #XFER
                    _add_transaction_to_report(transaction)

    return ofx_data


def calculate_exchange_rate(raw_transactions: list[StatementTransaction], account_currency: str) -> None:
    for transaction in raw_transactions:
        transaction.exchange_rate = (
            round(abs(transaction.amount / transaction.foreign_amount), 6)
            if transaction.foreign_amount and transaction.currency != account_currency
            else None
        )


def _log_ofx_summary(reports: list[OfxReport]) -> None:
    """Log a concise summary for debugging purposes."""

    for report in reports:
        logger.trace("%s", report)
        for txn in report.transactions:
            logger.trace("  %r", txn)

