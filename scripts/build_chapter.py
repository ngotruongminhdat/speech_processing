#!/usr/bin/env python3
"""Chạy trọn pipeline cho 1 chương: extract -> TTS -> smil -> opf/ncx -> validate -> package.

Khi có dữ liệu thật từ Lộc (dtbook.xml) và Vy (mp3 + timestamps.csv),
đặt file vào build/chapter_NN/ rồi chạy với --skip-extract --skip-tts.

Usage:
  .venv/bin/python scripts/build_chapter.py 1
  .venv/bin/python scripts/build_chapter.py 1 --skip-extract --skip-tts
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(script, *args):
    cmd = [PY, str(ROOT / "scripts" / script), *map(str, args)]
    print(f"\n=== {script} {' '.join(map(str, args))} ===")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    ap.add_argument("--skip-extract", action="store_true", help="đã có dtbook.xml thật từ Lộc")
    ap.add_argument("--skip-tts", action="store_true", help="đã có mp3 + timestamps thật từ Vy")
    ap.add_argument("--voice", default="vi-VN-HoaiMyNeural")
    a = ap.parse_args()

    if not a.skip_extract:
        run("extract_chapter.py", a.chapter)
    if not a.skip_tts:
        run("tts_chapter.py", a.chapter, "--voice", a.voice)
    run("gen_smil.py", a.chapter)
    run("gen_opf_ncx.py", a.chapter)
    run("validate_daisy.py", a.chapter)
    run("package_book.py", a.chapter)
    print("\n🎉 Hoàn tất — mở dist/... bằng Thorium Reader để kiểm tra.")
