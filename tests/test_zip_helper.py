"""Integration-style tests for zip helper utilities."""

from pathlib import Path

from moneywizimport.helpers.zip_helper import unzip_archive, zip_archive


def test_zip_and_unzip_with_password(tmp_path: Path) -> None:
    """zip_archive should write files and unzip_archive should extract them with password."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    file_path = source_dir / "hello.txt"
    file_path.write_text("hello", encoding="utf-8")

    archive = tmp_path / "archive.zip"
    password = b"pw"

    created = zip_archive(files=[file_path], archive_name=archive, password=password)
    assert created.exists()

    dest = tmp_path / "dest"
    extracted = unzip_archive(created, dest, password=password)

    assert extracted is not None
    assert extracted.exists()
    assert extracted.read_text(encoding="utf-8") == "hello"
