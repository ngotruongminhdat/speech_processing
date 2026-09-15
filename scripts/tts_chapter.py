#!/usr/bin/env python3
"""TTS tạm cho 1 chương (thay cho phần của Vy) -> chuongNN.mp3 + timestamps.csv.

Dùng edge-tts (giọng vi-VN-HoaiMyNeural, miễn phí) để đọc từng đoạn,
ghép thành 1 file mp3/chương và ghi lại timestamp chính xác của từng đoạn.

Output timestamps.csv đúng format đã chốt với Vy:
  id,file_mp3,clipBegin,clipEnd   (giây, 3 số lẻ)

Khi Vy giao mp3 + timestamps thật (từ Azure TTS), chỉ cần thay 2 file này,
các bước sau không đổi.

Usage: .venv/bin/python scripts/tts_chapter.py 1 [--voice vi-VN-NamMinhNeural]
"""
import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VOICE = "vi-VN-HoaiMyNeural"


async def synth_segment(text: str, voice: str, out_path: Path, retries: int = 3):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice).save(str(out_path))
            if out_path.stat().st_size > 0:
                return
        except Exception as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 * (attempt + 1))


async def main(chapter_no: int, voice: str):
    ch_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    seg_file = ch_dir / "segments.json"
    if not seg_file.exists():
        sys.exit(f"Chưa có {seg_file} — chạy extract_chapter.py {chapter_no} trước.")
    data = json.loads(seg_file.read_text(encoding="utf-8"))
    segments = data["segments"]

    parts_dir = ch_dir / "audio_parts"
    parts_dir.mkdir(exist_ok=True)

    # 1. TTS từng đoạn -> file mp3 nhỏ
    # Riêng tiêu đề đầu chương: xướng thêm số chương ("Chương 1. Nhà ga")
    # như audiobook chuẩn — text hiển thị trong dtbook vẫn giữ nguyên.
    prefix = "Phần mở đầu. " if chapter_no == 0 else f"Chương {chapter_no}. "
    for i, seg in enumerate(segments):
        part = parts_dir / f"{seg['id']}.mp3"
        if part.exists() and part.stat().st_size > 0:
            continue  # cho phép chạy lại không tốn công đoạn đã xong
        text = seg["text"]
        if i == 0 and seg["type"] == "h1" and (chapter_no > 0 or not text.startswith("Phần mở đầu")):
            text = prefix + text
        await synth_segment(text, voice, part)
        print(f"  [{i + 1}/{len(segments)}] {seg['id']} ({len(text)} ký tự)")

    # 2. Ghép thành 1 mp3/chương + tính timestamp từ độ dài từng phần
    mp3_name = f"chuong{chapter_no:02d}.mp3"
    rows, cursor = [], 0.0
    with open(ch_dir / mp3_name, "wb") as out:
        for seg in segments:
            part = parts_dir / f"{seg['id']}.mp3"
            dur = MP3(part).info.length
            out.write(part.read_bytes())
            rows.append([seg["id"], mp3_name, f"{cursor:.3f}", f"{cursor + dur:.3f}"])
            cursor += dur

    with open(ch_dir / "timestamps.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "file_mp3", "clipBegin", "clipEnd"])
        w.writerows(rows)

    print(f"✅ {mp3_name}: {cursor / 60:.1f} phút, {len(rows)} đoạn")
    print(f"   -> {ch_dir / mp3_name}")
    print(f"   -> {ch_dir / 'timestamps.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    args = ap.parse_args()
    asyncio.run(main(args.chapter, args.voice))
