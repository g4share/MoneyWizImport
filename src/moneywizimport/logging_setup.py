"""Logging configuration helpers."""

from __future__ import annotations

import logging


def setup_logging(level: int = logging.INFO, handler: logging.Handler | None = None) -> None:
    """Configure basic logging for the CLI tools."""

    handlers = [handler] if handler else [logging.StreamHandler()]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

