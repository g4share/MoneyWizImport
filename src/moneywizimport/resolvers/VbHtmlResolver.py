import datetime

from moneywizimport.helpers.conversion_helper import parse_amount_currency, parse_datetime, parse_float_safe
from moneywizimport.helpers.html_helper import read_by_xpath, read_elements_by_xpath
from moneywizimport.model import StatementTransaction
from moneywizimport.resolvers.BaseResolver import BaseResolver


class VbHtmlResolver(BaseResolver):
    _XPATH_BALANCE_START = '//td[normalize-space()="Soldul la inceputul perioadei :"]/following-sibling::td[1]'
    _XPATH_BALANCE_END = '//td[normalize-space()="Soldul la sfirsitul perioadei :"]/following-sibling::td[1]'

    _XPATH_DATE = "//span[contains(., 'Situatia la data de')]/ancestor::td/following-sibling::td[1]//text()"
    _XPATH_CURRENCY = "//tr/td/span[contains(text(),'Valuta contului')]/../following-sibling::td/span/text()"
    _XPATH_IBAN = "//span[contains(., 'IBAN')]/ancestor::td/following-sibling::td[1]//text()"

    _XPATH_TRANSACTIONS = "//table//tr[td and count(td)=7]"

    def resolve_balances(self) -> tuple[float | None, float | None]:
        start_text = read_by_xpath(self.file_path, self._XPATH_BALANCE_START)
        end_text = read_by_xpath(self.file_path, self._XPATH_BALANCE_END)

        start = parse_float_safe(start_text.strip()) if start_text else None
        end = parse_float_safe(end_text.strip()) if end_text else None

        return start, end

    def resolve_date(self) -> datetime.date:
        date_str = read_by_xpath(self.file_path, self._XPATH_DATE)
        date = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()

        return date.replace(day=1) - datetime.timedelta(days=1)

    def resolve_currency(self) -> str:
        currency = read_by_xpath(self.file_path, self._XPATH_CURRENCY).strip()
        if not currency:
            raise ValueError("Currency not found in statement")
        return currency

    def resolve_iban(self) -> str:
        return read_by_xpath(self.file_path, self._XPATH_IBAN)

    def resolve_transactions(self) -> list[StatementTransaction]:
        rows = read_elements_by_xpath(self.file_path, self._XPATH_TRANSACTIONS)[1:]
        transactions: list[StatementTransaction] = []

        for row in rows:
            columns = row.xpath("./td")
            if len(columns) != 7:
                continue

            date_time = parse_datetime(columns[1].text_content())
            if date_time is None:
                raise ValueError(f"Could not parse transaction date: {columns[1].text_content()!r}")
            details = columns[2].text_content().strip()
            amount = parse_float_safe(columns[4].text_content())

            foreign_amount, currency = parse_amount_currency(columns[3].text_content())
            fee = parse_float_safe(columns[5].text_content().strip())
            transactions.append(
                StatementTransaction(
                    date_time=date_time,
                    details=details,
                    amount=amount,
                    foreign_amount=foreign_amount,
                    currency=currency,
                    exchange_rate=None,
                    fee=None if not fee or fee == 0.0 else fee,
                )
            )

        return transactions
