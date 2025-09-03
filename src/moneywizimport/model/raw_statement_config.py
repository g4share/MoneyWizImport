"""Configuration model for raw statements."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawStatementConfig:
    """Configuration entry describing how to process raw statement archives."""

    input_dir: Path
    pattern: re.Pattern[str]
    label: str
    rename_template: str
    zip_password: bytes | None = None

    def __repr__(self) -> str:
        password_hint = "***" if self.zip_password else None
        return (
            "<RawStatementConfig "
            f"input_dir={self.input_dir}, "
            f"pattern={self.pattern.pattern!r}, "
            f"rename_template={self.rename_template}, "
            f"zip_password={password_hint}>"
        )

    def log(self, logger: logging.Logger, level: int = logging.DEBUG) -> None:
        """Log this config using the given logger and level."""

        logger.log(level, "→ %s", self)

