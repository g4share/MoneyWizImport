from pathlib import Path
from datetime import datetime
from typing import Any

from lxml import html


def read_statement_date(html_file: Path) -> str:
    """Return the statement date from ``html_file`` in ``DD-MM-YYYY`` format."""
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))
    return doc.xpath(
        "normalize-space(//span[contains(., 'Situatia la data de')]/ancestor::td/following-sibling::td[1]//text())"
    )


def read_iban(html_file: Path) -> str:
    """Return the IBAN value from the statement HTML file."""
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))
    return doc.xpath(
        "normalize-space(//span[contains(., 'IBAN')]/ancestor::td/following-sibling::td[1]//text())"
    )


def extract_balances(html_file: Path) -> tuple[str, str]:
    """Extract starting and ending balances from ``html_file``."""
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))

    def find_value(label: str) -> str:
        td = doc.xpath(f'//td[normalize-space()="{label}"]/following-sibling::td[1]')
        return td[0].text_content().strip() if td else "?"

    start = find_value("Soldul la inceputul perioadei :")
    end = find_value("Soldul la sfirsitul perioadei :")
    return start, end


def extract_transactions(html_file: Path) -> list[dict[str, Any]]:
    """Parse all transaction rows from ``html_file``."""
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))
    rows = doc.xpath("//table//tr[td and count(td)=7]")[1:]
    transactions: list[dict[str, Any]] = []

    for row in rows:
        cols = row.xpath("./td")
        if len(cols) != 7:
            continue

        raw_datetime = cols[1].text_content().strip()
        details = cols[2].text_content().strip()
        amount_raw = cols[3].text_content().strip()
        amount_mdl = cols[4].text_content().strip()
        fee = cols[5].text_content().strip()

        if not raw_datetime or not amount_raw:
            continue

        parts = raw_datetime.split()
        date = parts[0]
        time = parts[1] if len(parts) > 1 else ""

        try:
            date_iso = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            continue

        amount_parts = amount_raw.split()
        foreign_amount = amount_parts[0].replace(",", ".")
        currency = amount_parts[1] if len(amount_parts) > 1 else "MDL"
        mdl_amount = amount_mdl.replace(",", ".")

        if currency != "MDL":
            try:
                exchange_rate = round(abs(float(mdl_amount)) / abs(float(foreign_amount)), 6)
            except ZeroDivisionError:
                exchange_rate = None
        else:
            foreign_amount = ""
            exchange_rate = None

        transactions.append(
            {
                "date": date_iso,
                "time": time,
                "details": details,
                "amount": mdl_amount,
                "currency": currency,
                "foreign_amount": foreign_amount,
                "exchange_rate": exchange_rate,
                "fee": fee,
            }
        )

    return transactions
