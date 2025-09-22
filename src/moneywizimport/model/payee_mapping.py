"""Payee mapping rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PayeeRule:
    """Simple regex rule mapping a description to a payee name."""

    match: str
    name: str

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<PayeeRule match={self.match!r}, name={self.name!r}>"

