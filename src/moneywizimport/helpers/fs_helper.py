"""Helper utilities for interacting with the local file system."""

from __future__ import annotations

import logging
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Iterable

from moneywizimport.model.provider_config import Provider
from moneywizimport.model.statement_groups import StatementFile, StatementGroup, StatementProvider

logger = logging.getLogger(__name__)


def create_emp_folder() -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="mwz_"))
    return temp_dir

def ensure_directory(path: Path) -> Path:
    """Create ``path`` (and parents) if it does not yet exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text_file(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def exec_on_file(
    path: Path,
    fn: Callable[[Path], None] | None = None
) -> None:
    """Run callback on each file in directory if provided."""
    if fn:
        for file in (f for f in path.iterdir() if f.is_file()):
            fn(file)


def collect_statement_files(
    statement_dir: Path, providers: Iterable[Provider],
    group_key: str | None
) -> list[StatementGroup]:
    """Collect statement archives grouped by month."""

    groups: dict[str, StatementGroup] = {}

    def _get_or_create_group(_month_key: str) -> StatementGroup:
        if _month_key not in groups:
            groups[_month_key] = StatementGroup(month=_month_key)
        return groups[_month_key]

    def _match_file(_file_path: Path) -> tuple[str, StatementFile] | None:
        for provider in providers:
            if provider.filter is None:
                continue

            match = provider.filter.match(_file_path.name)
            if not match:
                continue

            iban = match.group("iban")
            month_key = f"{match.group('year')}-{match.group('month')}"

            account_name = next(
                (account.name for account in provider.accounts if account.iban == iban),
                iban,
            )

            statement_file = StatementFile(
                provider=StatementProvider(name=provider.name, label=provider.label),
                account=account_name,
                password=provider.zip_password,
                file=_file_path
            )

            return month_key, statement_file

        return None

    def _add_group(_file_path: Path) -> None:
        result = _match_file(_file_path)
        if not result:
            logger.trace("Skipping unmatched file: %s", _file_path.name)
            return

        month_key, statement_file = result
        if group_key is None or group_key == month_key:
            group = _get_or_create_group(month_key)
            group.add(statement_file)

    exec_on_file(statement_dir, fn=_add_group)

    return [groups[key] for key in groups.keys()]


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


def get_file_suffix(file_path: Path) -> str:
    suffix = file_path.suffix
    return suffix[1:].casefold() if suffix else ""
