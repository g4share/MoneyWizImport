from datetime import datetime

from moneywizimport.core.ofx_generator import generate_ofx_file
from moneywizimport.model.ofx_models import OfxInfo, OfxReport, Transaction


def test_generate_ofx_file_renders_core_fields() -> None:
    transaction = Transaction(
        date_time=datetime(2025, 3, 1, 9, 30),
        details="Grocery",
        amount=-12.34,
        payee="Store",
    )
    report = OfxReport(
        info=OfxInfo(provider="TestBank", account="Main-123", currency="USD"),
        transactions=[transaction],
        start_balance=None,
        end_balance=None,
    )

    content = generate_ofx_file([report])

    assert "OFXHEADER:100" in content
    assert "<BANKID>TestBank" in content
    assert "<ACCTID>Main-123" in content
    assert "<TRNAMT>-12.34" in content
    assert "<NAME>Store" in content
