"""Utilities for working with statement ZIP archives."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pyzipper

from moneywizimport.helpers.fs_helper import ensure_directory

logger = logging.getLogger(__name__)


def create_zip_archive(
    files: Iterable[Path], archive_name: Path, password: bytes | None = None
) -> Path:
    """Create a password-protected archive containing ``files``."""

    ensure_directory(archive_name.parent)

    with pyzipper.AESZipFile(archive_name, "w", compression=pyzipper.ZIP_DEFLATED) as zip_file:
        if password:
            zip_file.setpassword(password)
            zip_file.setencryption(pyzipper.WZ_AES, nbits=256)

        for file_path in files:
            zip_file.write(file_path, arcname=file_path.name)
            logger.debug("Added %s to %s", file_path, archive_name)

    logger.info("Created archive: %s", archive_name)
    return archive_name


def extract_statement_html(
    archive_path: Path, destination_dir: Path, password: bytes | None = None
) -> Path | None:
    """Extract the ``fullExtras.html`` file from ``archive_path``.

    Parameters
    ----------
    archive_path:
        Path to the ZIP archive that stores the statement export.
    destination_dir:
        Directory where the extracted HTML file should be placed.
    password:
        Optional password used to unlock the archive.
    """

    ensure_directory(destination_dir)

    with pyzipper.AESZipFile(archive_path) as zip_file:
        if password:
            zip_file.pwd = password

        for info in zip_file.infolist():
            if info.is_dir():
                continue

            target_path = Path(info.filename)
            if target_path.name != "fullExtras.html":
                continue

            extract_dir = ensure_directory(destination_dir / target_path.parent)
            zip_file.extract(info, path=destination_dir)
            logger.debug("Extracted %s to %s", info.filename, extract_dir)
            return destination_dir / info.filename

    logger.warning("Could not locate fullExtras.html in %s", archive_path)
    return None

