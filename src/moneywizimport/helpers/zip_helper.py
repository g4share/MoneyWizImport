from pathlib import Path
import logging
import pyzipper


logger = logging.getLogger(__name__)


def zip_files(files: list[Path], archive_name: Path, password: bytes | None = None) -> None:
    """Archive *files* into *archive_name*.

    Parameters
    ----------
    files:
        Sequence of paths to add to the archive.
    archive_name:
        Destination archive path.
    password:
        Optional password used to encrypt the archive.
    """

    with pyzipper.AESZipFile(archive_name, "w", compression=pyzipper.ZIP_DEFLATED) as zf:
        if password:
            zf.setpassword(password)
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
        for file in files:
            zf.write(file, arcname=file.name)
    logger.info("Archived %s", archive_name)

def unzip(zip_path: Path, tmp_dir: Path, password: bytes | None = None) -> Path | None:
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

def unzip_group(zip_items: list[dict], password: bytes | None = None) -> list[Path]:
    from tempfile import mkdtemp
    tmp_root = Path(mkdtemp())
    results = []

    for idx, item in enumerate(zip_items):
        zip_path = Path(item["path"])
        target_dir = tmp_root / str(idx)
        target_dir.mkdir(parents=True, exist_ok=True)

        extracted = unzip(zip_path, target_dir, password=password)
        if extracted:
            results.append(extracted)

    return results
