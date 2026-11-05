#!/usr/bin/env python3
"""Dựng lần lượt các giọng đọc (voices.py) cho nhiều cuốn sách, deploy dần.

Mỗi lượt lấy một nhóm vài phần của một cuốn, dựng đủ mọi giọng cho nhóm đó rồi
deploy, để người nghe thấy sách mới xuất hiện dần thay vì chờ cả thư viện.
Phần nào đã dựng xong (có mo0.smil và mp3 trong thư mục của giọng) thì bỏ qua,
nên có thể dừng và chạy lại bất cứ lúc nào.

Usage:
  .venv/bin/python pipeline/scripts/build_voices.py                       # mọi sách, ngắn trước
  .venv/bin/python pipeline/scripts/build_voices.py lao-hac tat-den --batch 3
  .venv/bin/python pipeline/scripts/build_voices.py --deploy-when /tmp/ok   # chỉ deploy khi file này tồn tại
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))
from voices import VOICES  # noqa: E402


def units_of(slug):
    return sorted(int(p.name.split("_")[1]) for p in (REPO / "books" / slug / "build").glob("chapter_*")
                  if (p / "segments.json").exists())


def done(slug, vid, no):
    ch = REPO / "books" / slug / "voices" / vid / "build" / f"chapter_{no:02d}"
    return (ch / "mo0.smil").exists() and (ch / f"chuong{no:02d}.mp3").exists()


def text_size(slug):
    return sum(len(s["text"]) for no in units_of(slug) for s in json.loads(
        (REPO / "books" / slug / "build" / f"chapter_{no:02d}" / "segments.json").read_text(encoding="utf-8"))["segments"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--voices", nargs="*", default=list(VOICES), choices=list(VOICES))
    ap.add_argument("--batch", type=int, default=3, help="số phần mỗi lượt trước khi deploy")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--deploy", action="store_true", help="deploy sau mỗi lượt")
    ap.add_argument("--deploy-when", type=Path, help="deploy sau mỗi lượt, nhưng chỉ khi file này tồn tại")
    a = ap.parse_args()

    slugs = a.slugs or sorted((p.parent.parent.name for p in (REPO / "books").glob("*/metadata/book_meta.json")),
                              key=text_size)
    t0 = time.time()
    for slug in slugs:
        units = units_of(slug)
        for i in range(0, len(units), a.batch):
            group = units[i:i + a.batch]
            built = False
            for vid in a.voices:
                for no in group:
                    if done(slug, vid, no):
                        continue
                    cmd = [sys.executable, str(SCRIPTS / "build_book.py"), slug, "--voice-id", vid, "--only", str(no)]
                    subprocess.run(cmd + (["--verify"] if a.verify else []), check=True)
                    built = True
            print(f"\n##### {slug} phần {group[0]}–{group[-1]}: đủ giọng {', '.join(a.voices)} "
                  f"| đã chạy {(time.time() - t0) / 60:.0f} phút #####", flush=True)
            if built and (a.deploy or (a.deploy_when and a.deploy_when.exists())):
                subprocess.run([sys.executable, str(SCRIPTS / "deploy_site.py")], check=False)
    print(f"\n🎉 Xong mọi giọng cho: {', '.join(slugs)} | {(time.time() - t0) / 60:.0f} phút")
