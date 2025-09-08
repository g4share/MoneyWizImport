"""Core utilities for processing statements and generating OFX files."""

from pathlib import Path
import logging
import re
import shutil
import tempfile
from datetime import datetime

from moneywizimport.core.ofx_generator import write_ofx_file
from moneywizimport.helpers import unzip, unzip_group, zip_files
from moneywizimport.helpers.fs_helper import delete_files
from moneywizimport.helpers.html_helper import (
    extract_balances,
    extract_transactions,
    read_statement_date,
)

logger = logging.getLogger(__name__)

def prepare_archives(statement_dir: Path, password: bytes | None = None):
    tmp = Path(tempfile.mkdtemp(prefix="mwz_"))
    try:
        for archive in sorted(Path(statement_dir).expanduser().glob("*.zip")):
            if archive.name.startswith("VB_"):
                continue
            logger.info("ZIP: %s", archive.name)
            html_file = unzip(archive, tmp, password=password)
            if html_file:
                date_str = read_statement_date(html_file)
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                archive_name = statement_dir / f"VB_{dt.date().isoformat()}.zip"
                zip_files([html_file], archive_name, password=password)
                archive.unlink(missing_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def resolve_category(payee: str, categories_mapping: dict[str, str]) -> str:
    """
    Returns the full category path for a given payee from a provided mapping.
    If not found, returns ': UNKNOWN'.
    """
    return categories_mapping.get(payee.lower(), ": UNKNOWN")

def resolve_payee(description: str, rules: list[tuple[str, str]]) -> str:
    """
    Matches a transaction description against regex rules to identify payee name.
    Matching is case-insensitive using re.IGNORECASE.
    """
    desc = description.strip()

    for pattern, label in rules:
        if re.search(pattern, desc, flags=re.IGNORECASE):
            return label

    return ": UNKNOWN"

def generate_reports(
    ofx_path: Path,
    groups: list[dict[str, list]],
    password: bytes | None = None,
    payees_mapping: list[tuple[str, str]] | None = None,
    categories_mapping: dict[str, str] | None = None,
) -> None:

    for group in groups:
        month = group["month"]
        files = group["files"]

        if datetime.strptime(month, "%Y-%m") >= datetime(2025, 2, 1):
            generate_report(
                ofx_path,
                files,
                month,
                password,
                payees_mapping,
                categories_mapping,
            )

def generate_report(
    ofx_path: Path,
    files: list[dict[str, str]],
    month: str,
    password: bytes | None = None,
    payees_mapping: list[tuple[str, str]] | None = None,
    categories_mapping: dict[str, str] | None = None,
) -> None:
    html_files = unzip_group(files, password)
    ofx_data = []

    try:
        for idx, f in enumerate(html_files):
            transactions = extract_transactions(f)
            for txn in transactions:
                payee = resolve_payee(txn["details"], payees_mapping)
                txn["payee"] = payee
                txn["category"] = resolve_category(payee, categories_mapping)

            start_balance, end_balance = extract_balances(f)

            info = {"name": files[idx]["account"]}
            ofx_data.append(
                {
                    "info": info,
                    "transactions": transactions,
                    "start_balance": start_balance,
                    "end_balance": end_balance,
                }
            )

        # debug print
        for entry in ofx_data:
            logger.info(
                ">>> %s (start: %s end: %s)",
                entry['info']['name'],
                entry['start_balance'],
                entry['end_balance'],
            )
            # for t in entry["transactions"]:
            #     logger.debug("   %s", t)

        write_ofx_file(ofx_data, ofx_path / month)

    finally:
        delete_files(html_files)
