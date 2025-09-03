"""Logging configuration helpers."""

from __future__ import annotations

import logging

TRACE_LEVEL = 5

class TraceLogger(logging.Logger):
    """Logger subclass that knows about TRACE."""

    def trace(self, message: str, *args: object, **kwargs: object) -> None:
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, message, args, **kwargs)


def register_trace_level() -> None:
    """Register global TRACE logging level if not already present."""
    if "TRACE" in logging._nameToLevel:
        return

    logging.addLevelName(TRACE_LEVEL, "TRACE")
    logging._nameToLevel["TRACE"] = TRACE_LEVEL
    logging._levelToName[TRACE_LEVEL] = "TRACE"
    logging.Logger.trace = TraceLogger.trace  # type: ignore[attr-defined]
    logging.setLoggerClass(TraceLogger)


def setup_logging(level: int = logging.INFO, handler: logging.Handler | None = None) -> None:
    """Configure basic logging for the CLI tools."""

    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    handlers = [handler] if handler else [logging.StreamHandler()]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


register_trace_level()
