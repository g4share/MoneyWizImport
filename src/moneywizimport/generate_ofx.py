import argparse
import logging
from pathlib import Path

from moneywizimport.core.statement import generate_reports
from moneywizimport.helpers.config_helper import ConfigHelper
from moneywizimport.helpers.fs_helper import collect_statement_files
from moneywizimport.logging_setup import setup_logging
from moneywizimport.model.bank_config import BankPattern
from moneywizimport.model.payee_mapping import PayeeRule
from moneywizimport.model.statement_groups import StatementGroup


def main() -> None:
    """Entry point for generating OFX files from statement archives."""

    setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    cfg = ConfigHelper(Path(args.config))
    prepared_dir, ofx_dir = cfg.get_statement_dirs()

    bank_patterns = cfg.compile_bank_patterns()
    groups = collect_statement_files(prepared_dir, bank_patterns)

    print_bank_patterns(bank_patterns)
    #print_groups(groups)

    categories_mapping = cfg.load_category_mapping()
    payees_rules = cfg.load_payees_rules()
    #print_payees_rules(payees_rules)
    generate_reports(ofx_dir, groups, payees_rules, categories_mapping)


if __name__ == "__main__":
    main()




def print_payees_rules(payees_rules: list[PayeeRule]) -> None:
    for rule in payees_rules:
        print(f"- match: {rule.match:20} → name: {rule.name}")

def print_groups(groups: list[StatementGroup]) -> None:
    for group in groups:
        print(f"Month: {group.month}")
        for item in group.items:
            pwd = "***" if item.password else None
            print(f"  Bank: {item.bank} | Account: {item.account:15} | Currency: {item.currency:3} | File: {item.file.name} | Password: {pwd}")
        print()

def print_bank_patterns(bank_patterns: list[BankPattern]) -> None:
    for bank in bank_patterns:
        print(bank.name)
        print(f"  filter:   {bank.filter.pattern if bank.filter else None}")
        print(f"  password: {'***' if bank.zip_password else None}")
        for acc in bank.accounts:
            print(f"  - {acc.name:15} → {acc.iban} {acc.currency}")
        print()