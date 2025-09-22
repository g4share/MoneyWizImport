"""Logging configuration helpers."""

from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: int = logging.INFO, handler: Optional[logging.Handler] = None) -> None:
    """Configure basic logging for the CLI tools."""

    handlers = [handler] if handler else [logging.StreamHandler()]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

