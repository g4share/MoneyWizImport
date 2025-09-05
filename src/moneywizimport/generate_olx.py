import argparse
from pathlib import Path
from moneywizimport.helpers.config_helper import ConfigHelper
from moneywizimport.helpers.fs_helper import collect_statement_files
from moneywizimport.core.statement import generate_reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    parser.add_argument("--olx", default="src/moneywizimport/olx-config.yaml")
    args = parser.parse_args()

    ch = ConfigHelper(Path(args.config))
    config = ch.load_config()
    statement_dir = Path(config["statement_dir"])
    olx_config_path = Path(args.olx)

    bank_sets = ConfigHelper.load_olx_bank_sets(olx_config_path)
    groups = collect_statement_files(statement_dir, bank_sets)
    olx_path = Path(config["olx_dir"])

    '''
    current_month = None
    for group in groups:
        if group["month"] != current_month:
            if current_month is not None:
                print()
            current_month = group["month"]
            print(current_month)

        print(f"  {group['file']} : {group['account']}")
    '''
    password = ch.get_zip_password()
    generate_reports(olx_path, groups, password)


if __name__ == "__main__":
    main()
