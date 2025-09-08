import argparse
from pathlib import Path

from moneywizimport.core import prepare_archives
from moneywizimport.helpers import ConfigHelper


def main() -> None:
    """Entry point for normalising statement archives."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()

    statement_dir = Path(config["statement_dir"]).expanduser()
    password = cfg.get_zip_password()

    prepare_archives(statement_dir=statement_dir, password=password)

if __name__ == "__main__":
    main()
