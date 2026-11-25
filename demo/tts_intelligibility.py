#!/usr/bin/env python3
"""Đo độ rõ của giọng đọc: cho ASR nghe lại audio rồi so với văn bản gốc.

Cùng một tập đoạn văn, mỗi hệ TTS một thư mục audio (file <id>.wav hoặc <id>.mp3).
WER/CER tính sau khi chuẩn hóa: chữ thường, bỏ dấu câu, chuẩn Unicode NFC.
Sai số của bản thân ASR là như nhau cho mọi hệ, nên con số dùng để SO SÁNH
giữa các hệ chứ không phải độ rõ tuyệt đối.

Usage: .venv/bin/python demo/tts_intelligibility.py --slug lao-hac \
         --system edge-tts=books/lao-hac/build/chapter_01/audio_parts \
         --system piper-vais1000=demo/outputs/piper/vi_VN-vais1000-medium
"""
import argparse
import csv
import json
import re
import time
import unicodedata
from pathlib import Path

import av
import jiwer
import numpy as np
from faster_whisper import WhisperModel

REPO = Path(__file__).resolve().parent.parent


def load_16k(path) -> np.ndarray:
    """Giải mã wav/mp3 thành mono 16 kHz float32 (tự làm, vì hàm giải mã của
    faster-whisper không tương thích với bản PyAV đang cài)."""
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks = []
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="lao-hac")
    ap.add_argument("--system", action="append", required=True, help="tên=thư_mục_audio")
    ap.add_argument("--model", default="large-v3-turbo")
    a = ap.parse_args()

    systems = dict(s.split("=", 1) for s in a.system)
    segs = json.loads((REPO / "books" / a.slug / "build" / "chapter_01" / "segments.json")
                      .read_text(encoding="utf-8"))["segments"]

    def audio_of(d, sid):
        for ext in (".wav", ".mp3"):
            p = REPO / d / f"{sid}{ext}"
            if p.exists() and p.stat().st_size > 0:
                return p
        return None

    # chỉ chấm các đoạn mà MỌI hệ đều có audio, để so sánh công bằng
    common = [s for s in segs if all(audio_of(d, s["id"]) for d in systems.values())]
    print(f"{len(common)} đoạn chung, {sum(len(s['text']) for s in common)} ký tự")

    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    rows = []
    for name, d in systems.items():
        refs, hyps, t0 = [], [], time.perf_counter()
        for s in common:
            parts, _ = model.transcribe(load_16k(audio_of(d, s["id"])), language="vi", beam_size=5,
                                        condition_on_previous_text=False)
            hyp = norm(" ".join(p.text for p in parts))
            ref = norm(s["text"])
            refs.append(ref)
            hyps.append(hyp)
            rows.append({"system": name, "id": s["id"], "wer": round(jiwer.wer(ref, hyp), 4),
                         "cer": round(jiwer.cer(ref, hyp), 4), "ref": ref, "hyp": hyp})
        print(f"{name}: WER {100 * jiwer.wer(refs, hyps):.2f}% | CER {100 * jiwer.cer(refs, hyps):.2f}% "
              f"| ASR mất {time.perf_counter() - t0:.0f}s")

    out = REPO / "demo" / "outputs" / "intelligibility.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {out}")
