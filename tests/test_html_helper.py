"""Unit tests for HTML helper utilities."""

from pathlib import Path

from moneywizimport.helpers.html_helper import read_by_xpath, read_elements_by_xpath


def test_read_by_xpath_and_elements(tmp_path: Path) -> None:
    """Should extract normalized text and elements from HTML."""
    html_file = tmp_path / "sample.html"
    html_file.write_text(
        """
        <html>
            <body>
                <div class="title">  Hello&nbsp;World </div>
                <ul>
                    <li>One</li>
                    <li>Two</li>
                </ul>
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    title = read_by_xpath(html_file, "//div[@class='title']")
    items = read_elements_by_xpath(html_file, "//ul/li")

    assert title.replace("\xa0", " ") == "Hello World"
    assert [el.text for el in items] == ["One", "Two"]
