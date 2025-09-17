from pathlib import Path
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

from pathlib import Path

def collect_statement_files(statement_dir: Path, bank_patterns: dict) -> list[dict]:
    def _match_file(file: Path):
        for bank, data in bank_patterns.items():
            m = data["filter"].match(file.name)
            if not m:
                continue

            year, month, iban = m.group("year"), m.group("month"), m.group("iban")
            month_key = f"{year}-{month}"

            account_name = "UNKNOWN"
            for pattern, acc_name in data["accounts"]:
                if pattern.fullmatch(iban):
                    account_name = acc_name
                    break

            return month_key, bank, account_name, data.get("password")

        return None

    grouped = defaultdict(list)

    for file in statement_dir.iterdir():
        if not file.is_file():
            continue
        match = _match_file(file)
        if not match:
            continue

        month_key, bank, account_name, password = match
        grouped[month_key].append({
            "bank": bank,
            "account": account_name,
            "password": password,
            "file": file,
        })

    return [
        {"month": month, "items": items}
        for month, items in sorted(grouped.items(), key=lambda x: x[0])
    ]

def delete_files(files: list[Path]) -> None:
    """Remove all files from ``files`` ignoring individual errors."""

    for file_path in files:
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError as exc:
            logger.warning("Failed to delete %s: %s", file_path, exc)
