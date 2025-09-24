"""Command line entry point for generating OFX reports."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from moneywizimport.core.statement import generate_reports
from moneywizimport.helpers import ConfigHelper, collect_statement_files
from moneywizimport.logging_setup import setup_logging
from moneywizimport.model.provider_config import Provider, OfflineAccount
from moneywizimport.model.statement_groups import StatementGroup

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for generating OFX files from statement archives."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="src/moneywizimport/config.yaml")
    parser.add_argument("--logging", choices=logging._nameToLevel, default=logging.INFO)
    args = parser.parse_args()

    setup_logging(logging.getLevelName(args.logging))

    config_helper = ConfigHelper(Path(args.config))

    prepared_dir, ofx_dir = config_helper.get_statement_dirs()

    providers = config_helper.compile_providers()
    groups = collect_statement_files(prepared_dir, providers)
    offline_accounts = config_helper.get_offline_accounts()

    _log_providers(providers)
    _log_groups(groups)
    _log_offline_accounts(offline_accounts)

    category_map = config_helper.load_category_mapping()
    payee_rules = config_helper.load_payees_rules()
    generate_reports(ofx_dir, groups, payee_rules, category_map, offline_accounts)


def _log_groups(groups: Iterable[StatementGroup]) -> None:
    for group in groups:
        logger.debug("%r", group)
        for statement in group.statements:
            logger.debug("  %r", statement)

def _log_providers(providers: Iterable[Provider]) -> None:
    for provider in providers:
        logger.debug("%r", provider)
        for account in provider.accounts or []:
            logger.debug("  %r", account)

def _log_offline_accounts(offline_accounts: Iterable[OfflineAccount]) -> None:
    for offline_account in offline_accounts:
        logger.debug("%r", offline_account)

if __name__ == "__main__":
    main()

