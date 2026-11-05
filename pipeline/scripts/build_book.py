#!/usr/bin/env python3
"""Dựng trọn một cuốn sách đã nhập (books/<slug>/) thành DAISY 3, rồi cập nhật danh mục.

Chạy cho mọi đơn vị build/chapter_NN/ đã có segments.json + dtbook.xml:
  TTS -> gen_smil -> gen_opf_ncx -> validate_daisy

Engine TTS:
  piper (mặc định) : chạy cục bộ trên CPU, nhanh hơn thời gian thực nhiều lần
  edge             : edge-tts như bản giữa kỳ; dịch vụ ngoài, hay bị bóp tần suất

Usage:
  .venv/bin/python pipeline/scripts/build_book.py lao-hac
  .venv/bin/python pipeline/scripts/build_book.py lao-hac --engine edge
  .venv/bin/python pipeline/scripts/build_book.py lao-hac --skip-tts
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent


def run(script, env, *args):
    print(f"\n=== {script} {' '.join(map(str, args))} ===", flush=True)
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True, env=env)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--engine", choices=["piper", "edge"], default="piper")
    ap.add_argument("--voice", help="mặc định: vi_VN-vais1000-medium (piper) / vi-VN-HoaiMyNeural (edge)")
    a = ap.parse_args()
    tts_script = "tts_chapter_piper.py" if a.engine == "piper" else "tts_chapter.py"
    voice = a.voice or ("vi_VN-vais1000-medium" if a.engine == "piper" else "vi-VN-HoaiMyNeural")

    book_root = REPO / "books" / a.slug
    units = sorted(int(p.name.split("_")[1]) for p in (book_root / "build").glob("chapter_*")
                   if (p / "segments.json").exists())
    if not units:
        sys.exit(f"Không có đơn vị nào trong {book_root / 'build'} — chạy import_wikisource.py trước.")

    env = {**os.environ, "DAISY_BOOK_ROOT": str(book_root)}
    for no in units:
        if not a.skip_tts:
            run(tts_script, env, no, "--voice", voice)
        run("gen_smil.py", env, no)
        run("gen_opf_ncx.py", env, no)
        run("validate_daisy.py", env, no)
    if not a.skip_tts:
        # ghi lại giọng đọc thật sự đã dùng để app hiển thị đúng
        meta_file = book_root / "metadata" / "book_meta.json"
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta["narrator"] = (f"Piper {voice} (giọng tổng hợp mã nguồn mở)" if a.engine == "piper"
                            else f"{voice} (Microsoft Neural TTS)")
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    run("build_catalog.py", os.environ)
    print(f"\n🎉 {a.slug}: {len(units)} đơn vị đã dựng và kiểm tra xong.")
