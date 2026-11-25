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
  .venv/bin/python pipeline/scripts/build_book.py tat-den --only 1-9      # dựng dần từng đợt
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))
from voices import TTS_SCRIPT, VOICES, narrator  # noqa: E402


def run(script, env, *args):
    print(f"\n=== {script} {' '.join(map(str, args))} ===", flush=True)
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True, env=env)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--only", metavar="A-B", help="chỉ dựng các phần từ A đến B, ví dụ 1-9 (để deploy dần)")
    ap.add_argument("--engine", choices=["piper", "edge"], default="piper")
    ap.add_argument("--voice-id", choices=list(VOICES),
                    help="dựng một giọng của thư viện (voices.py) vào books/<slug>/voices/<id>/")
    ap.add_argument("--verify", action="store_true", help="(giọng VieNeu) ASR nghe lại từng câu, sinh lại câu lệch")
    ap.add_argument("--voice", help="mặc định: vi_VN-vais1000-medium (piper) / vi-VN-HoaiMyNeural (edge)")
    a = ap.parse_args()
    tts_script = "tts_chapter_piper.py" if a.engine == "piper" else "tts_chapter.py"
    voice = a.voice or ("vi_VN-vais1000-medium" if a.engine == "piper" else "vi-VN-HoaiMyNeural")
    tts_args = ["--voice", voice]

    src_root = book_root = REPO / "books" / a.slug
    units = sorted(int(p.name.split("_")[1]) for p in (src_root / "build").glob("chapter_*")
                   if (p / "segments.json").exists())
    if a.voice_id:
        # mỗi giọng là một bản DAISY riêng: chép văn bản nguồn sang thư mục của giọng đó
        spec = VOICES[a.voice_id]
        tts_script, voice = TTS_SCRIPT[spec["engine"]], spec["voice"]
        tts_args = ["--voice", voice] + (["--verify"] if a.verify and spec["engine"] == "vieneu" else [])
        book_root = src_root / "voices" / a.voice_id
        (book_root / "metadata").mkdir(parents=True, exist_ok=True)
        meta = json.loads((src_root / "metadata" / "book_meta.json").read_text(encoding="utf-8"))
        meta["narrator"] = narrator(a.voice_id)
        (book_root / "metadata" / "book_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    if not units:
        sys.exit(f"Không có đơn vị nào trong {book_root / 'build'} — chạy import_wikisource.py trước.")
    if a.only:
        lo, _, hi = a.only.partition("-")
        units = [n for n in units if int(lo) <= n <= int(hi or lo)]

    env = {**os.environ, "DAISY_BOOK_ROOT": str(book_root)}
    for no in units:
        if a.voice_id:
            ch = book_root / "build" / f"chapter_{no:02d}"
            ch.mkdir(parents=True, exist_ok=True)
            for name in ("segments.json", "dtbook.xml"):
                shutil.copyfile(src_root / "build" / ch.name / name, ch / name)
        if not a.skip_tts:
            run(tts_script, env, no, *tts_args)
        run("gen_smil.py", env, no)
        run("gen_opf_ncx.py", env, no)
        run("validate_daisy.py", env, no)
    if not a.skip_tts and not a.voice_id:
        # ghi lại giọng đọc thật sự đã dùng để app hiển thị đúng
        meta_file = book_root / "metadata" / "book_meta.json"
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta["narrator"] = (f"Piper {voice} (giọng tổng hợp mã nguồn mở)" if a.engine == "piper"
                            else f"{voice} (Microsoft Neural TTS)")
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    run("build_catalog.py", os.environ)
    print(f"\n🎉 {a.slug}: {len(units)} đơn vị đã dựng và kiểm tra xong.")
