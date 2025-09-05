from pathlib import Path
from lxml import html

def read_statement_date(html_file: Path) -> str:
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))

    return doc.xpath(
        "normalize-space(//span[contains(., 'Situatia la data de')]/ancestor::td/following-sibling::td[1]//text())"
    )

def read_iban(html_file: Path) -> str:
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))

    return doc.xpath(
        "normalize-space(//span[contains(., 'IBAN')]/ancestor::td/following-sibling::td[1]//text())"
    )

def extract_balances(html_file: Path) -> tuple[str, str]:
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))

    start = doc.xpath('//td[contains(text(), "Soldul la inceputul perioadei")]/following-sibling::td[1]')
    end = doc.xpath('//td[contains(text(), "Soldul la sfirsitul perioadei")]/following-sibling::td[1]')

    start_balance = start[0].text_content().strip() if start else "?"
    end_balance = end[0].text_content().strip() if end else "?"

    return start_balance, end_balance

def extract_transactions(html_file: Path) -> list[dict[str, str]]:
    doc = html.fromstring(html_file.read_text(encoding="utf-8"))

    rows = doc.xpath("//table//tr[td and count(td)=7]")[1:]
    transactions = []

    for row in rows:
        cols = row.xpath("./td")
        if len(cols) != 7:
            continue

        raw_datetime = cols[1].text_content().strip()  # ex: '07-06-2025 11:11:58'
        details = cols[2].text_content().strip()
        amount_raw = cols[3].text_content().strip()    # ex: "-1000.00 MDL"
        amount_mdl = cols[4].text_content().strip()    # ex: "-1000.00"
        fee = cols[5].text_content().strip()

        if not raw_datetime or not amount_raw:
            continue

        # split date and time
        parts = raw_datetime.split()
        date = parts[0]
        time = parts[1] if len(parts) > 1 else ""

        # format date to ISO
        day, month, year = date.split("-")
        date_iso = f"{year}-{month}-{day}"

        # split amount and currency
        amount_parts = amount_raw.split()
        amount = amount_parts[0]
        currency = amount_parts[1] if len(amount_parts) > 1 else "MDL"

        transactions.append({
            "date": date_iso,
            "time": time,
            "details": details,
            "amount": amount,
            "currency": currency,
            "amount_mdl": amount_mdl,
            "fee": fee,
        })

    return transactions