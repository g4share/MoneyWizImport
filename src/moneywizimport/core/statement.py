from datetime import datetime
from pathlib import Path
import tempfile, shutil
from moneywizimport.helpers import unzip, zip
from moneywizimport.helpers.html_helper import read_statement_date, read_iban

def prepareArchives(statement_dir: Path, password: bytes | None = None):
    tmp = Path(tempfile.mkdtemp(prefix="mwz_"))
    try:
        for z in sorted(Path(statement_dir).expanduser().glob("*.zip")):
            if z.name.startswith("VB_"):
                continue
            print(f"ZIP: {z.name}")
            html_file = unzip(z, tmp, password=password)
            if html_file:
                date_str = read_statement_date(html_file)  # ex: "01-09-2025"
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                iban = read_iban(html_file).replace(" ", "")
                archive_name = statement_dir / f"VB_{dt.date().isoformat()}_{iban}.zip"
                zip([html_file], archive_name, password=password)
                z.unlink(missing_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
