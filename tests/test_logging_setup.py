"""Unit tests for logging setup and custom TRACE level."""

import logging

from moneywizimport.logger import logging_setup


def test_trace_level_registered(caplog) -> None:
    """Logger should expose a TRACE method and emit messages at custom level."""
    logger = logging.getLogger("test-trace")
    logger.setLevel(logging_setup.TRACE_LEVEL)

    with caplog.at_level(logging_setup.TRACE_LEVEL, logger="test-trace"):
        logger.trace("hello trace")

    assert "hello trace" in caplog.text
