from datetime import datetime
from pathlib import Path
from typing import List, Dict
import re
from typing import List, Tuple
from datetime import datetime

import tempfile, shutil
from moneywizimport.helpers import unzip, zip, unzip_group
from moneywizimport.helpers.fs_helper import delete_files
from moneywizimport.helpers.html_helper import extract_transactions, extract_balances
from moneywizimport.core.ofx_generator import write_ofx_file

from moneywizimport.helpers.html_helper import read_statement_date

def prepare_archives(statement_dir: Path, password: bytes | None = None):
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

def resolve_category(payee: str, categories_mapping: dict[str, str]) -> str:
    """
    Returns the full category path for a given payee from a provided mapping.
    If not found, returns ': UNKNOWN'.
    """
    return categories_mapping.get(payee.lower(), ": UNKNOWN")

def resolve_payee(description: str, rules: List[Tuple[str, str]]) -> str:
    """
    Matches a transaction description against regex rules to identify payee name.
    Matching is case-insensitive using re.IGNORECASE.
    """
    desc = description.strip()

    for pattern, label in rules:
        if re.search(pattern, desc, flags=re.IGNORECASE):
            return label

    return ": UNKNOWN"

def generate_reports(ofx_path: Path,
                     groups: List[Dict[str, list]],
                     password: bytes | None = None,
                     payees_mapping: list[tuple[str, str]] | None = None,
                     categories_mapping: dict[str, str] | None = None
) -> None:

    for group in groups:
        month = group["month"]
        files = group["files"]

        if datetime.strptime(month, "%Y-%m") >= datetime(2025, 2, 1):
            generate_report(ofx_path, files, month, password, payees_mapping, categories_mapping)

def generate_report(ofx_path: Path,
                    files: List[Dict[str, str]],
                    month: str,
                    password: bytes | None = None,
                    payees_mapping: list[tuple[str, str]] | None = None,
                    categories_mapping: dict[str, str] | None = None) -> None:
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
            ofx_data.append({
                "info": info,
                "transactions": transactions,
                "start_balance": start_balance,
                "end_balance": end_balance
            })

        # debug print
        for entry in ofx_data:
            print(f">>> {entry['info']['name']} (start: {entry['start_balance']} end: {entry['end_balance']})")
            #for t in entry["transactions"]:
            #    print(f"   {t}")

        write_ofx_file(ofx_data, ofx_path / month)

    finally:
        delete_files(html_files)
