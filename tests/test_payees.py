from moneywizimport.core.statement import _resolve_payee
from moneywizimport.model.payee_mapping import PayeeRule


def test_resolve_payee_matches_regex_anywhere_case_insensitive() -> None:
    rules = [PayeeRule(match=r"itunes|apple\.com", name="Apple Services")]

    payee = _resolve_payee("Payment to APPLE.COM/BILL", rules)

    assert payee == "Apple Services"
