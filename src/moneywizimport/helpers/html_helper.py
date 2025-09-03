"""Helpers for extracting data from statement HTML files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import html
from lxml.html import HtmlElement

logger = logging.getLogger(__name__)


def _parse_html(html_file: Path) -> HtmlElement:
    """Return an ``lxml`` document tree for ``html_file``."""

    text = html_file.read_text(encoding="utf-8", errors="replace")
    return html.fromstring(text)


def read_by_xpath(html_file: Path, xpath: str) -> str:
    try:
        document = _parse_html(html_file)
        return document.xpath(f"normalize-space({xpath})")
    except Exception:
        logger.exception("Failed to read xpath data from %s", html_file)
        raise

def read_elements_by_xpath(html_file: Path, xpath: str) -> list[HtmlElement]:
    """Return all matching HTML elements for the given XPath."""
    try:
        document = _parse_html(html_file)
        return document.xpath(xpath)
    except Exception:
        logger.exception("Failed to read elements by xpath from %s", html_file)
        raise
