from pathlib import Path
from datetime import datetime

from moneywizimport.model.ofx_models import OfxReport, Transaction


#
def _write_transaction(txn: Transaction, index: int) -> str:
    """Return an OFX <STMTTRN> block for a single transaction."""

    fitid = f"{txn.date.replace('-', '').replace(' ', '').replace(':', '')}{index:04d}"

    if " " in txn.date:
        date_part, time_part = txn.date.split(" ", 1)
        dtposted = f"{date_part.replace('-', '')}{time_part.replace(':', '')}"
    else:
        dtposted = f"{txn.date.replace('-', '')}000000"

    amount = txn.amount
    details = txn.details or ""
    payee = (txn.payee or "").strip()
    category = (txn.category or "").strip()

    if payee == ": UNKNOWN":
        memo = details
    else:
        memo = ""

    result = f"""
    <STMTTRN>
      <TRNTYPE>OTHER</TRNTYPE>
      <DTPOSTED>{dtposted}</DTPOSTED>
      <TRNAMT>{amount}</TRNAMT>
      <FITID>{fitid}</FITID>
      <NAME>{payee}</NAME>
      <MEMO>{memo}</MEMO>"""

    if category and category != ": UNKNOWN":
        result += f"""
      <CATEGORY>{category}</CATEGORY>"""

    result += """
    </STMTTRN>"""
    return result

#
def write_ofx_file(ofx_data: list[OfxReport], ofx_path: Path) -> None:
    """Write a list of OfxReport objects to an OFX file."""

    output_path = ofx_path.with_suffix(".ofx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y%m%d%H%M%S")

    header = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

"""

    signon = f"""<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <DTSERVER>{now}</DTSERVER>
      <LANGUAGE>ENG</LANGUAGE>
    </SONRS>
  </SIGNONMSGSRSV1>

  <BANKMSGSRSV1>
"""

    body = ""
    for idx, report in enumerate(ofx_data, start=1):
        bank = report.info.bank
        account_id = report.info.account
        transactions = report.transactions

        stmt_trns = ""
        for i, txn in enumerate(transactions, start=1):
            stmt_trns += _write_transaction(txn, i)

        body += f"""
    <STMTTRNRS>
      <TRNUID>{idx}</TRNUID>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <STMTRS>
        <CURDEF>MDL</CURDEF>
        <BANKACCTFROM>
          <BANKID>{bank}</BANKID>
          <ACCTID>{account_id}</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>{stmt_trns}
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
"""

    footer = """  </BANKMSGSRSV1>
</OFX>
"""

    content = header + signon + body + footer
    output_path.write_text(content, encoding="utf-8")