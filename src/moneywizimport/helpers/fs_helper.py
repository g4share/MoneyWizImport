"""Helper utilities for interacting with the local file system."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Iterable

from moneywizimport.model.bank_config import BankPattern
from moneywizimport.model.statement_groups import StatementFile, StatementGroup

logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> Path:
    """Create ``path`` (and parents) if it does not yet exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def collect_statement_files(
    statement_dir: Path, bank_patterns: Iterable[BankPattern]
) -> list[StatementGroup]:
    """Collect statement archives grouped by month."""

    groups: dict[str, StatementGroup] = {}

    def _get_or_create_group(month_key: str) -> StatementGroup:
        if month_key not in groups:
            groups[month_key] = StatementGroup(month=month_key)
        return groups[month_key]

    def _match_file(file_path: Path) -> tuple[str, str, str, bytes | None] | None:
        for bank in bank_patterns:
            if bank.filter is None:
                continue

            match = bank.filter.match(file_path.name)
            if not match:
                continue

            year = match.group("year")
            month = match.group("month")
            iban = match.group("iban")
            month_key = f"{year}-{month}"

            account_name = next(
                (account.name for account in bank.accounts if account.iban == iban),
                iban,
            )

            return month_key, bank.name, account_name, bank.zip_password

        return None

    for path in sorted(statement_dir.iterdir()):
        if not path.is_file():
            continue

        match = _match_file(path)
        if not match:
            logger.debug("Skipping unmatched file: %s", path.name)
            continue

        month_key, bank_name, account_name, password = match
        statement_file = StatementFile(
            bank=bank_name,
            account=account_name,
            password=password,
            file=path,
        )

        group = _get_or_create_group(month_key)
        group.add(statement_file)

    return [groups[key] for key in sorted(groups.keys())]


def delete_paths(paths: Iterable[Path]) -> None:
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


def copy_file(src: Path, dst: Path) -> bool:
    """Copy ``src`` to ``dst`` if the target does not already exist."""

    if dst.exists():
        logger.debug("File already exists, skipping copy: %s", dst)
        return False

    ensure_directory(dst.parent)
    shutil.copy(src, dst)
    return True

