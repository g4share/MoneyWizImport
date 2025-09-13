from datetime import datetime
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from moneywizimport.core.ofx_generator import write_ofx_file
from moneywizimport.helpers import unzip, zip, unzip_group
from moneywizimport.helpers.fs_helper import delete_files
from moneywizimport.helpers.html_helper import (
    extract_balances,
    extract_transactions,
    read_statement_date,
)


def prepare_archives(statement_dir: Path, password: bytes | None = None) -> None:
    """Normalize statement archives for further processing.

    Each ``*.zip`` file in ``statement_dir`` is unzipped, the contained
    HTML statement is re-zipped using the ``VB_YYYY-MM-DD.zip`` naming
    scheme expected by MoneyWiz, and the original archive is removed.

    Parameters
    ----------
    statement_dir:
        Directory containing the original statement archives.
    password:
        Optional ZIP password for both reading and writing archives.
    """

    tmp = Path(tempfile.mkdtemp(prefix="mwz_"))
    try:
        for z in sorted(Path(statement_dir).expanduser().glob("*.zip")):
            if z.name.startswith("VB_"):
                continue
            print(f"ZIP: {z.name}")
            html_file = unzip(z, tmp, password=password)
            if html_file:
                date_str = read_statement_date(html_file)
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                archive_name = statement_dir / f"VB_{dt.date().isoformat()}.zip"
                zip([html_file], archive_name, password=password)
                z.unlink(missing_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def resolve_category(payee: str, categories_mapping: dict[str, str] | None) -> str:
    """Return the category path for ``payee``.

    Parameters
    ----------
    payee:
        Normalised payee name.
    categories_mapping:
        Mapping of payee name (lowercase) to a full category path. If
        ``None`` or the payee is not found, ``': UNKNOWN'`` is returned.
    """

    if not categories_mapping:
        return ": UNKNOWN"
    return categories_mapping.get(payee.lower(), ": UNKNOWN")


def resolve_payee(description: str, rules: list[tuple[str, str]] | None) -> str:
    """Resolve a human-readable payee name from a transaction description.

    Parameters
    ----------
    description:
        Raw transaction description string.
    rules:
        Optional list of ``(regex, label)`` tuples. The first matching
        regex (case-insensitive) yields the associated label.

    Returns
    -------
    str
        A normalised payee name or ``': UNKNOWN'`` if no rule matches.
    """

    if not rules:
        return ": UNKNOWN"

    desc = description.strip()

    for pattern, label in rules:
        if re.search(pattern, desc, flags=re.IGNORECASE):
            return label

    return ": UNKNOWN"


def generate_reports(
    ofx_path: Path,
    groups: list[dict[str, Any]],
    payees_mapping: list[tuple[str, str]] | None = None,
    categories_mapping: dict[str, str] | None = None,
) -> None:
    """Generate OFX reports for grouped statement files.

    Parameters
    ----------
    ofx_path:
        Destination directory for the generated OFX files.
    groups:
        Output from :func:`collect_statement_files` grouping files by
        month.
    payees_mapping:
        Optional list of regex rules for payee resolution.
    categories_mapping:
        Optional mapping of payees to category names.
    """

    for group in groups:
        month = group["month"]
        files = group["files"]

        if datetime.strptime(month, "%Y-%m") >= datetime(2025, 2, 1):
            generate_report(
                ofx_path,
                files,
                month,
                payees_mapping,
                categories_mapping,
            )


def generate_report(
    ofx_path: Path,
    files: list[dict[str, Any]],
    month: str,
    payees_mapping: list[tuple[str, str]] | None = None,
    categories_mapping: dict[str, str] | None = None,
) -> None:
    """Generate an OFX file for a group of statement HTML files."""

    html_files = unzip_group(files)
    ofx_data: list[dict] = []

    payees_mapping = payees_mapping or []
    categories_mapping = categories_mapping or {}

    try:
        for idx, html_file in enumerate(html_files):
            transactions = extract_transactions(html_file)
            for txn in transactions:
                payee = resolve_payee(txn["details"], payees_mapping)
                txn["payee"] = payee
                txn["category"] = resolve_category(payee, categories_mapping)

            start_balance, end_balance = extract_balances(html_file)

            info = {
                "bank": files[idx]["bank"],
                "account": files[idx]["account"],
            }
            ofx_data.append(
                {
                    "info": info,
                    "transactions": transactions,
                    "start_balance": start_balance,
                    "end_balance": end_balance,
                }
            )

        for entry in ofx_data:
            print(
                f">>> {entry['info']['account']} "
                f"(start: {entry['start_balance']} end: {entry['end_balance']})"
            )

        #write_ofx_file(ofx_data, ofx_path / month)

    finally:
        delete_files(html_files)