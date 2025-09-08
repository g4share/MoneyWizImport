"""Command line interface to generate OFX reports."""

import argparse
import logging
from pathlib import Path

from moneywizimport.core.statement import generate_reports
from moneywizimport.helpers.config_helper import ConfigHelper
from moneywizimport.helpers.fs_helper import collect_statement_files

logger = logging.getLogger(__name__)

def main() -> None:
    """Entry point for the ``generate-ofx`` console script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()
    statement_dir = Path(config["statement_dir"])

    bank_sets = cfg.load_ofx_bank_sets()

    groups = collect_statement_files(statement_dir, bank_sets)
    ofx_path = Path(config["ofx_dir"])
    password = cfg.get_zip_password()
    categories_mapping = cfg.load_category_mapping()

    payees_mapping = cfg.load_payees_mapping()
    logger.info("Generating OFX reports in %s", ofx_path)
    generate_reports(ofx_path, groups, password, payees_mapping, categories_mapping)


if __name__ == "__main__":
    main()
