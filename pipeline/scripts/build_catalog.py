#!/usr/bin/env python3
"""Sinh books/catalog.json: danh mục thư viện mà ứng dụng đọc sách tải về.

Mỗi cuốn là một thư mục books/<slug>/ có metadata/book_meta.json. Chỉ liệt kê
các đơn vị đã dựng xong (có mo0.smil và file mp3), kèm thời lượng lấy từ
timestamps.csv để app hiển thị và tính tiến độ nghe.

Usage: python pipeline/scripts/build_catalog.py
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from voices import VOICES, narrator  # noqa: E402
BOOKS = REPO / "books"


def unit_entry(ch_dir: Path):
    seg_file, ts_file = ch_dir / "segments.json", ch_dir / "timestamps.csv"
    if not ((ch_dir / "mo0.smil").exists() and seg_file.exists() and ts_file.exists()):
        return None
    seg = json.loads(seg_file.read_text(encoding="utf-8"))
    with open(ts_file, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or not (ch_dir / rows[0]["file_mp3"]).exists():
        return None
    return {
        "no": seg["chapter"],
        "label": seg["label"],
        "title": seg["title"],
        "duration": round(float(rows[-1]["clipEnd"]), 3),
        "segments": len(rows),
        "path": f"{ch_dir.parent.parent.name}/build/{ch_dir.name}",
        "audio": rows[0]["file_mp3"],
    }


def main():
    books = []
    for meta_file in sorted(BOOKS.glob("*/metadata/book_meta.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        root = meta_file.parent.parent
        units = [u for u in map(unit_entry, sorted((root / "build").glob("chapter_*"))) if u]
        if not units:
            continue
        # các giọng cho người nghe chọn: mỗi giọng một bản DAISY ở voices/<id>/
        voices = {}
        for vid in VOICES:
            vunits = [u for u in map(unit_entry, sorted((root / "voices" / vid / "build").glob("chapter_*"))) if u]
            if vunits:
                voices[vid] = {"narrator": narrator(vid), "units": len(vunits),
                               "duration": round(sum(u["duration"] for u in vunits), 3)}
        books.append({
            "slug": meta["book_slug"],
            "title": meta["title"],
            "creator": meta["creator"],
            "subject": meta["subject"],
            "description": meta["description"],
            "date": meta["date"],
            "language": meta["language"],
            "narrator": meta.get("narrator", ""),
            "voices": voices,
            "sourceURL": meta.get("sourceURL", ""),
            "note": meta.get("note", ""),
            "duration": round(sum(u["duration"] for u in units), 3),
            "units": units,
        })
    out = BOOKS / "catalog.json"
    out.write_text(json.dumps({"version": 1, "books": books}, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(b["duration"] for b in books)
    print(f"✅ {out}: {len(books)} sách, {sum(len(b['units']) for b in books)} đơn vị, {total / 60:.1f} phút")


if __name__ == "__main__":
    main()
