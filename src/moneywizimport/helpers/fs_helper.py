from pathlib import Path
import logging
import re
from collections import defaultdict
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _compile_bank_patterns(
    banks: list[dict[str, Any]],
) -> tuple[Optional[Path], list[dict[str, Any]]]:
    """Create a collection of compiled regex patterns for all banks.

    Returns the statement directory (shared by all banks) and a list of
    dictionaries describing each compiled pattern together with the
    information needed during matching.
    """

    if not banks:
        return None, []

    statement_dir = Path(banks[0]["statement_dir"]).expanduser()
    regex_collection: list[dict[str, Any]] = []

    for bank in banks:
        bank_name = bank["name"]
        accounts = bank.get("accounts", [])
        password = bank.get("zip_password")
        password_bytes = (
            password.encode("utf-8") if isinstance(password, str) and password else None
        )
        iban_map = {acc["iban"]: acc["name"] for acc in accounts}

        patterns = [fconf["filter"] for fconf in bank.get("files", [])] or [bank["filter"]]
        for pattern in patterns:
            regex_collection.append(
                {
                    "regex": re.compile(pattern, re.IGNORECASE),
                    "bank": bank_name,
                    "iban_map": iban_map,
                    "password": password_bytes,
                }
            )

    return statement_dir, regex_collection


def _match_file(
    file: Path, regex_collection: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Return file information if ``file`` matches any bank regex."""

    for info in regex_collection:
        m = info["regex"].match(file.name)
        if not m:
            continue
        group_dict = m.groupdict()
        year = group_dict.get("year", m.group(1))
        month = group_dict.get("month", m.group(2))
        iban_token = group_dict.get("iban", m.group(3))

        account_name = "UNKNOWN"
        for iban, acc_name in info["iban_map"].items():
            if iban_token.lower() == iban.lower():
                account_name = acc_name
                break

        return {
            "file": file.name,
            "path": str(file.resolve()),
            "bank": info["bank"],
            "account": account_name,
            "password": info["password"],
            "month": f"{year}-{month}",
        }
    return None


def _group_files_by_month(
    statement_dir: Path, regex_collection: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Iterate over statement directory and group matching files by month."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for file in statement_dir.iterdir():
        if not file.is_file():
            continue
        info = _match_file(file, regex_collection)
        if info:
            month_key = info.pop("month")
            grouped[month_key].append(info)
    return grouped


def collect_statement_files(banks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group statement archives by month."""

    statement_dir, regex_collection = _compile_bank_patterns(banks)
    if statement_dir is None:
        return []

    grouped = _group_files_by_month(statement_dir, regex_collection)

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
