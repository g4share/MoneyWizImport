from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moneywizimport.helpers.fs_helper import collect_statement_files
from moneywizimport.model.bank_config import Account, BankPattern


def test_collects_all_banks(tmp_path):
    (tmp_path / "VB_2024-05-01_ACC1.zip").touch()
    (tmp_path / "MAIB_2024-05-15_ACC2.zip").touch()
    (tmp_path / "VB_2024-06-01_ACC1.zip").touch()
    (tmp_path / "UNMATCHED.zip").touch()

    vb_regex = re.compile(r"^VB_(?P<year>\d{4})-(?P<month>\d{2})-\d{2}_(?P<iban>.+)\.zip$")
    maib_regex = re.compile(r"^MAIB_(?P<year>\d{4})-(?P<month>\d{2})-\d{2}_(?P<iban>.+)\.zip$")

    bank_patterns = [
        BankPattern(
            name="Bank A",
            filter=vb_regex,
            accounts=[Account(name="Account 1", iban="ACC1")],
            zip_password=None,
        ),
        BankPattern(
            name="Bank B",
            filter=maib_regex,
            accounts=[Account(name="Account 2", iban="ACC2")],
            zip_password=None,
        ),
    ]

    groups = collect_statement_files(tmp_path, bank_patterns)

    assert [group.month for group in groups] == ["2024-05", "2024-06"]
    may_files = sorted((item.bank, item.account) for item in groups[0].items)
    june_files = sorted((item.bank, item.account) for item in groups[1].items)

    assert may_files == [("Bank A", "Account 1"), ("Bank B", "Account 2")]
    assert june_files == [("Bank A", "Account 1")]

