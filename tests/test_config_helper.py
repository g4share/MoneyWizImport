"""Unit tests for config helper loading and resolution."""

from pathlib import Path

import yaml

from moneywizimport.helpers.config_helper import ConfigHelper


def test_config_helper_resolves_env(monkeypatch, tmp_path: Path) -> None:
    """ConfigHelper should resolve ${VAR} placeholders and build objects."""
    monkeypatch.setenv("ZIP_PASS", "secret")

    config_content = {
        "statements": {
            "prepared_dir": "./prep",
            "ofx_dir": "./ofx",
            "raw": [
                {
                    "input_dir": "./in",
                    "pattern": r"^File_(?P<year>\d{4})-(?P<month>\d{2}).zip$",
                    "label": "TEST",
                    "rename_template": "T_{year}-{month}.zip",
                    "zip_password": "${ZIP_PASS}",
                }
            ],
        },
        "payees_mapping": [{"match": "SHOP", "name": "Shop"}],
        "offline_accounts": [{"name": "Cash", "match": ["ATM"]}],
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config_content), encoding="utf-8")

    helper = ConfigHelper(config_path)

    prepared_dir, ofx_dir = helper.get_statement_dirs()
    assert prepared_dir == Path("./prep")
    assert ofx_dir == Path("./ofx")

    raw_configs = helper.get_config_statements()
    assert len(raw_configs) == 1
    assert raw_configs[0].zip_password == b"secret"

    payees = helper.load_payees_rules()
    assert payees[0].name == "Shop"

    offline = helper.get_offline_accounts()
    assert offline[0].name == "Cash"
