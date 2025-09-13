import argparse
from pathlib import Path

from moneywizimport.core.statement import generate_reports
from moneywizimport.helpers.config_helper import ConfigHelper
from moneywizimport.helpers.fs_helper import collect_statement_files


def main() -> None:
    """Entry point for generating OFX files from statement archives."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()

    statement_dir = Path(config["statement_dir"])
    ofx_path = Path(config["ofx_dir"])

    bank_patterns = cfg.compile_bank_patterns()
    groups = collect_statement_files(statement_dir, bank_patterns)

    print_bank_patterns(bank_patterns)
 #   print_groups(groups)

    categories_mapping = cfg.load_category_mapping()
    payees_mapping = cfg.load_payees_mapping()

    generate_reports(ofx_path, groups, payees_mapping, categories_mapping)


if __name__ == "__main__":
    main()

def print_groups(groups: list[dict]) -> None:
    for group in groups:
        print(group["month"])
        for f in group["files"]:
            print(f"  - {f['file']:<45} {f['bank']:<20} {f['account']}")
        print()


def print_bank_patterns(bank_patterns: dict) -> None:
    for bank, data in bank_patterns.items():
        print(f"{bank}")
        print(f"  filter:   {data['filter'].pattern}")
        print(f"  password: {data['zip_password']}")
        for pattern, acc_name in data["accounts"]:
            print(f"  - {acc_name:15} → {pattern.pattern}")
        print()