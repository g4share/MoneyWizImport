import re
from pathlib import Path

from pdfminer.high_level import extract_text


def extract_pdf_value(pdf_path: Path, label: str) -> str | None:
    text = extract_text(pdf_path)
    pattern = re.compile(rf"{re.escape(label)}\s*([^\n]+)")
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _extract_value(pdf_path: Path, label: str) -> str | None:
    """Helper to extract a labelled value from a PDF."""

    return extract_pdf_value(pdf_path, label)


def read_pdf_start_balance(pdf_path: Path) -> str | None:
    return _extract_value(pdf_path, "Sold inițial:")


def read_pdf_end_balance(pdf_path: Path) -> str | None:
    return _extract_value(pdf_path, "Sold final:")
