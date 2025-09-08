"""CLI utility to normalize statement archives."""

import argparse
import logging
from pathlib import Path

from moneywizimport.core import prepare_archives
from moneywizimport.helpers import ConfigHelper

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for the ``prepare-statement`` console script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()

    statement_dir = Path(config["statement_dir"]).expanduser()
    password = cfg.get_zip_password()

    logger.info("Preparing statement archives in %s", statement_dir)
    prepare_archives(statement_dir=statement_dir, password=password)

if __name__ == "__main__":
    main()
