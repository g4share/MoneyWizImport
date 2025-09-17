import os
import re
from pathlib import Path
from typing import Any

import yaml

from moneywizimport.model import RawStatementConfig
from moneywizimport.model.bank_config import BankPattern, Account
from moneywizimport.model.payee_mapping import PayeeRule


class ConfigHelper:
    """Utility for loading and interpreting project configuration files."""

    def __init__(self, config_path: Path):
        self.config_path = config_path

    #
    def load_config(self) -> dict[str, Any]:
        """Load the YAML configuration file and resolve environment variables."""
        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return self._resolve_value(raw)

    #
    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_value(v) for v in value]
        if isinstance(value, str) and "${" in value:
            env_key = re.findall(r"\$\{([^}]+)}", value)[0]
            return os.getenv(env_key, "")
        return value

    #
    def get_prepared_dir(self) -> Path:
        """Return prepared_dir from YAML config as Path."""
        config = self.load_config()
        return Path(config.get("statements", {}).get("prepared_dir", ".")).expanduser()

    #
    def get_statement_dirs(self) -> tuple[Path, Path]:
        config = self.load_config()
        stm = config.get("statements", {})
        prepared = Path(stm.get("prepared_dir", "./statements/prepared"))
        ofx = Path(stm.get("ofx_dir", "./ofx"))
        return prepared, ofx

    #
    def get_config_statements(self) -> list[RawStatementConfig]:
        """Return list of RawStatementConfig entries from YAML config."""
        config = self.load_config()
        results: list[RawStatementConfig] = []

        for item in config.get("statements", {}).get("raw", []):
            zip_password = item.get("zip_password")
            if isinstance(zip_password, str):
                zip_password = zip_password.encode()

            results.append(
                RawStatementConfig(
                    input_dir=Path(item["input_dir"]),
                    pattern=re.compile(item["pattern"]),
                    rename_template=item["rename_template"],
                    zip_password=zip_password,
                )
            )
        return results


    def load_category_mapping(self) -> dict[str, str]:
        """Load payee-to-category mapping from the ``categories`` section."""

        def recurse(node, current_path):
            if isinstance(node, dict):
                for key, value in node.items():
                    new_path = f"{current_path} / {key}" if current_path else key
                    if isinstance(value, dict) and "payees" in value:
                        for payee in value["payees"]:
                            result[payee.lower()] = new_path
                    else:
                        recurse(value, new_path)

        raw = self.load_config()
        result: dict[str, str] = {}
        categories = raw.get("categories", {})
        recurse(categories, "")
        return result

    #
    def load_payees_rules(self) -> list[PayeeRule]:
        """Load the payee regex rules from the config YAML."""
        raw = self.load_config()
        payees = raw.get("payees_mapping", [])
        return [
            PayeeRule(match=item["match"], name=item["name"])
            for item in payees
            if "match" in item and "name" in item
        ]
    #
    def compile_bank_patterns(self) -> list[BankPattern]:
        """Compile regex filter, accounts and zip password for each bank."""

        raw = self.load_config()
        compiled: list[BankPattern] = []

        for bank in raw.get("banks", []):
            accounts: list[Account] = []
            for acc in bank.get("accounts", []):
                accounts.append(
                    Account(
                        name=acc["name"],
                        iban=acc["iban"],
                        currency=acc["currency"],
                    )
                )

            bank_filter = bank.get("filter")
            compiled.append(
                BankPattern(
                    name=bank["name"],
                    filter=re.compile(bank_filter),
                    accounts=accounts,
                    zip_password=bank.get("zip_password").encode() if bank.get("zip_password") else None,
                )
            )

        return compiled