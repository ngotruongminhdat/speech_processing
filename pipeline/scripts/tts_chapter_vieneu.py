#!/usr/bin/env python3
"""TTS một đơn vị sách bằng VieNeu-TTS v3 Turbo (chạy cục bộ trên CPU qua ONNX).

Cùng đầu ra với tts_chapter_piper.py: chuongNN.mp3, timestamps.csv (mức đoạn,
cho SMIL/DAISY) và sentences.csv (mức câu, cho ứng dụng tô sáng và tua).

Khác Piper ở hai điểm:
  - Mô hình lớn hơn nhiều, ngữ điệu tự nhiên hơn, nhưng chậm hơn: chỉ nhanh hơn
    thời gian thực khoảng 1,5–2 lần trên CPU.
  - Mô hình sinh mẫu ngẫu nhiên, nên có thể đọc thiếu hoặc thừa chữ. Tùy chọn
    --verify cho ASR nghe lại từng câu và sinh lại câu nào lệch quá ngưỡng.

Usage: DAISY_BOOK_ROOT=books/lao-hac .venv/bin/python pipeline/scripts/tts_chapter_vieneu.py 1 --voice "Ngọc Linh"
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import lameenc
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _vieneu_local import SAMPLE_RATE, load_vieneu  # noqa: E402
from tts_chapter_piper import split_sentences  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
ROOT = Path(os.environ.get("DAISY_BOOK_ROOT") or REPO)
DEFAULT_VOICE = "Ngọc Linh"

SENT_PAUSE = 0.40   # nghỉ giữa hai câu trong cùng một đoạn (giây)
PARA_PAUSE = 0.80   # nghỉ sau mỗi đoạn văn
HEAD_PAUSE = 1.00   # nghỉ sau tiêu đề
EDGE_PAD = 0.04     # khoảng lặng giữ lại ở hai đầu mỗi câu sau khi cắt
OUT_RATE = 24_000   # mô hình ra 48 kHz; hạ xuống 24 kHz khi nén để file nhỏ như bản Piper
BITRATE_KBPS = 48   # như bản giữa kỳ
PACE_PRIOR = 0.235  # giây mỗi âm tiết, trung vị đo được trên "Gió lạnh đầu mùa"
PACE_MIN_SYL = 6    # câu ngắn hơn thì nhịp dao động tự nhiên quá lớn, không xét
PACE_LO, PACE_HI = 0.65, 1.6   # ngoài khoảng này so với trung vị thì coi là đọc sót / đọc thừa


def trim_silence(x: np.ndarray, thresh: float = 0.004) -> np.ndarray:
    """Cắt khoảng lặng thừa ở hai đầu, để khoảng nghỉ giữa các câu do pipeline quyết định."""
    win = SAMPLE_RATE // 100
    n = len(x) // win
    if n == 0:
        return x
    rms = np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(axis=1))
    loud = np.nonzero(rms > thresh)[0]
    if len(loud) == 0:
        return x
    pad = int(EDGE_PAD * SAMPLE_RATE)
    return x[max(0, loud[0] * win - pad): min(len(x), (loud[-1] + 1) * win + pad)]


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


class Verifier:
    """ASR nghe lại một câu; trả về tỉ lệ lỗi ký tự so với văn bản gốc."""

    def __init__(self):
        import jiwer
        import soxr
        from faster_whisper import WhisperModel
        self.jiwer, self.soxr = jiwer, soxr
        self.model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

    def cer(self, audio: np.ndarray, text: str) -> float:
        ref = norm(text)
        if not ref:
            return 0.0
        wav = self.soxr.resample(audio, SAMPLE_RATE, 16000).astype(np.float32)
        parts, _ = self.model.transcribe(wav, language="vi", beam_size=1, condition_on_previous_text=False)
        return self.jiwer.cer(ref, norm(" ".join(p.text for p in parts)) or "∅")


def main(chapter_no: int, voice: str, verify: bool, max_cer: float, tries: int):
    ch_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    seg_file = ch_dir / "segments.json"
    if not seg_file.exists():
        sys.exit(f"Chưa có {seg_file} — nhập sách trước (import_wikisource.py).")
    data = json.loads(seg_file.read_text(encoding="utf-8"))
    segments = data["segments"]

    tts = load_vieneu()
    checker = Verifier() if verify else None
    rate = SAMPLE_RATE

    def silence(sec: float) -> np.ndarray:
        return np.zeros(int(sec * rate), dtype=np.float32)

    paces = [PACE_PRIOR] * 5     # giây mỗi âm tiết của các câu gần đây, để biết nhịp đọc bình thường

    def infer_paced(sent: str) -> np.ndarray:
        """Sinh một câu, có lưới an toàn không tốn kém: mô hình sinh mẫu ngẫu nhiên nên
        đôi khi bỏ sót hoặc nói thừa chữ. Khi đó thời lượng lệch hẳn khỏi nhịp đọc bình
        thường (đo trên sách thật: mọi câu nằm trong 0,8–1,3 lần trung vị). Câu nào lệch
        quá ngưỡng thì sinh lại, giữ bản gần nhịp bình thường nhất."""
        nonlocal paced_retries
        n_syl = len(re.findall(r"\w+", sent))
        ref = float(np.median(paces[-40:]))
        best, best_dev = None, 9.0
        for attempt in range(3):
            audio = trim_silence(np.asarray(tts.infer(sent, voice=voice), dtype=np.float32))
            if n_syl < PACE_MIN_SYL:
                return audio
            ratio = len(audio) / rate / n_syl / ref
            dev = abs(np.log(ratio))
            if dev < best_dev:
                best, best_dev, best_pace = audio, dev, ratio * ref
            if PACE_LO <= ratio <= PACE_HI:
                break
            paced_retries += 1
        if PACE_LO <= best_pace / ref <= PACE_HI:
            paces.append(best_pace)
        return best

    def synth(sent: str):
        """Sinh một câu; nếu bật kiểm tra thì giữ bản có CER thấp nhất trong `tries` lần."""
        best, best_cer, n = None, 9.0, 0
        while n < (tries if checker else 1):
            n += 1
            audio = infer_paced(sent)
            if not checker:
                return audio, None, 1
            cer = checker.cer(audio, sent)
            if cer < best_cer:
                best, best_cer = audio, cer
            if cer <= max_cer:
                break
        return best, best_cer, n

    label = data.get("label") or ("Phần mở đầu" if chapter_no == 0 else f"Chương {chapter_no}")
    mp3_name = f"chuong{chapter_no:02d}.mp3"
    pcm, cursor = [], 0          # cursor tính bằng số mẫu
    seg_rows, sent_rows, qa_rows = [], [], []
    retried = flagged = paced_retries = 0
    t0 = time.perf_counter()

    for i, seg in enumerate(segments):
        text = seg["text"]
        if i == 0 and seg["type"] == "h1" and not text.startswith(label):
            text = f"{label}. {text}"
        seg_begin = cursor
        sentences = split_sentences(text)
        for k, sent in enumerate(sentences, start=1):
            audio, cer, n = synth(sent)
            if checker:
                retried += n > 1
                flagged += cer > max_cer
                qa_rows.append([seg["id"], k, n, f"{cer:.3f}", sent])
            sent_begin = cursor
            pcm.append(audio)
            cursor += len(audio)
            sent_rows.append([seg["id"], k, f"{sent_begin / rate:.3f}", f"{cursor / rate:.3f}", sent])
            if k < len(sentences):
                pcm.append(silence(SENT_PAUSE))
                cursor += len(pcm[-1])
        pause = silence(HEAD_PAUSE if seg["type"] == "h1" else PARA_PAUSE)
        pcm.append(pause)
        cursor += len(pause)
        seg_rows.append([seg["id"], mp3_name, f"{seg_begin / rate:.3f}", f"{cursor / rate:.3f}"])
        if (i + 1) % 10 == 0:
            print(f"   … {i + 1}/{len(segments)} đoạn, {cursor / rate / 60:.1f} phút audio, "
                  f"{time.perf_counter() - t0:.0f}s", flush=True)

    gen_s = time.perf_counter() - t0
    audio_s = cursor / rate

    import soxr
    wav = np.clip(soxr.resample(np.concatenate(pcm), rate, OUT_RATE), -1.0, 1.0)
    enc = lameenc.Encoder()
    enc.set_bit_rate(BITRATE_KBPS)
    enc.set_in_sample_rate(OUT_RATE)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3 = enc.encode((wav * 32767).astype(np.int16).tobytes()) + enc.flush()
    (ch_dir / mp3_name).write_bytes(bytes(mp3))

    with open(ch_dir / "timestamps.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "file_mp3", "clipBegin", "clipEnd"])
        w.writerows(seg_rows)
    with open(ch_dir / "sentences.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sent_no", "clipBegin", "clipEnd", "text"])
        w.writerows(sent_rows)
    if checker:
        with open(ch_dir / "tts_qa.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "sent_no", "tries", "cer", "text"])
            w.writerows(qa_rows)

    print(f"✅ {mp3_name}: {audio_s / 60:.1f} phút, {len(seg_rows)} đoạn, {len(sent_rows)} câu "
          f"| tạo trong {gen_s:.0f}s (RTF {gen_s / audio_s:.3f}) | giọng VieNeu {voice}"
          f" | {paced_retries} lần sinh lại vì lệch nhịp")
    if checker:
        print(f"   kiểm tra bằng ASR: {retried} câu phải sinh lại, {flagged} câu vẫn lệch quá {max_cer:.0%} "
              f"-> {ch_dir / 'tts_qa.csv'}")
    print(f"   -> {ch_dir / mp3_name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--verify", action="store_true", help="ASR nghe lại từng câu, sinh lại câu lệch")
    ap.add_argument("--max-cer", type=float, default=0.15)
    ap.add_argument("--tries", type=int, default=3)
    a = ap.parse_args()
    main(a.chapter, a.voice, a.verify, a.max_cer, a.tries)
