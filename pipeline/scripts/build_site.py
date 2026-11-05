#!/usr/bin/env python3
"""Lắp ráp trang web tĩnh của thư viện vào site/ (thư mục này được deploy lên GitHub Pages).

  site/
  ├── index.html, app.css, app.js, sw.js, ...   <- chép từ app/web/
  ├── catalog.json                               <- danh mục thư viện
  └── books/<slug>/NN.json, NN.mp3, <slug>-daisy.zip

Mỗi phần của sách cần build/chapter_NN/segments.json. Phần đã có audio (mp3 +
timestamps.csv) được xuất bản đầy đủ; phần chưa có audio vẫn hiện trong mục lục
với trạng thái "đang chuẩn bị". Nhờ vậy có thể deploy dần từng chương, từng cuốn.

Nếu có sentences.csv (TTS Piper) thì văn bản được đồng bộ theo từng câu; nếu
không (bản giữa kỳ dùng edge-tts) thì mỗi đoạn là một mốc.

Usage: python3 pipeline/scripts/build_site.py [--legacy-totto]
"""
import argparse
import csv
import json
import shutil
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
BOOKS, WEB, SITE = REPO / "books", REPO / "app" / "web", REPO / "site"
DAISY_FILES = ["dtbook.xml", "mo0.smil", "book.opf", "navigation.ncx", "resources.res"]

# Cuốn của đồ án giữa kỳ: không dựng lại ở đây, chỉ thêm một thẻ trên kệ trỏ tới
# trang đã deploy sẵn dưới build/ (deploy_site.py giữ nguyên thư mục đó).
LEGACY_TOTTO = {
    "slug": "totto-chan", "title": "Totto-chan Bên Cửa Sổ", "creator": "Tetsuko Kuroyanagi",
    "subject": "Trẻ em & Thiếu nhi", "duration": 18701, "unitCount": 63,
    "external": "build/index.html", "cover": "build/cover.jpg",
}


def read_csv(path: Path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def human_size(n: int) -> str:
    return f"{n / 1e6:.0f} MB" if n >= 10e6 else f"{n / 1e6:.1f} MB"


def build_unit(ch_dir: Path, out_dir: Path, slug: str):
    """-> (mục trong danh mục, đường dẫn file DAISY của phần này hoặc None)"""
    seg = json.loads((ch_dir / "segments.json").read_text(encoding="utf-8"))
    no = seg["chapter"]
    entry = {"no": no, "label": seg["label"], "title": seg["title"], "duration": 0, "ready": False}
    ts_file = ch_dir / "timestamps.csv"
    rows = read_csv(ts_file) if ts_file.exists() else []
    mp3 = ch_dir / rows[0]["file_mp3"] if rows else None
    if not rows or not mp3.exists() or not (ch_dir / "mo0.smil").exists():
        return entry, None

    clips = {r["id"]: (float(r["clipBegin"]), float(r["clipEnd"])) for r in rows}
    sents = {}
    if (ch_dir / "sentences.csv").exists():
        for r in read_csv(ch_dir / "sentences.csv"):
            sents.setdefault(r["id"], []).append(
                [round(float(r["clipBegin"]), 3), round(float(r["clipEnd"]), 3), r["text"]])
    paras = []
    for s in seg["segments"]:
        b, e = clips[s["id"]]
        paras.append({"id": s["id"], "t": s["type"], "b": round(b, 3), "e": round(e, 3),
                      "s": sents.get(s["id"]) or [[round(b, 3), round(e, 3), s["text"]]]})
    duration = round(max(e for _, e in clips.values()), 3)

    name = f"{no:02d}"
    (out_dir / f"{name}.json").write_text(json.dumps(
        {"slug": slug, "no": no, "label": seg["label"], "title": seg["title"],
         "duration": duration, "paras": paras}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    shutil.copyfile(mp3, out_dir / f"{name}.mp3")
    entry.update(duration=duration, ready=True,
                 data=f"books/{slug}/{name}.json", audio=f"books/{slug}/{name}.mp3")
    return entry, ch_dir


def main(legacy_totto: bool):
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(WEB, SITE)
    (SITE / ".nojekyll").write_text("")          # GitHub Pages: phát nguyên trạng, không qua Jekyll

    books = []
    for meta_file in sorted(BOOKS.glob("*/metadata/book_meta.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        root, slug = meta_file.parent.parent, meta["book_slug"]
        ch_dirs = [d for d in sorted((root / "build").glob("chapter_*")) if (d / "segments.json").exists()]
        if not ch_dirs:
            continue
        out_dir = SITE / "books" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        units, daisy_dirs = [], []
        for d in ch_dirs:
            entry, daisy_dir = build_unit(d, out_dir, slug)
            units.append(entry)
            if daisy_dir:
                daisy_dirs.append(daisy_dir)
        book = {
            "slug": slug, "title": meta["title"], "creator": meta["creator"], "subject": meta["subject"],
            "description": meta["description"], "date": meta["date"], "narrator": meta.get("narrator", ""),
            "sourceURL": meta.get("sourceURL", ""), "note": meta.get("note", ""),
            "duration": round(sum(u["duration"] for u in units), 3), "units": units,
        }
        if daisy_dirs:   # gói DAISY 3 đầy đủ để mở bằng Thorium / EasyReader
            zip_path = out_dir / f"{slug}-daisy.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                for d in daisy_dirs:
                    prefix = "" if len(ch_dirs) == 1 else f"{d.name}/"
                    for name in DAISY_FILES + [p.name for p in d.glob("chuong*.mp3")]:
                        if (d / name).exists():
                            z.write(d / name, prefix + name)
            book["daisy"] = f"books/{slug}/{zip_path.name}"
            book["daisySize"] = human_size(zip_path.stat().st_size)
        books.append(book)

    books.sort(key=lambda b: b["title"])
    if legacy_totto:
        books.append(LEGACY_TOTTO)
    (SITE / "catalog.json").write_text(
        json.dumps({"version": 1, "books": books}, ensure_ascii=False, indent=1), encoding="utf-8")

    ready = sum(1 for b in books for u in b.get("units", []) if u["ready"])
    total = sum(len(b.get("units", [])) for b in books)
    size = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
    minutes = sum(b["duration"] for b in books if "units" in b) / 60
    print(f"✅ site/: {len(books)} sách, {ready}/{total} phần đã có audio, {minutes:.0f} phút, {human_size(size)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy-totto", action="store_true",
                    help="thêm thẻ Totto-chan trỏ tới trang giữa kỳ dưới build/")
    main(ap.parse_args().legacy_totto)
