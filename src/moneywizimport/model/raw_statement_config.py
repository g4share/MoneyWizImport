from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re
import logging

@dataclass
class RawStatementConfig:
    input_dir: Path
    pattern: re.Pattern[str]
    rename_template: str
    zip_password: Optional[bytes] = None

    def __repr__(self) -> str:
        pwd = "***" if self.zip_password else None
        return (
            f"<RawStatementConfig "
            f"input_dir={self.input_dir}, "
            f"pattern={self.pattern.pattern!r}, "
            f"rename_template={self.rename_template}, "
            f"zip_password={pwd}>"
        )

    def log(self, logger: logging.Logger, level: int = logging.DEBUG) -> None:
        """Log this config using the given logger and level."""
        logger.log(level, "→ %s", self)