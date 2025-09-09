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

    for bank in cfg.load_banks():
        statement_dir = Path(bank["statement_dir"]).expanduser()
        password = bank.get("zip_password")
### CODEX: add a function in config helper an use it to return password
        password_bytes = (
            password.encode("utf-8") if isinstance(password, str) and password else None
        )
        prepare_archives(statement_dir=statement_dir, password=password_bytes)

if __name__ == "__main__":
    main()
