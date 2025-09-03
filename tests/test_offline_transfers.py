from datetime import datetime

from moneywizimport.core.statement import add_offline_transactions
from moneywizimport.model.ofx_models import OfxInfo, OfxReport, Transaction, TransactionType
from moneywizimport.model.provider_config import OfflineAccount


def test_add_offline_transactions_mirrors_transfer_and_skips_fee() -> None:
    transfer = Transaction(
        date_time=datetime(2025, 2, 1, 12, 0),
        details="Transfer to REVOLUT",
        amount=-50.0,
    )
    fee = Transaction(
        date_time=datetime(2025, 2, 1, 12, 5),
        details="REVOLUT fee",
        amount=-1.5,
        type=TransactionType.FEE,
    )
    report = OfxReport(
        info=OfxInfo(provider="Bank", account="Main", currency="USD"),
        transactions=[transfer, fee],
        start_balance=None,
        end_balance=None,
    )
    offline_accounts = [OfflineAccount(name="Revolut", match=["REVOLUT"])]

    results = add_offline_transactions([report], offline_accounts)

    assert transfer.details == "Revolut"
    assert transfer.type == TransactionType.INTRN_XFER

    offline_report = next(r for r in results if r.info.account == "Revolut")
    assert offline_report.info.provider == "OFFLINE"
    assert len(offline_report.transactions) == 1

    mirrored = offline_report.transactions[0]
    assert mirrored.amount == 50.0
    assert mirrored.type == TransactionType.INTRN_XFER
