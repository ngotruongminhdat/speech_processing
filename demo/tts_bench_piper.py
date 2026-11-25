#!/usr/bin/env python3
"""Đo tốc độ Piper TTS tiếng Việt trên CPU với các đoạn văn thật của một cuốn sách.

Với mỗi giọng: đọc N đoạn đầu của books/<slug>/build/chapter_01/segments.json,
ghi wav vào demo/outputs/piper/<giọng>/ và in RTF = thời gian tạo / thời lượng audio
(RTF < 1 là nhanh hơn thời gian thực). Kết quả chi tiết ghi ra CSV.

Usage: .venv/bin/python demo/tts_bench_piper.py --slug lao-hac --n 20
"""
import argparse
import csv
import json
import time
import wave
from pathlib import Path

from piper import PiperVoice

REPO = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="lao-hac")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--voices", nargs="*", default=["vi_VN-vais1000-medium", "vi_VN-25hours_single-low"])
    a = ap.parse_args()

    segs = json.loads((REPO / "books" / a.slug / "build" / "chapter_01" / "segments.json")
                      .read_text(encoding="utf-8"))["segments"][: a.n]
    out_root = REPO / "demo" / "outputs" / "piper"
    rows = []
    for name in a.voices:
        t0 = time.perf_counter()
        voice = PiperVoice.load(REPO / "models" / "piper" / f"{name}.onnx")
        load_s = time.perf_counter() - t0
        out_dir = out_root / name
        out_dir.mkdir(parents=True, exist_ok=True)
        gen_total = audio_total = 0.0
        for seg in segs:
            path = out_dir / f"{seg['id']}.wav"
            t0 = time.perf_counter()
            n_sent = samples = 0
            with wave.open(str(path), "wb") as wf:
                for chunk in voice.synthesize(seg["text"]):   # mỗi chunk là một câu
                    if n_sent == 0:
                        wf.setnchannels(chunk.sample_channels)
                        wf.setsampwidth(chunk.sample_width)
                        wf.setframerate(chunk.sample_rate)
                        rate = chunk.sample_rate
                    wf.writeframes(chunk.audio_int16_bytes)
                    samples += len(chunk.audio_int16_array)
                    n_sent += 1
            gen = time.perf_counter() - t0
            dur = samples / rate
            gen_total += gen
            audio_total += dur
            rows.append({"voice": name, "id": seg["id"], "chars": len(seg["text"]), "sentences": n_sent,
                         "gen_s": round(gen, 3), "audio_s": round(dur, 3), "rtf": round(gen / dur, 4)})
        print(f"{name}: nạp mô hình {load_s:.2f}s | {len(segs)} đoạn | audio {audio_total:.1f}s "
              f"| tạo {gen_total:.1f}s | RTF {gen_total / audio_total:.3f} "
              f"(nhanh gấp {audio_total / gen_total:.1f} lần thời gian thực)")

    csv_path = out_root / "bench.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {csv_path}")
