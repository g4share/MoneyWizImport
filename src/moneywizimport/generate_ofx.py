"""Command line entry point for generating OFX reports."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from moneywizimport.core.statement import generate_reports
from moneywizimport.helpers import ConfigHelper, collect_statement_files
from moneywizimport.logging_setup import setup_logging
from moneywizimport.model.bank_config import BankPattern
from moneywizimport.model.payee_mapping import PayeeRule
from moneywizimport.model.statement_groups import StatementGroup

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for generating OFX files from statement archives."""

    setup_logging(logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    args = parser.parse_args()

    config_helper = ConfigHelper(Path(args.config))
    prepared_dir, ofx_dir = config_helper.get_statement_dirs()

    bank_patterns = config_helper.compile_bank_patterns()
    groups = collect_statement_files(prepared_dir, bank_patterns)

    _log_bank_patterns(bank_patterns)
    _log_groups(groups)

    category_map = config_helper.load_category_mapping()
    payee_rules = config_helper.load_payees_rules()
    _log_payee_rules(payee_rules)

    generate_reports(ofx_dir, groups, payee_rules, category_map)


def _log_payee_rules(payee_rules: Iterable[PayeeRule]) -> None:
    for rule in payee_rules:
        logger.debug("Payee rule: match=%s → name=%s", rule.match, rule.name)


def _log_groups(groups: Iterable[StatementGroup]) -> None:
    for group in groups:
        logger.debug("Month: %s", group.month)
        for item in group.items:
            password_hint = "***" if item.password else None
            logger.debug(
                "  Bank=%s Account=%s File=%s Password=%s",
                item.bank,
                item.account,
                item.file.name,
                password_hint,
            )


def _log_bank_patterns(bank_patterns: Iterable[BankPattern]) -> None:
    for bank in bank_patterns:
        logger.debug("Bank: %s", bank.name)
        logger.debug("  filter:   %s", bank.filter.pattern if bank.filter else None)
        logger.debug("  password: %s", "***" if bank.zip_password else None)
        for acc in bank.accounts:
            logger.debug("  account: %s → %s", acc.name, acc.iban)


if __name__ == "__main__":
    main()

