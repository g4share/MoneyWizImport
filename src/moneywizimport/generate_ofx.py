import argparse
from pathlib import Path
from moneywizimport.helpers.config_helper import ConfigHelper
from moneywizimport.helpers.fs_helper import collect_statement_files
from moneywizimport.core.statement import generate_reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    config = cfg.load_config()
    statement_dir = Path(config["statement_dir"])

    bank_sets = cfg.load_ofx_bank_sets()

    groups = collect_statement_files(statement_dir, bank_sets)
    ofx_path = Path(config["ofx_dir"])

    '''
    for group in groups:
        print(group["month"])
        for f in group["files"]:
            print(f"  {f['file']} : {f['account']}")
    '''
    password = cfg.get_zip_password()
    categories_mapping = cfg.load_category_mapping()

    payees_mapping = cfg.load_payees_mapping()
    generate_reports(ofx_path, groups, password, payees_mapping, categories_mapping)


if __name__ == "__main__":
    main()
