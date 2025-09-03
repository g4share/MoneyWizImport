"""Unit tests for filesystem helper utilities."""

import re
from pathlib import Path

from moneywizimport.helpers.fs_helper import collect_statement_files, copy_file, ensure_directory
from moneywizimport.model.provider_config import Account, Provider


def test_collect_statement_files_groups_by_month(tmp_path: Path) -> None:
    """Ensure matching files are grouped and account names are resolved."""
    source = tmp_path / "raw"
    source.mkdir()
    file_path = source / "VB_2025-02_MD123.zip"
    file_path.write_text("dummy")

    provider = Provider(
        name="Victoria Bank",
        label="VB",
        filter=re.compile(r"^VB_(?P<year>\d{4})-(?P<month>\d{2})_(?P<iban>.+)\.zip$"),
        accounts=[Account(name="Friendly", iban="MD123")],
        zip_password=None,
    )

    groups = collect_statement_files(source, [provider], group_key=None)

    assert len(groups) == 1
    group = groups[0]
    assert group.month == "2025-02"
    assert len(group.statements) == 1
    statement = group.statements[0]
    assert statement.account == "Friendly"
    assert statement.provider.get_label() == "VB"


def test_copy_file_skips_existing(tmp_path: Path) -> None:
    """copy_file should not overwrite existing targets."""
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("content")
    dst.write_text("existing")

    copied = copy_file(src, dst)

    assert copied is False
    assert dst.read_text() == "existing"


def test_ensure_directory_creates_path(tmp_path: Path) -> None:
    """ensure_directory should create nested directories."""
    target = tmp_path / "nested" / "dir"
    result = ensure_directory(target)

    assert result == target
    assert target.exists() and target.is_dir()
