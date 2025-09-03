import argparse
from pathlib import Path
from moneywizimport.helpers import ConfigHelper
from moneywizimport.core import prepareArchives

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()

    statement_dir = Path(config["statement_dir"]).expanduser()
    raw_pw = config.get("zip_password")
    password = raw_pw.encode("utf-8") if isinstance(raw_pw, str) and raw_pw != "" else None

    prepareArchives(statement_dir=statement_dir, password=password)

if __name__ == "__main__":
    main()
