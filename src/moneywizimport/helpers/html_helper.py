"""Helpers for extracting data from statement HTML files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import html

from moneywizimport.helpers.conversion_helper import parse_datetime, parse_float_safe, parse_amount_currency
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
    except Exception:
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
    except Exception:
        logger.exception("Failed to read IBAN from %s", html_file)
        raise


def read_account_currency(html_file: Path) -> str | None:
    """Extract account currency from ``html_file``."""

    try:
        document = _parse_html(html_file)
        values = document.xpath(
            "//tr/td/span[contains(text(),'Valuta contului')]/../following-sibling::td/span/text()"
        )
        return values[0].strip() if values else None
    except Exception:
        logger.exception("Failed to read account currency from %s", html_file)
        raise


def extract_balances(html_file: Path) -> tuple[float | None, float | None]:
    """Extract starting and ending balances from ``html_file``."""

    try:
        document = _parse_html(html_file)

        def find_value(label: str) -> float | None:
            cell = document.xpath(f'//td[normalize-space()="{label}"]/following-sibling::td[1]')
            return parse_float_safe(cell[0].text_content().strip())

        start = find_value("Soldul la inceputul perioadei :")
        end = find_value("Soldul la sfirsitul perioadei :")
        return start, end
    except Exception:
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

        date_time = parse_datetime(columns[1].text_content())
        amount = parse_float_safe(columns[4].text_content())

        details = columns[2].text_content().strip()
        account_currency = read_account_currency(html_file)

        foreign_amount, currency = parse_amount_currency(columns[3].text_content(), account_currency)
        fee = parse_float_safe(columns[5].text_content().strip())

        exchange_rate = (
            round(abs(float(amount) / float(foreign_amount)), 6)
            if currency != account_currency and foreign_amount
            else None
        )

        transactions.append(
            StatementTransaction(
                date_time=date_time,
                details=details,
                amount=amount,
                currency=currency,
                foreign_amount=foreign_amount,
                exchange_rate=exchange_rate,
                fee = None if not fee or fee == 0.0 else fee
            )
        )

    return transactions

