from pathlib import Path
from datetime import datetime

def write_ofx_file(ofx_data: list[dict], ofx_path: Path) -> None:
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
    for idx, entry in enumerate(ofx_data, start=1):
        account_name = entry["info"]["name"]
        transactions = entry["transactions"]

        stmt_trns = ""
        for i, txn in enumerate(transactions, start=1):
            stmt_trns += write_transaction(txn, i)

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
          <BANKID>VictoriaBank</BANKID>
          <ACCTID>{account_name}</ACCTID>
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
    print(f"    Wrote → {output_path}")

def write_transaction(txn: dict, index: int) -> str:
    """
    Returns an OFX <STMTTRN> block for a single transaction.
    Assumes txn['amount'] is in MDL.
    Adds foreign currency info to <MEMO> if present.
    """
    fitid = f"{txn['date'].replace('-', '')}{index:04d}"
    dtposted = f"{txn['date'].replace('-', '')}{txn['time'].replace(':', '')}"

    amount = txn["amount"]
    details = txn["details"]
    payee = txn.get("payee", "").strip()
    category = txn.get("category", "").strip()

    currency = txn.get("currency", "MDL").strip()
    foreign = txn.get("foreign_amount", "").strip()

    if payee == ": UNKNOWN":
        if currency != "MDL" and foreign:
            memo = f"{foreign} {currency} : {details}"
        else:
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
