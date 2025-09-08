"""Helpers for loading and parsing the YAML configuration file."""

import os
from pathlib import Path
import yaml


class ConfigHelper:

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._data: dict | None = None

    def load_config(self) -> dict:
        """
        Loads and resolves top-level config keys, applying environment variable substitution.
        """
        raw = self._load_raw()
        return {k: self._resolve_value(v) for k, v in raw.items()}

    def _load_raw(self) -> dict:
        if self._data is None:
            self._data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        return self._data

    def _resolve_value(self, value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        return value

    def get_zip_password(self) -> bytes | None:
        """
        Reads the 'zip_password' field and returns it as bytes (or None).
        """
        raw = self.load_config().get("zip_password")
        if isinstance(raw, str) and raw != "":
            return raw.encode("utf-8")
        return None

    def load_ofx_bank_sets(self) -> list[dict]:
        """
        Loads 'bank_sets' from the config file (for filtering zip statements).
        """
        return self._load_raw().get("bank_sets", [])

    def load_category_mapping(self) -> dict[str, str]:
        """
        Loads payee-to-category mapping from the 'categories' section of a YAML file.
        Supports nested subcategories of arbitrary depth.

        Returns:
            dict of lowercase payee -> full category path (e.g. 'Food & Dining / Restaurants')
        """

        def recurse(node, current_path):
            if isinstance(node, dict):
                for key, value in node.items():
                    new_path = f"{current_path} / {key}" if current_path else key
                    if isinstance(value, dict) and "payees" in value:
                        for payee in value["payees"]:
                            result[payee.lower()] = new_path
                    else:
                        recurse(value, new_path)

        raw = self._load_raw()
        result: dict[str, str] = {}
        categories = raw.get("categories", {})
        recurse(categories, "")
        return result

    def load_payees_mapping(self) -> list[tuple[str, str]]:
        """
        Loads the payee regex rules from the config YAML.
        Returns a list of (regex, payee name) tuples.
        """
        raw = self._load_raw()
        payees = raw.get("payees_mapping", [])
        return [
            (item["match"], item["name"])
            for item in payees
            if "match" in item and "name" in item
        ]