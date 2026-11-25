#!/usr/bin/env python3
"""TTS một đơn vị bằng Piper (chạy cục bộ trên CPU) -> chuongNN.mp3 + timestamps.csv.

Thay cho tts_chapter.py (edge-tts, dịch vụ ngoài hay bị bóp tần suất). Đầu ra
giữ đúng hợp đồng cũ nên các bước sau (gen_smil, gen_opf_ncx, validate_daisy)
không đổi:
  timestamps.csv : id,file_mp3,clipBegin,clipEnd   (mức đoạn, giây, 3 số lẻ)

Thêm so với bản cũ:
  sentences.csv  : id,sent_no,clipBegin,clipEnd,text  (mức câu, để app tô sáng
                   và tua theo câu; bước DAISY hiện chưa dùng)

Mốc thời gian tính từ số mẫu PCM trước khi nén, và cả đơn vị được nén MP3 một
lần duy nhất, nên không có sai số cộng dồn giữa các đoạn.

Usage: .venv/bin/python pipeline/scripts/tts_chapter_piper.py 1 [--voice vi_VN-vais1000-medium]
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import lameenc
import numpy as np
from piper import PiperVoice, SynthesisConfig

REPO = Path(__file__).resolve().parent.parent.parent
ROOT = Path(os.environ.get("DAISY_BOOK_ROOT") or REPO)
DEFAULT_VOICE = "vi_VN-vais1000-medium"

SENT_PAUSE = 0.25   # nghỉ giữa hai câu trong cùng một đoạn (giây)
PARA_PAUSE = 0.60   # nghỉ sau mỗi đoạn văn
HEAD_PAUSE = 0.90   # nghỉ sau tiêu đề
BITRATE_KBPS = 48   # như bản giữa kỳ

def split_sentences(text: str):
    """Tách câu sau . ! ? … (kể cả "...") cùng dấu đóng ngoặc/nháy đi kèm."""
    parts, start = [], 0
    for m in re.finditer(r'[.!?…]+["”’)\]]*\s+', text):
        parts.append(text[start:m.end()].strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    # câu chỉ gồm dấu câu (ví dụ "...") gộp vào câu trước để không sinh audio rỗng
    merged = []
    for p in parts:
        if merged and not re.search(r"\w", p):
            merged[-1] += " " + p
        else:
            merged.append(p)
    return [p for p in merged if re.search(r"\w", p)] or [text]


def synth(voice: PiperVoice, text: str, cfg: SynthesisConfig) -> np.ndarray:
    chunks = [c.audio_int16_array for c in voice.synthesize(text, cfg)]
    return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int16)


def main(chapter_no: int, voice_name: str, length_scale: float):
    ch_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    seg_file = ch_dir / "segments.json"
    if not seg_file.exists():
        sys.exit(f"Chưa có {seg_file} — nhập sách trước (import_wikisource.py).")
    data = json.loads(seg_file.read_text(encoding="utf-8"))
    segments = data["segments"]

    model = REPO / "models" / "piper" / f"{voice_name}.onnx"
    if not model.exists():
        sys.exit(f"Thiếu mô hình {model} — tải từ huggingface.co/rhasspy/piper-voices (vi/vi_VN).")
    voice = PiperVoice.load(model)
    rate = voice.config.sample_rate
    cfg = SynthesisConfig(length_scale=length_scale)

    def silence(sec: float) -> np.ndarray:
        return np.zeros(int(sec * rate), dtype=np.int16)

    label = data.get("label") or ("Phần mở đầu" if chapter_no == 0 else f"Chương {chapter_no}")
    mp3_name = f"chuong{chapter_no:02d}.mp3"
    pcm, cursor = [], 0          # cursor tính bằng số mẫu
    seg_rows, sent_rows = [], []
    t0 = time.perf_counter()

    for i, seg in enumerate(segments):
        text = seg["text"]
        # tiêu đề đầu đơn vị: xướng thêm nhãn ("Chương 1. Nhà ga") như bản giữa kỳ
        if i == 0 and seg["type"] == "h1" and not text.startswith(label):
            text = f"{label}. {text}"
        seg_begin = cursor
        sentences = split_sentences(text)
        for k, sent in enumerate(sentences, start=1):
            audio = synth(voice, sent, cfg)
            sent_begin = cursor
            pcm.append(audio)
            cursor += len(audio)
            sent_rows.append([seg["id"], k, f"{sent_begin / rate:.3f}", f"{cursor / rate:.3f}", sent])
            if k < len(sentences):
                pcm.append(silence(SENT_PAUSE))
                cursor += len(pcm[-1])
        # khoảng nghỉ sau đoạn thuộc về chính đoạn đó, để các clip nối liền nhau
        pause = silence(HEAD_PAUSE if seg["type"] == "h1" else PARA_PAUSE)
        pcm.append(pause)
        cursor += len(pause)
        seg_rows.append([seg["id"], mp3_name, f"{seg_begin / rate:.3f}", f"{cursor / rate:.3f}"])

    gen_s = time.perf_counter() - t0
    audio_s = cursor / rate

    enc = lameenc.Encoder()
    enc.set_bit_rate(BITRATE_KBPS)
    enc.set_in_sample_rate(rate)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3 = enc.encode(np.concatenate(pcm).tobytes()) + enc.flush()
    (ch_dir / mp3_name).write_bytes(bytes(mp3))

    with open(ch_dir / "timestamps.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "file_mp3", "clipBegin", "clipEnd"])
        w.writerows(seg_rows)
    with open(ch_dir / "sentences.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sent_no", "clipBegin", "clipEnd", "text"])
        w.writerows(sent_rows)

    print(f"✅ {mp3_name}: {audio_s / 60:.1f} phút, {len(seg_rows)} đoạn, {len(sent_rows)} câu "
          f"| tạo trong {gen_s:.0f}s (RTF {gen_s / audio_s:.3f}) | giọng {voice_name}")
    print(f"   -> {ch_dir / mp3_name}")
    print(f"   -> {ch_dir / 'timestamps.csv'} , {ch_dir / 'sentences.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--length-scale", type=float, default=1.0,
                    help="> 1 đọc chậm hơn, < 1 đọc nhanh hơn")
    a = ap.parse_args()
    main(a.chapter, a.voice, a.length_scale)
