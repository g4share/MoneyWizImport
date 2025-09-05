from pathlib import Path
from datetime import datetime

def write_olx_file(olx_data: list[dict], olx_path: Path) -> None:
    output_path = olx_path.with_suffix(".ofx")
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

    for idx, entry in enumerate(olx_data, start=1):
        account_name = entry["info"]["name"]
        transactions = entry["transactions"]

        stmt_trns = ""
        for i, txn in enumerate(transactions, start=1):
            fitid = f"{txn['date'].replace('-', '')}{i:04d}"
            dtposted = f"{txn['date'].replace('-', '')}{txn['time'].replace(':', '')}"
            amount = float(txn["amount"].replace(",", "."))
            category = ""

            if amount > 0:
                category = "Sales"
            elif amount < 0 and "beef house" in txn["details"].lower():
                category = "Food & Dining / Restaurants"

            stmt_trns += f"""
            <STMTTRN>
              <TRNTYPE>OTHER</TRNTYPE>
              <DTPOSTED>{dtposted}</DTPOSTED>
              <TRNAMT>{txn['amount']}</TRNAMT>
              <FITID>{fitid}</FITID>
              <NAME>{txn['details'][:32]}</NAME>
              <MEMO>{txn['details']}</MEMO>"""

            if category:
                stmt_trns += f"""
              <CATEGORY>{category}</CATEGORY>"""

            stmt_trns += """
            </STMTTRN>"""

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
        <LEDGERBAL>
          <BALAMT>0.00</BALAMT>
          <DTASOF>{now}</DTASOF>
        </LEDGERBAL>
      </STMTRS>
    </STMTTRNRS>
"""

    footer = """  </BANKMSGSRSV1>
</OFX>
"""

    content = header + signon + body + footer
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote → {output_path}")
