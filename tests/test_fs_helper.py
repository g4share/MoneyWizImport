from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moneywizimport.helpers.fs_helper import collect_statement_files


def test_collects_all_banks(tmp_path):
    # Create dummy statement files for two banks
    (tmp_path / "VB_2024-05-01_ACC1.zip").touch()
    (tmp_path / "MAIB_2024-05-15_ACC2.zip").touch()
    (tmp_path / "VB_2024-06-01_ACC1.zip").touch()

    vb_regex = (
        r"^VB_(?P<year>\d{4})-(?P<month>\d{2})-\d{2}_(?P<iban>.+)\.zip$"
    )
    maib_regex = (
        r"^MAIB_(?P<year>\d{4})-(?P<month>\d{2})-\d{2}_(?P<iban>.+)\.zip$"
    )
    banks = [
        {
            "name": "Bank A",
            "statement_dir": str(tmp_path),
            "accounts": [{"name": "Account 1", "iban": "ACC1"}],
            "filter": vb_regex,
        },
        {
            "name": "Bank B",
            "accounts": [{"name": "Account 2", "iban": "ACC2"}],
            "filter": maib_regex,
        },
    ]

    groups = collect_statement_files(banks)

    assert [g["month"] for g in groups] == ["2024-05", "2024-06"]
    assert len(groups[0]["files"]) == 2  # both banks in May
    assert len(groups[1]["files"]) == 1  # only VB in June
