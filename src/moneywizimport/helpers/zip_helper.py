from pathlib import Path
import pyzipper

def zip(files: list[Path], archive_name: Path, password: bytes | None = None):
    with pyzipper.AESZipFile(archive_name, "w", compression=pyzipper.ZIP_DEFLATED) as zf:
        if password:
            zf.setpassword(password)
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
        for f in files:
            zf.write(f, arcname=f.name)
    print(f"Archived → {archive_name}")

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
