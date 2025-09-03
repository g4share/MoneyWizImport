import datetime
import logging
import re
from pathlib import Path

import pdfplumber
from pdfminer.high_level import extract_text

from moneywizimport.helpers.conversion_helper import parse_datetime, parse_float_safe
from moneywizimport.model import StatementTransaction
from moneywizimport.resolvers.BaseResolver import BaseResolver

logger = logging.getLogger(__name__)

_TRANSACTION_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_NUMERIC_TOKEN_RE = re.compile(r"^[+-]?[\d.,]+$")
_TOKEN_MERGE_GAP = 3.0  # max distance (points) between consecutive tokens to merge them


class MaibPdfResolver(BaseResolver):

    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path)
        self.text = extract_text(file_path)

    def resolve_balances(self) -> tuple[float | None, float | None]:
        with pdfplumber.open(self.file_path) as pdf:
            rows = pdf.pages[0].extract_tables()[0]

            def _find(label: str) -> float | None:
                for r in rows:
                    if r and r[0] and label in r[0].lower():
                        return parse_float_safe(r[1] or r[2], default=None)
                return None

            return _find("inițial"), _find("final")

    def resolve_date(self) -> datetime.date:
        match = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*-", self.text)
        if not match:
            raise ValueError("Cannot locate statement start date")
        try:
            return datetime.datetime.strptime(match.group(1), "%d.%m.%Y").date()
        except ValueError:
            logger.debug("Cannot parse statement start date: %s", match.group(1))
            raise

    def resolve_currency(self) -> str:
        match = re.search(r"Valuta contului:\s*([A-Z]{3})", self.text)
        if not match:
            raise ValueError("Currency not found in statement")
        return match.group(1)

    def resolve_iban(self) -> str:
        match = re.search(r"Cod IBAN:\s*([A-Z0-9]+)", self.text)
        if not match:
            raise ValueError("IBAN not found in statement")
        return match.group(1)

    def resolve_transactions(self) -> list[StatementTransaction]:

        transactions: list[StatementTransaction] = []
        minute = 0  # monotonically increasing; per-day reset can be added later

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                for transaction_line in _extract_transactions_line(page.extract_words()):
                    t = _to_statement_transaction(transaction_line, minute)
                    transactions.append(t)
                    minute += 1

        return transactions

def _normalize(amount: str | None) -> str:
    return ((amount or "")
            .replace("\xa0", " ")
            .replace(" ", "")
            .replace(",", "."))


def _merge_tokens(line: list[dict], gap: float | None) -> list[str]:
    """Merge tokens within a line. If gap=None, merge all into one string."""
    if not line:
        return []
    words = [line[0]["text"]]
    prev = line[0]
    for w in line[1:]:
        if gap is None or (w["x0"] - prev["x1"]) < gap:
            words[-1] += f" {w['text']}"
        else:
            words.append(w["text"])
        prev = w
    return words


def _construct_transaction_line(lines: list[list[dict]]) -> list[str]:
    """Merge tokens in the first line by visual gap; append all other lines to description."""
    if not lines:
        return []

    primary = _merge_tokens(lines[0], _TOKEN_MERGE_GAP)

    # Merge and append continuation lines to description (column index 2)
    for line in lines[1:]:
        extras = _merge_tokens(line, None)
        if len(primary) > 2 and extras:
            primary[2] += " " + " ".join(extras)

    # Normalize to 8 fields (insert fee=0.00 if missing)
    if len(primary) == 7:
        primary.insert(-1, "0.00")

    return primary


def _handle_transaction_block(block: list[list[dict]]) -> list[str]:
    """Process a block of lines belonging to one transaction and return merged tokens."""
    if not block:
        return []

    result: list[list[dict]] = []
    description_x = block[0][2]["x0"] if len(block[0]) > 2 else None

    for line in block:
        first_x = line[0]["x0"]
        if line is block[0] or (description_x is not None and first_x == description_x):
            result.append(line)

    return _construct_transaction_line(result)


def _extract_transactions_line(words: list[dict]) -> list[list[str]]:
    """Group tokens by Y position, detect transaction blocks, and return all merged transaction lines."""
    def _is_transaction_line(tokens: list[dict]) -> bool:
        return bool(_TRANSACTION_LINE_RE.match(tokens[0]["text"]))

    # Group tokens by vertical position
    lines: dict[float, list[dict]] = {}
    for w in words:
        key = round(w["top"], 1)
        lines.setdefault(key, []).append(w)

    sorted_lines = [tokens for _, tokens in sorted(lines.items(), key=lambda kv: kv[0])]
    for tokens in sorted_lines:
        tokens.sort(key=lambda t: t["x0"])

    transactions: list[list[str]] = []
    i = 0
    while i < len(sorted_lines):
        if _is_transaction_line(sorted_lines[i]):
            block = [sorted_lines[i]]
            i += 1
            while i < len(sorted_lines) and not _is_transaction_line(sorted_lines[i]):
                block.append(sorted_lines[i])
                i += 1
            merged = _handle_transaction_block(block)
            if merged:
                transactions.append(merged)
        else:
            i += 1

    return transactions


def _to_statement_transaction(fields: list[str], minutes: int) -> StatementTransaction:
    """Convert parsed transaction line to StatementTransaction and add minute offset."""
    if len(fields) < 8:
        raise ValueError(f"Incomplete transaction line: {fields}")

    foreign_amount = parse_float_safe(fields[3]) or 0.0
    amount = parse_float_safe(fields[5]) or 0.0

    # Align amount sign with foreign_amount
    if (foreign_amount < 0) != (amount < 0):
        amount = -amount

    dt = parse_datetime(fields[0])
    if dt is None:
        raise ValueError(f"Could not parse transaction date: {fields[0]!r}")
    dt = dt + datetime.timedelta(minutes=minutes)

    return StatementTransaction(
        date_time=dt,
        details=fields[2],
        amount=amount,
        foreign_amount=foreign_amount,
        currency=fields[4],
        exchange_rate=None,
        fee=parse_float_safe(fields[6]) or 0.0,
    )
