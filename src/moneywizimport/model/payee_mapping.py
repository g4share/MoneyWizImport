from dataclasses import dataclass


@dataclass
class PayeeRule:
    match: str
    name: str

    def __repr__(self) -> str:
        return f"<PayeeRule match={self.match!r}, name={self.name!r}>"
