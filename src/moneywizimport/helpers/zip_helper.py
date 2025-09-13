from pathlib import Path
import pyzipper


def zip(files: list[Path], archive_name: Path, password: bytes | None = None) -> None:
    """Create a ZIP archive containing ``files``.

    Parameters
    ----------
    files:
        List of file paths to include in the archive.
    archive_name:
        Target archive file path.
    password:
        Optional password to encrypt the archive using AES.
    """

    with pyzipper.AESZipFile(archive_name, "w", compression=pyzipper.ZIP_DEFLATED) as zf:
        if password:
            zf.setpassword(password)
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
        for f in files:
            zf.write(f, arcname=f.name)
    print(f"Archived → {archive_name}")


def unzip(zip_path: Path, tmp_dir: Path, password: bytes | None = None) -> Path | None:
    """Extract ``fullExtras.html`` from ``zip_path`` into ``tmp_dir``.

    Returns the path to the extracted file or ``None`` if it was not
    found.
    """

    with pyzipper.AESZipFile(zip_path) as zf:
        if password:
            zf.pwd = password
        for info in zf.infolist():
            if info.is_dir():
                continue
            if Path(info.filename).name == "fullExtras.html":
                (tmp_dir / info.filename).parent.mkdir(parents=True, exist_ok=True)
                zf.extract(info, tmp_dir)
                return tmp_dir / info.filename
    return None

def unzip_group(zip_items: list[dict]) -> list[Path]:
    """Unzip each archive in ``zip_items`` and collect extracted HTML paths."""

    from tempfile import mkdtemp
    tmp_root = Path(mkdtemp())
    results: list[Path] = []
    print("Unzipping group...")
    print(zip_items)
    for idx, item in enumerate(zip_items):
        zip_path = Path(item["path"])
        password = item.get("zip_password")
        target_dir = tmp_root / str(idx)
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"Extracting {zip_path}, pwd: {password}")
        extracted = unzip(zip_path, target_dir, password=password)
        print(f"Extracted  {zip_path} to {extracted}")
        if extracted:
            results.append(extracted)

    return results
