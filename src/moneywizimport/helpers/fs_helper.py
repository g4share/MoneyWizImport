"""Filesystem helper utilities.

This module contains helpers for locating and removing statement files.
"""

from pathlib import Path
import logging
import re
from collections import defaultdict
from typing import Iterable

RE_VB = re.compile(r"^VB_(\d{4})-(\d{2})-\d{2}_(.+)\.zip$", re.IGNORECASE)
logger = logging.getLogger(__name__)

def collect_statement_files(statement_dir: Path, bank_sets: list[dict]) -> list[dict[str, list]]:
    """Return statement metadata grouped by month.

    Parameters
    ----------
    statement_dir:
        Directory containing statement archives.
    bank_sets:
        List of bank configuration dictionaries as loaded from the config
        file.
    """

    grouped: dict[str, list] = defaultdict(list)
    for bank in bank_sets:
        bank_name = bank["name"]
        pattern = bank["filter"]
        accounts = bank.get("accounts", [])
        iban_map = {acc["iban"]: acc["name"] for acc in accounts}

        for file in statement_dir.glob(pattern):
            m = RE_VB.match(file.name)
            if not m:
                continue
            year, month, iban_token = m.group(1), m.group(2), m.group(3)
            month_key = f"{year}-{month}"

            account_name = "UNKNOWN"
            for iban, acc_name in iban_map.items():
                if iban_token.casefold() == iban.casefold():
                    account_name = acc_name
                    break

            grouped[month_key].append({
                "file": file.name,
                "path": str(file.resolve()),
                "bank": bank_name,
                "account": account_name,
            })

    result = []
    for month in sorted(grouped.keys()):
        files = sorted(grouped[month], key=lambda x: x["file"])
        result.append({
            "month": month,
            "files": files
        })

    return result


def delete_files(files: Iterable[Path]) -> None:
    """Delete files if they exist.

    Any :class:`OSError` raised while deleting is logged and suppressed.
    """

    for file in files:
        try:
            file.unlink(missing_ok=True)
        except OSError as exc:  # pragma: no cover - best-effort cleanup
            logger.warning("Failed to delete %s: %s", file, exc)
