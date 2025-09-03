import os
import re
import yaml
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class ConfigHelper:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load_config(self) -> dict:
        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return {k: self._resolve_value(k, v) for k, v in raw.items()}

    def _resolve_value(self, key: str, value):
        if isinstance(value, str) and "${" in value:
            env_key = re.findall(r"\$\{([^}]+)\}", value)[0]
            env_val = os.getenv(env_key, "")
            return env_val
        return value
