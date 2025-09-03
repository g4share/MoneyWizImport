"""Utilities for working with statement ZIP archives."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pyzipper

from moneywizimport.helpers.fs_helper import ensure_directory

logger = logging.getLogger(__name__)


def zip_archive(
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
            logger.trace("Added %s to %s", file_path, archive_name)

    return archive_name


def unzip_archive(
    archive_path: Path, destination_dir: Path, password: bytes | None = None
) -> Path | None:

    ensure_directory(destination_dir)

    with pyzipper.AESZipFile(archive_path) as zip_file:
        if password:
            zip_file.pwd = password

        for info in zip_file.infolist():
            if info.is_dir():
                continue

            target_path = Path(info.filename)

            extract_dir = ensure_directory(destination_dir / target_path.parent)
            zip_file.extract(info, path=destination_dir)
            logger.trace("Extracted %s to %s", info.filename, extract_dir)
            return destination_dir / info.filename

    return None
