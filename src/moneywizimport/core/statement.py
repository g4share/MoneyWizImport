from datetime import datetime
from pathlib import Path
from typing import List, Dict

import tempfile, shutil
from moneywizimport.helpers import unzip, zip, unzip_group
from moneywizimport.helpers.fs_helper import delete_files
from moneywizimport.helpers.html_helper import extract_transactions
from moneywizimport.core.olx_generator import write_olx_file

from moneywizimport.helpers.html_helper import read_statement_date

def prepareArchives(statement_dir: Path, password: bytes | None = None):
    tmp = Path(tempfile.mkdtemp(prefix="mwz_"))
    try:
        for z in sorted(Path(statement_dir).expanduser().glob("*.zip")):
            if z.name.startswith("VB_"):
                continue
            print(f"ZIP: {z.name}")
            html_file = unzip(z, tmp, password=password)
            if html_file:
                date_str = read_statement_date(html_file)
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                archive_name = statement_dir / f"VB_{dt.date().isoformat()}.zip"
                zip([html_file], archive_name, password=password)
                z.unlink(missing_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def generate_reports(olx_path: Path, groups: List[Dict[str, str]], password: bytes | None = None) -> None:
    for group in groups:
        if group["month"] == "2024-02":
            generate_report(olx_path, [group], password)

def generate_report(olx_path: Path, group: List[Dict[str, str]], password: bytes | None = None) -> None:

    html_files = unzip_group(group, password)
    olx_data = []

    try:
        for idx, f in enumerate(html_files):
            print(f)
            transactions = extract_transactions(f)
            info = {"name": group[idx]["account"]}
            olx_data.append({
                "info": info,
                "transactions": transactions
                #aucu citeste din  file
            })

        # debug print
        for entry in olx_data:
            print(f">>> {entry['info']['name']}") # aici ripareste
            #for t in entry["transactions"]:
            #    print(f"   {t}")

        month = group[0]["month"]
        write_olx_file(olx_data, olx_path / month)

    finally:
        delete_files(html_files)