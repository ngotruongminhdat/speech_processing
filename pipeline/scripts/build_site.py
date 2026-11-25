#!/usr/bin/env python3
"""Lắp ráp trang web tĩnh của thư viện vào site/ (thư mục này được deploy lên GitHub Pages).

  site/
  ├── index.html, app.css, app.js, sw.js, ...   <- chép từ app/web/
  ├── catalog.json                               <- danh mục thư viện
  └── books/<slug>/<giọng>/NN.json, NN.mp3    <- mỗi giọng đọc một thư mục (hm; dự phòng nu, piper)
      books/<slug>/<slug>-daisy-<giọng>.zip

Mỗi cuốn có thể có nhiều giọng đọc (voices.py), mỗi giọng là một bản DAISY riêng ở
books/<slug>/voices/<id>/. Bản Piper ở thư mục gốc của sách chỉ được đưa lên cho
những phần chưa dựng đủ các giọng mới, làm giọng dự phòng.

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
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from voices import FALLBACKS, VOICES  # noqa: E402
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


def build_unit(ch_dir: Path, out_dir: Path, slug: str, vid: str):
    """Xuất một phần của một giọng -> {data, audio, duration} hoặc None nếu chưa dựng xong."""
    ts_file = ch_dir / "timestamps.csv"
    rows = read_csv(ts_file) if ts_file.exists() else []
    mp3 = ch_dir / rows[0]["file_mp3"] if rows else None
    if not rows or not mp3.exists() or not (ch_dir / "mo0.smil").exists():
        return None
    seg = json.loads((ch_dir / "segments.json").read_text(encoding="utf-8"))
    no = seg["chapter"]

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
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(
        {"slug": slug, "no": no, "voice": vid, "label": seg["label"], "title": seg["title"],
         "duration": duration, "paras": paras}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    shutil.copyfile(mp3, out_dir / f"{name}.mp3")
    return {"data": f"books/{slug}/{vid}/{name}.json", "audio": f"books/{slug}/{vid}/{name}.mp3",
            "duration": duration}


def write_daisy_zip(zip_path: Path, ch_dirs, single: bool):
    """Gói DAISY 3 đầy đủ của một giọng, để mở bằng Thorium / EasyReader."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for d in ch_dirs:
            prefix = "" if single else f"{d.name}/"
            for name in DAISY_FILES + [p.name for p in d.glob("chuong*.mp3")]:
                if (d / name).exists():
                    z.write(d / name, prefix + name)


def main(legacy_totto: bool):
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(WEB, SITE)
    (SITE / ".nojekyll").write_text("")          # GitHub Pages: phát nguyên trạng, không qua Jekyll
    # bản cài cho Android, để tải thẳng từ trang (mục Cài ứng dụng trong Hướng dẫn)
    apk = REPO / "app" / "android" / "SachNoi-1.0.0.apk"
    if apk.exists():
        shutil.copyfile(apk, SITE / "SachNoi.apk")
    # lời nhắc thu sẵn của chế độ chạm đơn giản (build_prompts.py), nếu đã thu
    if (REPO / "prompts" / "index.json").exists():
        shutil.copytree(REPO / "prompts", SITE / "prompts")
    # trang nghe thử so sánh giọng đọc (demo/make_listen_page.py), nếu đã tạo
    listen = REPO / "demo" / "outputs" / "nghe_thu"
    if (listen / "index.html").exists():
        shutil.copytree(listen, SITE / "nghe-thu")

    voice_info = {vid: {"id": vid, "label": v["label"], "name": v["name"]} for vid, v in VOICES.items()}
    for fb in FALLBACKS:
        voice_info[fb["id"]] = {"id": fb["id"], "label": fb["label"], "name": fb["name"], "fallback": True}
    books = []
    for meta_file in sorted(BOOKS.glob("*/metadata/book_meta.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        root, slug = meta_file.parent.parent, meta["book_slug"]
        ch_dirs = [d for d in sorted((root / "build").glob("chapter_*")) if (d / "segments.json").exists()]
        if not ch_dirs:
            continue
        out_dir = SITE / "books" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        units, daisy_dirs = [], {}
        for d in ch_dirs:
            seg = json.loads((d / "segments.json").read_text(encoding="utf-8"))
            voices = {}
            for vid in VOICES:   # các giọng cho người nghe chọn
                vdir = root / "voices" / vid / "build" / d.name
                built = build_unit(vdir, out_dir / vid, slug, vid) if (vdir / "segments.json").exists() else None
                if built:
                    voices[vid] = built
                    daisy_dirs.setdefault(vid, []).append(vdir)
            if not voices:   # chưa có giọng chính: kèm giọng dự phòng đầu tiên đang có
                for fb in FALLBACKS:
                    fdir = root / fb["dir"] / "build" / d.name if fb["dir"] else d
                    built = build_unit(fdir, out_dir / fb["id"], slug, fb["id"]) if (fdir / "segments.json").exists() else None
                    if built:
                        voices[fb["id"]] = built
                        daisy_dirs.setdefault(fb["id"], []).append(fdir)
                        break
            first = next(iter(voices.values()), None)
            units.append({"no": seg["chapter"], "label": seg["label"], "title": seg["title"],
                          "duration": first["duration"] if first else 0, "ready": bool(voices), "voices": voices})
        present = [vid for vid in voice_info if any(vid in u["voices"] for u in units)]
        if not any(u["ready"] for u in units):
            continue   # sách mới nhập, chưa phần nào có giọng đọc: chưa đưa lên thư viện
        chosen = [vid for vid in present if not voice_info[vid].get("fallback")] or present
        book = {
            "slug": slug, "title": meta["title"], "creator": meta["creator"], "subject": meta["subject"],
            "description": meta["description"], "date": meta["date"],
            "narrator": (meta.get("narrator", "") if chosen == ["piper"] else
                         ", ".join(f"{voice_info[v]['name']} ({voice_info[v]['label'].lower()})" for v in chosen)),
            "sourceURL": meta.get("sourceURL", ""), "note": meta.get("note", ""),
            "duration": round(sum(u["duration"] for u in units), 3),
            "voices": [voice_info[v] for v in present], "units": units, "daisy": {},
        }
        # bìa sách (make_covers.py) và nguồn ảnh bìa
        cover = meta_file.parent / "cover.jpg"
        if cover.exists():
            shutil.copyfile(cover, out_dir / "cover.jpg")
            book["cover"] = f"books/{slug}/cover.jpg"
            src = meta_file.parent / "cover_source.json"
            if src.exists():
                c = json.loads(src.read_text(encoding="utf-8"))
                book["coverCredit"] = {"text": f"{c['credit']} · {c['license']}", "url": c["page"]}
        # Sách dài: không kèm file zip tải về (GitHub Pages giới hạn 1 GB, zip lặp lại toàn bộ audio);
        # bộ file DAISY từng phần vẫn nằm trên trang.
        for vid, dirs in ({} if meta.get("no_zip") else daisy_dirs).items():
            zip_path = out_dir / f"{slug}-daisy-{vid}.zip"
            write_daisy_zip(zip_path, dirs, single=len(ch_dirs) == 1)
            book["daisy"][vid] = {"url": f"books/{slug}/{zip_path.name}", "size": human_size(zip_path.stat().st_size)}
        books.append(book)

    books.sort(key=lambda b: b["title"])
    if legacy_totto:
        books.append(LEGACY_TOTTO)
    (SITE / "catalog.json").write_text(
        json.dumps({"version": 2, "books": books}, ensure_ascii=False, indent=1), encoding="utf-8")

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
