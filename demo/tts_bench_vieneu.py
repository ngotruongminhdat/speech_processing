#!/usr/bin/env python3
"""Đo tốc độ VieNeu-TTS v3 Turbo trên CPU với các đoạn văn thật của một cuốn sách.

Cùng cách đo với demo/tts_bench_piper.py: đọc N đoạn đầu của
books/<slug>/build/chapter_01/segments.json, ghi wav vào
demo/outputs/vieneu/<giọng>/ và tính RTF = thời gian tạo / thời lượng audio.
Mô hình sinh mẫu ngẫu nhiên nên mỗi lần chạy cho audio hơi khác nhau.

Usage: .venv/bin/python demo/tts_bench_vieneu.py --slug lao-hac --n 20 --voices "Ngọc Linh" "Thiện Minh"
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "pipeline" / "scripts"))
from _vieneu_local import SAMPLE_RATE, load_vieneu  # noqa: E402


def slug_of(name: str) -> str:
    s = unicodedata.normalize("NFD", name.replace("Đ", "D").replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="lao-hac")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--voices", nargs="*", default=["Ngọc Linh"])
    a = ap.parse_args()

    segs = json.loads((REPO / "books" / a.slug / "build" / "chapter_01" / "segments.json")
                      .read_text(encoding="utf-8"))["segments"][: a.n]
    t0 = time.perf_counter()
    tts = load_vieneu()
    load_s = time.perf_counter() - t0
    tts.infer("Xin chào.", voice=a.voices[0])   # làm nóng, không tính giờ
    print(f"nạp mô hình {load_s:.1f}s", flush=True)

    rows = []
    for name in a.voices:
        out_dir = REPO / "demo" / "outputs" / "vieneu" / slug_of(name)
        out_dir.mkdir(parents=True, exist_ok=True)
        gen_total = audio_total = 0.0
        for seg in segs:
            t0 = time.perf_counter()
            audio = tts.infer(seg["text"], voice=name)
            gen = time.perf_counter() - t0
            dur = len(audio) / SAMPLE_RATE
            tts.save(audio, str(out_dir / f"{seg['id']}.wav"))
            gen_total += gen
            audio_total += dur
            rows.append({"voice": name, "id": seg["id"], "chars": len(seg["text"]),
                         "gen_s": round(gen, 3), "audio_s": round(dur, 3), "rtf": round(gen / dur, 4)})
        print(f"{name}: {len(segs)} đoạn | audio {audio_total:.1f}s | tạo {gen_total:.1f}s "
              f"| RTF {gen_total / audio_total:.3f} (nhanh gấp {audio_total / gen_total:.1f} lần thời gian thực)",
              flush=True)

    out = REPO / "demo" / "outputs" / "vieneu_speed.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("→", out.relative_to(REPO))
