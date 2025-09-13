from pathlib import Path
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


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

            return bank, account_name, month_key
        return None

    groups: dict[str, list[dict]] = defaultdict(list)

    for file in statement_dir.iterdir():
        if not file.is_file():
            continue

        match = _match_file(file)
        if not match:
            continue

        bank, account, month_key = match

        groups[month_key].append({
            "file": file.name,
            "path": str(file),
            "bank": bank,
            "account": account,
        })

    return [
        {"month": month, "files": files}
        for month, files in sorted(groups.items())
    ]

def delete_files(files: list[Path]) -> None:
    """Remove all files from ``files`` ignoring individual errors."""

    for file_path in files:
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError as exc:
            logger.warning("Failed to delete %s: %s", file_path, exc)
