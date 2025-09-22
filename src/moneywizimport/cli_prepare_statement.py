"""CLI for normalising provider statement archives."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from moneywizimport.core import prepare_archives
from moneywizimport.helpers import ConfigHelper
from moneywizimport.logging_setup import setup_logging


def main() -> None:
    """Entry point for normalising statement archives."""

    setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    config_helper = ConfigHelper(Path(args.config))
    
    config_statements = config_helper.get_config_statements()
    logger.info("Found %d statements in config", len(config_statements))
    for config_statement in config_statements:
        config_statement.log(logger)

    prepared_dir, _ = config_helper.get_statement_dirs()
    prepare_archives(config_statements, prepared_dir)


if __name__ == "__main__":
    main()

