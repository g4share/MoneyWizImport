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

    cfg = ConfigHelper(Path(args.config))
    config_statements = cfg.get_config_statements()
    logger.info("Found %d Statements in config", len(config_statements))
    for config_statement in config_statements:
        config_statement.log(logger)

    prepared_dir = cfg.get_prepared_dir()
    prepare_archives(config_statements, prepared_dir)


if __name__ == "__main__":
    main()
