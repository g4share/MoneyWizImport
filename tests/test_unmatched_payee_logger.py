"""Unit tests for the UnmatchedPayeeLogger."""

import logging

from moneywizimport.logger.unmatched_payee_logger import UnmatchedPayeeLogger


def test_unmatched_payee_logger_adds_unique_and_logs(caplog) -> None:
    logger = UnmatchedPayeeLogger()

    logger.add(" Payee A ")
    logger.add("Payee A")  # duplicate; should be kept once
    logger.add(None)

    with caplog.at_level(logging.INFO):
        logger.log()

    assert "Unmatched payee: Payee A" in caplog.text
