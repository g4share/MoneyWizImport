import argparse
from pathlib import Path
from moneywizimport.helpers import ConfigHelper, config_helper
from moneywizimport.core import prepareArchives

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()

    statement_dir = Path(config["statement_dir"]).expanduser()
    password = config_helper.get_zip_password()

    prepareArchives(statement_dir=statement_dir, password=password)

if __name__ == "__main__":
    main()
