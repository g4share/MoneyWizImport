import datetime
import re

from moneywizimport.helpers.conversion_helper import parse_datetime, parse_float_safe
from moneywizimport.helpers.html_helper import read_by_xpath, read_elements_by_xpath
from moneywizimport.model import StatementTransaction
from moneywizimport.resolvers.BaseResolver import BaseResolver


class MaibHtmlResolver(BaseResolver):
    _XPATH_BALANCE_START = "//td/font[contains(., 'Soldul initial:')]/ancestor::td/following-sibling::td[1]"
    _XPATH_BALANCE_END = "//td/font[contains(., 'Soldul final:')]/ancestor::td/following-sibling::td[1]"

    _XPATH_CURRENCY = "//td/font/b[contains(., 'Valuta:')]/ancestor::td/following-sibling::td[1]"

    _XPATH_DATE = "//td/font/b[contains(., 'Perioada')]"
    _DATE_RE = re.compile(r"(\d{2}-\d{2}-\d{4})")

    _XPATH_IBAN = "//td/font[contains(., 'Contul #:')]/ancestor::td/following-sibling::td[1]"
    _IBAN_PREFIX = "MD34AG0000000"

    _XPATH_TRANSACTIONS = (
        "//table[.//td and count(.//td)=7 and not(.//strong)]"
        "[following::font[contains(., 'Cardul #')]"
        " or preceding::font[contains(., 'Cardul #')]]"
    )

    def resolve_balances(self) -> tuple[float | None, float | None]:
        start_text = read_by_xpath(self.file_path, self._XPATH_BALANCE_START)
        end_text = read_by_xpath(self.file_path, self._XPATH_BALANCE_END)

        start_balance = parse_float_safe(start_text)
        end_balance = parse_float_safe(end_text)

        return start_balance, end_balance


    def resolve_date(self) -> datetime.date:
        text = read_by_xpath(self.file_path, self._XPATH_DATE)
        matches = self._DATE_RE.findall(text)
        if not matches:
            raise ValueError(f"No date found in text: {text}")
        end_date_str = matches[-1]
        parsed = datetime.datetime.strptime(end_date_str, "%d-%m-%Y").date()
        return datetime.date(parsed.year, parsed.month, 1)

    def resolve_currency(self) -> str:
        currency = read_by_xpath(self.file_path, self._XPATH_CURRENCY).strip()
        if not currency:
            raise ValueError("Currency not found in statement")
        return currency

    def resolve_iban(self) -> str:
        account_number = read_by_xpath(self.file_path, self._XPATH_IBAN).strip()
        if not account_number:
            raise ValueError("Account number not found in statement")
        return f"{self._IBAN_PREFIX}{account_number}"

    def resolve_transactions(self) -> list[StatementTransaction]:
        rows = read_elements_by_xpath(self.file_path, self._XPATH_TRANSACTIONS)
        txns: list[StatementTransaction] = []

        for row in rows:
            tds = row.xpath(".//td")
            if len(tds) != 7:
                continue

            posted = parse_datetime(tds[0].text_content())
            if posted is None:
                raise ValueError(f"Could not parse transaction date: {tds[0].text_content()!r}")
            details = tds[3].text_content().strip()
            currency = tds[4].text_content().strip() or None
            foreign_amount = parse_float_safe(tds[5].text_content())
            amount = parse_float_safe(tds[6].text_content())

            txns.append(
                StatementTransaction(
                    date_time=posted,
                    details=details,
                    amount=amount,
                    currency=currency,
                    foreign_amount=foreign_amount,
                    exchange_rate=None,
                    fee=None,
                )
            )

        return txns
