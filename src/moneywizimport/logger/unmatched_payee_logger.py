import logging


class UnmatchedPayeeLogger:
    """Collects and logs unmatched transaction descriptions."""

    def __init__(self) -> None:
        self._unmatched: set[str] = set()
        self._logger = logging.getLogger(__name__)

    def add(self, description: str | None) -> None:
        if description:
            self._unmatched.add(description.strip())

    def log(self) -> None:
        if not self._unmatched:
            return

        for desc in sorted(self._unmatched):
            self._logger.info("Unmatched payee: %s", desc)
