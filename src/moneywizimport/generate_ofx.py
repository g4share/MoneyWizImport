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
    banks = cfg.load_banks()
    filename_regex = config["statement_regex"]
    groups = collect_statement_files(banks, filename_regex)
    ofx_path = Path(config["ofx_dir"])

    categories_mapping = cfg.load_category_mapping()
    payees_mapping = cfg.load_payees_mapping()

    generate_reports(ofx_path, groups, payees_mapping, categories_mapping)


if __name__ == "__main__":
    main()
