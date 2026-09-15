#!/usr/bin/env python3
"""Đóng gói 1 chương thành format nộp bài:

  dist/<MSHV1_MSHV2_.../>
  └── <Tên_sách>-Chương N/
      ├── <Tên_sách>.zip              (dtbook.xml, mo0.smil, mp3, book.opf, navigation.ncx, resources.res)
      └── <Tên_sách>_sha256sums.txt   (hash từng file trong zip + hash file zip)

Usage: python scripts/package_book.py 1
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))

PACK_FILES = ["dtbook.xml", "mo0.smil", "book.opf", "navigation.ncx", "resources.res"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def package(chapter_no: int):
    ch = ROOT / "build" / f"chapter_{chapter_no:02d}"
    slug = META["book_slug"]
    files = PACK_FILES + [f"chuong{chapter_no:02d}.mp3"]
    for f in files:
        if not (ch / f).exists():
            raise SystemExit(f"Thiếu {f} — chạy validate_daisy.py trước.")

    from extract_chapter import book_units
    folders = {no: folder for no, _l, folder, _s in book_units()}
    unit = folders.get(chapter_no, f"Chương {chapter_no}")
    out_dir = ROOT / "dist" / META["submission_folder"] / f"{slug}-{unit}"
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / f"{slug}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(ch / f, f)

    # chỉ hash file zip — để `sha256sum -c` chạy được ngay trong thư mục nộp
    sums_path = out_dir / f"{slug}_sha256sums.txt"
    sums_path.write_text(f"{sha256(zip_path)}  {slug}.zip\n", encoding="utf-8")

    # bản sao để trang preview cho tải trực tiếp qua GitHub Pages
    import shutil
    shutil.copy(zip_path, ch / "daisy.zip")

    size_mb = zip_path.stat().st_size / 1e6
    print(f"✅ {zip_path} ({size_mb:.1f} MB)")
    print(f"✅ {sums_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    package(ap.parse_args().chapter)
