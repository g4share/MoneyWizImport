import argparse
from pathlib import Path
from moneywizimport.helpers.config_helper import ConfigHelper
from moneywizimport.helpers.fs_helper import collect_statement_files

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    parser.add_argument("--olx", default="src/moneywizimport/olx-config.yaml")
    args = parser.parse_args()

    config = ConfigHelper(Path(args.config)).load_config()
    statement_dir = Path(config["statement_dir"])
    olx_config_path = Path(args.olx)

    bank_sets = ConfigHelper.load_olx_bank_sets(olx_config_path)
    results = collect_statement_files(statement_dir, bank_sets)

    current_month = None
    for item in results:
        if item["month"] != current_month:
            if current_month is not None:
                print()
            current_month = item["month"]
            print(current_month)

        print(f"  {item['file']} : {item['account']}")

if __name__ == "__main__":
    main()
