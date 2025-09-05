from pathlib import Path
import re
from collections import defaultdict
from typing import List, Dict, Any

RE_VB = re.compile(r"^VB_(\d{4})-(\d{2})-\d{2}_(.+)\.zip$", re.IGNORECASE)

def collect_statement_files(statement_dir: Path, bank_sets: list[dict]) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)

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
                if iban_token.lower() == iban.lower():
                    account_name = acc_name
                    break

            grouped[month_key].append({
                "file": file.name,
                "path": str(file.resolve()),  # <== read path
                "bank": bank_name,
                "account": account_name
            })

    result = []
    for month in sorted(grouped.keys()):
        files = sorted(grouped[month], key=lambda x: x["file"])
        result.append({
            "month": month,
            "files": files
        })

    return result

def delete_files(files: list[Path]) -> None:
    for f in files:
        try:
            if f.exists():
                f.unlink()
        except OSError:
            pass  # suppress errors silently for now