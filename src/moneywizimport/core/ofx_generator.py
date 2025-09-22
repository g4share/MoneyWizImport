"""Utilities for formatting OFX files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from moneywizimport.model.ofx_models import OfxReport, Transaction


def _write_transaction(transaction: Transaction, index: int) -> str:
    """Return an OFX ``<STMTTRN>`` block for ``transaction``."""

    fit_id = f"{transaction.date.replace('-', '').replace(' ', '').replace(':', '')}{index:04d}"

    if " " in transaction.date:
        date_part, time_part = transaction.date.split(" ", 1)
        posted = f"{date_part.replace('-', '')}{time_part.replace(':', '')}"
    else:
        posted = f"{transaction.date.replace('-', '')}000000"

    amount = transaction.amount
    payee = (transaction.payee or "").strip()
    category = (transaction.category or "").strip()

    memo = transaction.details if payee == ": UNKNOWN" else ""

    result = [
        "    <STMTTRN>",
        "      <TRNTYPE>OTHER</TRNTYPE>",
        f"      <DTPOSTED>{posted}</DTPOSTED>",
        f"      <TRNAMT>{amount}</TRNAMT>",
        f"      <FITID>{fit_id}</FITID>",
        f"      <NAME>{payee}</NAME>",
        f"      <MEMO>{memo}</MEMO>",
    ]

    if category and category != ": UNKNOWN":
        result.append(f"      <CATEGORY>{category}</CATEGORY>")

    result.append("    </STMTTRN>")
    return "\n".join(result)


def write_ofx_file(ofx_reports: list[OfxReport], output_path: Path) -> Path:
    """Write ``ofx_reports`` to ``output_path`` and return the resulting path."""

    output_path = output_path.with_suffix(".ofx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    header = "\n".join(
        [
            "OFXHEADER:100",
            "DATA:OFXSGML",
            "VERSION:102",
            "SECURITY:NONE",
            "ENCODING:USASCII",
            "CHARSET:1252",
            "COMPRESSION:NONE",
            "OLDFILEUID:NONE",
            "NEWFILEUID:NONE",
            "",
        ]
    )

    sign_on = "\n".join(
        [
            "<OFX>",
            "  <SIGNONMSGSRSV1>",
            "    <SONRS>",
            "      <STATUS>",
            "        <CODE>0</CODE>",
            "        <SEVERITY>INFO</SEVERITY>",
            "      </STATUS>",
            f"      <DTSERVER>{timestamp}</DTSERVER>",
            "      <LANGUAGE>ENG</LANGUAGE>",
            "    </SONRS>",
            "  </SIGNONMSGSRSV1>",
            "",
            "  <BANKMSGSRSV1>",
        ]
    )

    body_parts: list[str] = []

    for index, report in enumerate(ofx_reports, start=1):
        transactions = "\n".join(
            _write_transaction(transaction, txn_index)
            for txn_index, transaction in enumerate(report.transactions, start=1)
        )

        body_parts.append(
            "\n".join(
                [
                    "    <STMTTRNRS>",
                    f"      <TRNUID>{index}</TRNUID>",
                    "      <STATUS>",
                    "        <CODE>0</CODE>",
                    "        <SEVERITY>INFO</SEVERITY>",
                    "      </STATUS>",
                    "      <STMTRS>",
                    "        <CURDEF>MDL</CURDEF>",
                    "        <BANKACCTFROM>",
                    f"          <BANKID>{report.info.bank}</BANKID>",
                    f"          <ACCTID>{report.info.account}</ACCTID>",
                    "          <ACCTTYPE>CHECKING</ACCTTYPE>",
                    "        </BANKACCTFROM>",
                    "        <BANKTRANLIST>",
                    transactions,
                    "        </BANKTRANLIST>",
                    "      </STMTRS>",
                    "    </STMTTRNRS>",
                ]
            )
        )

    footer = "\n".join(
        [
            "  </BANKMSGSRSV1>",
            "</OFX>",
        ]
    )

    content = "\n".join([header, sign_on, "\n".join(body_parts), footer])
    output_path.write_text(content, encoding="utf-8")
    return output_path

