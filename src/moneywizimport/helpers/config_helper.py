"""Utilities for loading and interpreting YAML configuration files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from moneywizimport.model import RawStatementConfig
from moneywizimport.model.bank_config import Account, BankPattern
from moneywizimport.model.payee_mapping import PayeeRule


class ConfigHelper:
    """Utility for loading and interpreting project configuration files."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._cache: dict[str, Any] | None = None

    def load_config(self) -> dict[str, Any]:
        """Load the YAML configuration file and resolve environment variables."""

        if self._cache is None:
            raw_content = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
            self._cache = self._resolve_value(raw_content)
        return self._cache

    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._resolve_value(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._resolve_value(item) for item in value]
        if isinstance(value, str):
            return re.sub(r"\$\{([^}]+)\}", lambda match: os.getenv(match.group(1), ""), value)
        return value

    def get_statement_dirs(self) -> tuple[Path, Path]:
        config = self.load_config()
        statements = config.get("statements", {})
        prepared = Path(statements.get("prepared_dir", "./statements/prepared"))
        ofx = Path(statements.get("ofx_dir", "./ofx"))
        return prepared, ofx

    def get_config_statements(self) -> list[RawStatementConfig]:
        """Return list of ``RawStatementConfig`` entries from the YAML config."""

        config = self.load_config()
        results: list[RawStatementConfig] = []

        for item in config.get("statements", {}).get("raw", []):
            zip_password = item.get("zip_password")
            password_bytes = zip_password.encode() if isinstance(zip_password, str) else None

            results.append(
                RawStatementConfig(
                    input_dir=Path(item["input_dir"]),
                    pattern=re.compile(item["pattern"]),
                    rename_template=item["rename_template"],
                    zip_password=password_bytes,
                )
            )

        return results

    def load_category_mapping(self) -> dict[str, str]:
        """Load payee-to-category mapping from the ``categories`` section."""

        raw_config = self.load_config()
        categories = raw_config.get("categories", {})
        mapping: Dict[str, str] = {}

        def _populate(node: Any, current_path: str) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    new_path = f"{current_path} / {key}" if current_path else key
                    if isinstance(value, dict) and "payees" in value:
                        for payee in value["payees"]:
                            mapping[payee.lower()] = new_path
                    else:
                        _populate(value, new_path)

        _populate(categories, "")
        return mapping

    def load_payees_rules(self) -> list[PayeeRule]:
        """Load the payee regex rules from the config YAML."""

        config = self.load_config()
        payees = config.get("payees_mapping", [])
        rules: list[PayeeRule] = []

        for item in payees:
            match = item.get("match")
            name = item.get("name")
            if match and name:
                rules.append(PayeeRule(match=match, name=name))

        return rules

    def compile_bank_patterns(self) -> list[BankPattern]:
        """Compile regex filters, accounts and zip password for each bank."""

        config = self.load_config()
        compiled: list[BankPattern] = []

        for bank in config.get("banks", []):
            accounts: list[Account] = []
            for account in bank.get("accounts", []):
                accounts.append(Account(name=account["name"], iban=account["iban"]))

            pattern = bank.get("filter")
            compiled.append(
                BankPattern(
                    name=bank["name"],
                    filter=re.compile(pattern) if pattern else None,
                    accounts=accounts,
                    zip_password=bank.get("zip_password").encode() if bank.get("zip_password") else None,
                )
            )

        return compiled

