from datetime import datetime

from moneywizimport.core.statement import calculate_exchange_rate
from moneywizimport.model.ofx_models import StatementTransaction


def test_calculate_exchange_rate_sets_rate_and_skips_same_currency() -> None:
    fx_transaction = StatementTransaction(
        date_time=datetime(2025, 1, 1),
        details="USD purchase",
        amount=-100.0,
        currency="USD",
        foreign_amount=-110.0,
        exchange_rate=None,
        fee=None,
    )
    same_currency_transaction = StatementTransaction(
        date_time=datetime(2025, 1, 2),
        details="EUR purchase",
        amount=-50.0,
        currency="EUR",
        foreign_amount=-50.0,
        exchange_rate=None,
        fee=None,
    )

    calculate_exchange_rate([fx_transaction, same_currency_transaction], account_currency="EUR")

    assert fx_transaction.exchange_rate == 0.909091
    assert same_currency_transaction.exchange_rate is None
