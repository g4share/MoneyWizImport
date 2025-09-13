from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moneywizimport.helpers.fs_helper import collect_statement_files


def test_collects_all_banks(tmp_path):
    # Create dummy statement files for two banks
    (tmp_path / "VB_2024-05-01_ACC1.zip").touch()
    (tmp_path / "MAIB_2024-05-15_ACC2.zip").touch()
    (tmp_path / "VB_2024-06-01_ACC1.zip").touch()

    banks = [
        {
            "name": "Bank A",
            "statement_dir": str(tmp_path),
            "filter": "VB_*.zip",
            "accounts": [{"name": "Account 1", "iban": "ACC1"}],
        },
        {
            "name": "Bank B",
            "statement_dir": str(tmp_path),
            "filter": "MAIB_*.zip",
            "accounts": [{"name": "Account 2", "iban": "ACC2"}],
        },
    ]

    regex = r"^([A-Za-z]+)_(\d{4})-(\d{2})-\d{2}_(.+)\.zip$"
    groups = collect_statement_files(banks, regex)

    assert [g["month"] for g in groups] == ["2024-05", "2024-06"]
    assert len(groups[0]["files"]) == 2  # both banks in May
    assert len(groups[1]["files"]) == 1  # only VB in June
