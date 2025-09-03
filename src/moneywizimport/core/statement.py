from datetime import datetime
from pathlib import Path
import re
import logging
import tempfile

from moneywizimport.core.ofx_generator import write_ofx_file
from moneywizimport.helpers import unzip
from moneywizimport.helpers.fs_helper import copy_file, delete_paths
from moneywizimport.helpers.html_helper import (
    extract_balances,
    extract_transactions,
    read_statement_date, read_iban, read_account_currency,
)
from moneywizimport.model import StatementInfo, RawStatementConfig
from moneywizimport.model.ofx_models import OfxReport, Transaction, OfxInfo, StatementTransaction
from moneywizimport.model.payee_mapping import PayeeRule
from moneywizimport.model.statement_groups import StatementGroup


logger = logging.getLogger(__name__)


#
def _get_statement_info(cfg: RawStatementConfig, file: Path) -> StatementInfo:
    tmp_dir = Path(tempfile.mkdtemp(prefix="mwz_"))
    try:
        html_file = unzip(file, tmp_dir, password=cfg.zip_password)
        if not html_file:
            raise ValueError(f"Could not unzip {file}")

        date_str = read_statement_date(html_file)
        dt = datetime.strptime(date_str, "%d-%m-%Y")

        iban = read_iban(html_file)

        return StatementInfo(
            year=f"{dt.year:04d}",
            month=f"{dt.month:02d}",
            day=f"{dt.day:02d}",
            iban=iban,
        )
    finally:
        delete_paths([tmp_dir])

#
def _resolve_category(payee: str, categories_mapping: dict[str, str] | None) -> str:
    if not categories_mapping:
        return ": UNKNOWN"
    return categories_mapping.get(payee.lower(), ": UNKNOWN")

#
def _prepare_archive(config_statemen: RawStatementConfig, file: Path, prepared_dir: Path) -> None:
    statement_info = _get_statement_info(config_statemen, file)

    new_name = config_statemen.rename_template.format(**vars(statement_info))
    new_path = prepared_dir / new_name
    if copy_file(file, new_path):
        logger.info("Copied %s → %s", file, new_path)

#
def _resolve_payee(description: str, rules: list[PayeeRule]) -> str:
    desc = description.strip()

    for rule in rules:
        if re.search(rule.match, desc, flags=re.IGNORECASE):
            return rule.name

    return ": UNKNOWN"

#
def _map_statement_to_transaction(
    stmt: StatementTransaction,
    payees_mapping: list[PayeeRule],
    categories_mapping: dict[str, str],
) -> Transaction:
    payee = _resolve_payee(stmt.details, payees_mapping)
    return Transaction(
        date=f"{stmt.date} {stmt.time}" if stmt.time else stmt.date,
        details=stmt.details,
        amount=stmt.amount,
        payee=payee,
        category=_resolve_category(payee, categories_mapping),
    )


#
def prepare_archives(config_statements: list[RawStatementConfig], prepared_dir: Path) -> None:
    for config_statement in config_statements:
        input_dir = config_statement.input_dir.expanduser()
        if not input_dir.exists():
            logger.error("Input dir %s not found", input_dir)
            continue

        for file in (p for p in input_dir.iterdir() if p.is_file()):
            match_cfg = next((c for c in config_statements if c.pattern.match(file.name)), None)
            if match_cfg:
                _prepare_archive(match_cfg, file, prepared_dir)


#
def generate_reports(
    ofx_path: Path,
    groups: list[StatementGroup],
    payees_rules: list[PayeeRule],
    categories_mapping: dict[str, str],
) -> None:
    for group in groups:
        if datetime.strptime(group.month, "%Y-%m") == datetime(2025, 2, 1):
            generate_report(
                ofx_path,
                group,
                payees_rules,
                categories_mapping,
            )

#
def generate_report(
    ofx_path: Path,
    group: StatementGroup,
    payees_mapping: list[PayeeRule],
    categories_mapping: dict[str, str],
) -> None:
    """Generate an OFX file for one group of statement files."""

    files = group.items
    ofx_data: list[OfxReport] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        for idx, entry in enumerate(files):

            file_tmp = tmp_dir / str(idx)
            file_tmp.mkdir(parents=True, exist_ok=True)

            html_file = unzip(entry.file, file_tmp, password=entry.password) #TODO: create folder in zip method
            if not html_file:
                continue

            raw_txns: list[StatementTransaction] = extract_transactions(html_file)
            transactions: list[Transaction] = [
                _map_statement_to_transaction(stmt, payees_mapping, categories_mapping)
                for stmt in raw_txns
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

        output_path = ofx_path / group.month
        print_ofx_data(ofx_data)
        write_ofx_file(ofx_data, output_path)
        logger.info("OFX file created: %s", output_path)


def print_ofx_data(ofx_data: list[OfxReport]) -> None:

    for entry in ofx_data:
        print(f"Account: {entry.info.account}, {entry.info.currency}  ({entry.info.bank})")
        print(f"  Start balance: {entry.start_balance}")
        print(f"  End balance:   {entry.end_balance}")
        print("  Transactions:")
        for txn in entry.transactions:
            print(
                f"    {txn.date or '????'} | "
                f"{txn.amount:>10} | "
                f"{(txn.payee or 'UNKNOWN'):<20} | "
                f"{txn.category or '-'}"
            )
        print()
