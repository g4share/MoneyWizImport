from pathlib import Path
from lxml import html

def read_statement_date(html_path: Path) -> str:
    doc = html.parse(str(html_path))
    return doc.xpath("normalize-space(//span[contains(., 'Situatia la data de')]/ancestor::td/following-sibling::td[1]//text())")
