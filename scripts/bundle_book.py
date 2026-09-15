#!/usr/bin/env python3
"""Gộp toàn bộ các phần DAISY đã đóng gói thành 1 file zip để tải cả cuốn.

Đầu vào : dist/<submission_folder>/  (các thư mục phần, mỗi phần có
          <slug>.zip + <slug>_sha256sums.txt — đúng cấu trúc nộp bài)
Đầu ra  : build/<slug>-DAISY.zip  (để trang bìa cho tải qua GitHub Pages)
          + build/<slug>-DAISY.sha256.txt

Usage: python scripts/bundle_book.py
"""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def bundle():
    src = ROOT / "dist" / META["submission_folder"]
    if not src.exists():
        raise SystemExit(f"Chưa có {src} — đóng gói các phần trước (package_book.py).")

    files = sorted(p for p in src.rglob("*") if p.is_file())
    if not files:
        raise SystemExit("Không có phần nào trong dist/ để gộp.")

    out = ROOT / "build" / f"{META['book_slug']}-DAISY.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(src.parent))  # giữ cấu trúc MSHV.../Phần/...

    checksum = out.with_suffix(".sha256.txt")
    checksum.write_text(f"{sha256(out)}  {out.name}\n", encoding="utf-8")

    n_parts = len([d for d in src.iterdir() if d.is_dir()])
    print(f"✅ {out} ({out.stat().st_size / 1e6:.1f} MB, {n_parts} phần)")
    print(f"✅ {checksum}")


if __name__ == "__main__":
    bundle()
