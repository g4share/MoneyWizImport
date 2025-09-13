from pathlib import Path
import logging
import re
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

def collect_statement_files(banks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group statement archives by month.

    Parameters
    ----------
    banks:
        Configuration describing how to locate and label account files. Each
        bank may define either a top-level ``filter`` regex or a ``files`` list
        where each item provides its own ``filter`` regex.

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries of the form ``{"month": str, "files": list}``.
    """

    grouped = defaultdict(list)
    for bank in banks:
        bank_name = bank["name"]
        statement_dir = Path(bank["statement_dir"]).expanduser()
        accounts = bank.get("accounts", [])
        password = bank.get("zip_password")
        password_bytes = (
            password.encode("utf-8") if isinstance(password, str) and password else None
        )
        iban_map = {acc["iban"]: acc["name"] for acc in accounts}

        file_patterns = [
            fconf["filter"] for fconf in bank.get("files", [])
        ] or [bank["filter"]]

        for pattern in file_patterns:
            regex = re.compile(pattern, re.IGNORECASE)

            for file in statement_dir.iterdir():
                if not file.is_file():
                    continue
                m = regex.match(file.name)
                if not m:
                    continue
                group_dict = m.groupdict()
                year = group_dict.get("year", m.group(1))
                month = group_dict.get("month", m.group(2))
                iban_token = group_dict.get("iban", m.group(3))
                month_key = f"{year}-{month}"

                account_name = "UNKNOWN"
                for iban, acc_name in iban_map.items():
                    if iban_token.lower() == iban.lower():
                        account_name = acc_name
                        break

                grouped[month_key].append(
                    {
                        "file": file.name,
                        "path": str(file.resolve()),
                        "bank": bank_name,
                        "account": account_name,
                        "password": password_bytes,
                    }
                )

    result = []
    for month in sorted(grouped.keys()):
        files = sorted(grouped[month], key=lambda x: x["file"])
        result.append({"month": month, "files": files})

    return result


def delete_files(files: list[Path]) -> None:
    """Remove all files from ``files`` ignoring individual errors."""

    for file_path in files:
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError as exc:
            logger.warning("Failed to delete %s: %s", file_path, exc)
