import shutil
import logging

from pathlib import Path

from moneywizimport.model.bank_config import BankPattern
from moneywizimport.model.statement_groups import StatementGroup, StatementFile

logger = logging.getLogger(__name__)

#
def collect_statement_files(statement_dir: Path, bank_patterns: list[BankPattern]) -> list[StatementGroup]:
    groups: list[StatementGroup] = []

    def _get_or_create_group(month_key: str) -> StatementGroup:
        for g in groups:
            if g.month == month_key:
                return g

        group = StatementGroup(month=month_key, items=[])
        groups.append(group)
        return group

    def _match_file(file: Path):
        for bank in bank_patterns:
            m = bank.filter.match(file.name)
            if not m:
                continue

            year, month, iban = m.group("year"), m.group("month"), m.group("iban")
            month_key = f"{year}-{month}"

            account_name = "UNKNOWN"
            for acc in bank.accounts:
                if acc.iban == iban:
                    account_name = acc.name
                    break

            return month_key, bank.name, account_name, bank.zip_password

        return None

    for file in statement_dir.iterdir():
        if not file.is_file():
            continue

        match = _match_file(file)
        if not match:
            continue

        month_key, bank_name, account_name, password = match
        stmt_file = StatementFile(
            bank=bank_name,
            account=account_name,
            password=password,
            file=file,
        )

        group = _get_or_create_group(month_key)
        group.add(stmt_file)

    return groups

#
def delete_paths(paths: list[Path]) -> None:
    """Remove files or directories from ``paths`` ignoring individual errors."""
    for path in paths:
        try:
            if path.exists():
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
        except OSError as exc:
            logger.warning("Failed to delete %s: %s", path, exc)

#
def copy_file(src: Path, dst: Path) -> bool:
    if dst.exists():
        return False
    shutil.copy(src, dst)
    return True