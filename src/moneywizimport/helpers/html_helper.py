"""Helpers for extracting data from statement HTML files."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from lxml import html

from moneywizimport.model.ofx_models import StatementTransaction

logger = logging.getLogger(__name__)


def _parse_html(html_file: Path):
    """Return an ``lxml`` document tree for ``html_file``."""

    text = html_file.read_text(encoding="utf-8", errors="replace")
    return html.fromstring(text)


def read_statement_date(html_file: Path) -> str:
    """Return the statement date from ``html_file`` in ``DD-MM-YYYY`` format."""

    try:
        document = _parse_html(html_file)
        return document.xpath(
            "normalize-space(//span[contains(., 'Situatia la data de')]/ancestor::td/"
            "following-sibling::td[1]//text())"
        )
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to read statement date from %s", html_file)
        raise


def read_iban(html_file: Path) -> str:
    """Return the IBAN value from the statement HTML file."""

    try:
        document = _parse_html(html_file)
        return document.xpath(
            "normalize-space(//span[contains(., 'IBAN')]/ancestor::td/"
            "following-sibling::td[1]//text())"
        )
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to read IBAN from %s", html_file)
        raise


def read_account_currency(html_file: Path) -> Optional[str]:
    """Extract account currency from ``html_file``."""

    try:
        document = _parse_html(html_file)
        values = document.xpath(
            "//tr/td/span[contains(text(),'Valuta contului')]/../following-sibling::td/span/text()"
        )
        return values[0].strip() if values else None
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to read account currency from %s", html_file)
        raise


def extract_balances(html_file: Path) -> tuple[str, str]:
    """Extract starting and ending balances from ``html_file``."""

    try:
        document = _parse_html(html_file)

        def find_value(label: str) -> str:
            cell = document.xpath(f'//td[normalize-space()="{label}"]/following-sibling::td[1]')
            return cell[0].text_content().strip() if cell else "?"

        start = find_value("Soldul la inceputul perioadei :")
        end = find_value("Soldul la sfirsitul perioadei :")
        return start, end
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to extract balances from %s", html_file)
        raise


def extract_transactions(html_file: Path) -> list[StatementTransaction]:
    """Parse all transaction rows from ``html_file`` into ``StatementTransaction`` objects."""

    document = _parse_html(html_file)
    rows = document.xpath("//table//tr[td and count(td)=7]")[1:]
    transactions: list[StatementTransaction] = []

    for row in rows:
        columns = row.xpath("./td")
        if len(columns) != 7:
            continue

        raw_datetime = columns[1].text_content().strip()
        details = columns[2].text_content().strip()
        amount_raw = columns[3].text_content().strip()
        amount_mdl = columns[4].text_content().strip()
        fee = columns[5].text_content().strip()

        if not raw_datetime or not amount_raw:
            continue

        parts = raw_datetime.split()
        date = parts[0]
        time_value = parts[1] if len(parts) > 1 else None

        try:
            iso_date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            continue

        amount_parts = amount_raw.split()
        foreign_amount = amount_parts[0].replace(",", ".")
        currency = amount_parts[1] if len(amount_parts) > 1 else "MDL"
        mdl_amount = amount_mdl.replace(",", ".")

        if currency != "MDL":
            try:
                exchange_rate: Optional[str] = str(
                    round(abs(float(mdl_amount)) / abs(float(foreign_amount)), 6)
                )
            except ZeroDivisionError:
                exchange_rate = None
        else:
            foreign_amount = None
            exchange_rate = None

        transactions.append(
            StatementTransaction(
                date=iso_date,
                time=time_value,
                details=details,
                amount=mdl_amount,
                currency=currency,
                foreign_amount=foreign_amount,
                exchange_rate=exchange_rate,
                fee=fee or None,
            )
        )

    return transactions

