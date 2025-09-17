import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ConfigHelper:
    """Utility for loading and interpreting project configuration files."""

    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load_config(self) -> dict[str, Any]:
        """Load the YAML configuration file and resolve environment variables."""
        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return self._resolve_value(raw)

    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_value(v) for v in value]
        if isinstance(value, str) and "${" in value:
            env_key = re.findall(r"\$\{([^}]+)}", value)[0]
            return os.getenv(env_key, "")
        return value

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

    def load_payees_mapping(self) -> list[tuple[str, str]]:
        """Load the payee regex rules from the config YAML."""
        raw = self.load_config()
        payees = raw.get("payees_mapping", [])
        return [
            (item["match"], item["name"]) for item in payees if "match" in item and "name" in item
        ]

    def compile_bank_patterns(self) -> dict[str, dict]:
        """Compile regex filter, account IBAN patterns and zip password for each bank."""
        raw = self.load_config()
        compiled: dict[str, dict] = {}

        for bank in raw.get("banks", []):
            name = bank["name"]

            bank_filter = bank.get("filter")
            filter_re = re.compile(bank_filter) if bank_filter else None

            accounts = bank.get("accounts", [])
            acc_patterns: list[tuple[re.Pattern, str]] = []
            for acc in accounts:
                iban = acc.get("iban")
                if iban:
                    acc_patterns.append((re.compile(iban), acc["name"]))

            compiled[name] = {
                "filter": filter_re,
                "accounts": acc_patterns,
                "password": bank.get("zip_password"),
            }

        return compiled