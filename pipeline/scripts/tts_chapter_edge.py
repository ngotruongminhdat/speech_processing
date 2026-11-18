#!/usr/bin/env python3
"""Đọc một chương bằng giọng Microsoft (edge-tts, mặc định vi-VN-HoaiMyNeural),
ra cùng bộ file như tts_chapter_vieneu.py: chuongNN.mp3, timestamps.csv (mức
đoạn) và sentences.csv (mức câu).

Khác bản giữa kỳ (tts_chapter.py): đọc cả đoạn văn một lần để giữ ngữ điệu liền
mạch, nhưng vẫn có mốc câu nhờ sự kiện WordBoundary mà dịch vụ trả về kèm audio
(mốc bắt đầu và độ dài của từng từ). Các từ được gán lần lượt vào các câu do
split_sentences tách ra; đo trên sách thật, chuỗi từ hai bên khớp nhau 100%.

Dịch vụ miễn phí, không cam kết: từng đoạn đã tải về được giữ trong audio_parts/
để chạy lại không tốn công, và mỗi đoạn được thử lại nhiều lần trước khi bỏ cuộc.

Dùng:  DAISY_BOOK_ROOT=books/<slug>/voices/hm python3 tts_chapter_edge.py 1
"""
import argparse
import asyncio
import csv
import io
import json
import os
import re
import sys
import time
from pathlib import Path

import av
import edge_tts
import lameenc
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts_chapter_piper import split_sentences  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
ROOT = Path(os.environ.get("DAISY_BOOK_ROOT") or REPO)
DEFAULT_VOICE = "vi-VN-HoaiMyNeural"

RATE = 24_000        # edge-tts trả mp3 24 kHz mono; giữ nguyên tần số
BITRATE_KBPS = 64    # nén lại một lần nữa nên để cao hơn 48 kbps của nguồn để ít mất mát
PARA_PAUSE = 0.80    # nghỉ sau mỗi đoạn văn (giây); nghỉ giữa câu trong đoạn do giọng đọc tự quyết
HEAD_PAUSE = 1.00    # nghỉ sau tiêu đề
EDGE_PAD = 0.06      # khoảng lặng giữ lại ở hai đầu mỗi đoạn sau khi cắt
RETRIES = 60
FETCH_TIMEOUT = 120  # giây cho một đoạn văn, kể cả lúc chờ máy chủ
TRUNC_RETRIES = 8    # sau ngần này lần vẫn thiếu từ thì chấp nhận (cách tách từ hai bên khác nhau)
GAP = 0.3            # giãn nhịp giữa hai yêu cầu, tránh bị bóp tần suất
PARALLEL = int(os.environ.get("EDGE_PARALLEL", "4"))   # số đoạn tải cùng lúc
TOKEN = re.compile(r"\w+")


def decode_mp3(data: bytes) -> np.ndarray:
    with av.open(io.BytesIO(data)) as c:
        st = c.streams.audio[0]
        if st.rate != RATE:
            raise RuntimeError(f"edge-tts trả {st.rate} Hz, mong {RATE} Hz")
        x = np.concatenate([f.to_ndarray() for f in c.decode(st)], axis=1)
    return (x.mean(axis=0) if x.ndim == 2 else x).astype(np.float32)


def trim_bounds(x: np.ndarray, thresh: float = 0.004):
    """Chỉ số mẫu [đầu, cuối) của phần có tiếng, cộng thêm EDGE_PAD mỗi bên."""
    win = RATE // 100
    n = len(x) // win
    if n == 0:
        return 0, len(x)
    rms = np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(axis=1))
    loud = np.nonzero(rms > thresh)[0]
    if len(loud) == 0:
        return 0, len(x)
    pad = int(EDGE_PAD * RATE)
    return max(0, loud[0] * win - pad), min(len(x), (loud[-1] + 1) * win + pad)


async def fetch(text: str, voice: str):
    """Audio mp3 và danh sách từ [(bắt đầu, độ dài, chữ)] tính bằng giây."""
    for attempt in range(RETRIES):
        try:
            audio, words = bytearray(), []

            async def pull():
                async for ch in edge_tts.Communicate(text, voice, boundary="WordBoundary").stream():
                    if ch["type"] == "audio":
                        audio.extend(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append([ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]])

            # có lần kết nối treo im lặng hơn 30 phút dù thư viện đã đặt hạn đọc: chặn trên toàn bộ
            await asyncio.wait_for(pull(), FETCH_TIMEOUT)
            if not audio:
                raise RuntimeError("không nhận được audio")
            # dịch vụ đôi khi trả audio cụt, thiếu vài từ cuối (3 đoạn trong Tắt đèn):
            # số từ nhận về phải bằng số từ gửi đi, không thì coi như lỗi và tải lại
            sent = len(TOKEN.findall(text))
            got = sum(len(TOKEN.findall(w[2])) for w in words)
            if got < sent and attempt < TRUNC_RETRIES:
                raise RuntimeError(f"audio cụt: nhận {got}/{sent} từ")
            return bytes(audio), words
        except Exception as e:      # dịch vụ chập chờn theo từng kết nối: thử lại dày, nghỉ ngắn
            if attempt == RETRIES - 1:
                raise
            print(f"   ! lần {attempt + 1}: {type(e).__name__}: {str(e)[:80]} — thử lại", flush=True)
            # Đo ngày 18/11: mỗi lần gọi hỏng với xác suất khoảng 3/4 bất kể đã chờ bao lâu,
            # nên chờ ngắn; chỉ khi hỏng liên tiếp nhiều lần mới coi là bị bóp theo đợt và chờ dài dần.
            await asyncio.sleep(0.5 if attempt < 12 else min(30, attempt - 8))


def sentence_spans(text: str, words, total: float):
    """Mốc [bắt đầu, kết thúc] của từng câu, tính theo giây trong audio của đoạn.

    Gán lần lượt các từ dịch vụ trả về vào các câu theo số lượng từ của mỗi câu.
    Nếu hai cách tách từ không khớp (hiếm) thì chia thời lượng theo số ký tự."""
    sentences = split_sentences(text)
    ours = [t.lower() for t in TOKEN.findall(text)]
    theirs = [t.lower() for w in words for t in TOKEN.findall(w[2])]
    if ours and ours == theirs:
        spans, p = [], 0
        for sent in sentences:
            need = len(TOKEN.findall(sent))
            if need == 0:
                prev = spans[-1][1] if spans else 0.0
                spans.append([prev, prev])
                continue
            begin, end, got = None, None, 0
            while got < need and p < len(words):
                w = words[p]
                begin = w[0] if begin is None else begin
                end = w[0] + w[1]
                got += len(TOKEN.findall(w[2]))
                p += 1
            spans.append([begin or 0.0, end or total])
        return sentences, spans, True
    spans, cursor = [], 0.0
    chars = max(1, sum(len(s) for s in sentences))
    for sent in sentences:
        dur = total * len(sent) / chars
        spans.append([cursor, cursor + dur])
        cursor += dur
    return sentences, spans, False


async def main(chapter_no: int, voice: str):
    ch_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    seg_file = ch_dir / "segments.json"
    if not seg_file.exists():
        sys.exit(f"Chưa có {seg_file} — nhập sách trước (import_wikisource.py).")
    data = json.loads(seg_file.read_text(encoding="utf-8"))
    segments = data["segments"]
    parts = ch_dir / "audio_parts"
    parts.mkdir(exist_ok=True)

    label = data.get("label") or ("Phần mở đầu" if chapter_no == 0 else f"Chương {chapter_no}")
    mp3_name = f"chuong{chapter_no:02d}.mp3"
    pcm, cursor = [], 0
    seg_rows, sent_rows = [], []
    fetched = unaligned = 0
    t0 = time.perf_counter()

    def spoken_text(i, seg):
        text = seg["text"]
        if i == 0 and seg["type"] == "h1" and not text.startswith(label):
            text = f"{label}. {text}"
        return text

    # Tải trước các đoạn còn thiếu, vài đoạn cùng lúc; vòng lặp bên dưới chỉ còn đọc từ đĩa.
    gate = asyncio.Semaphore(PARALLEL)

    async def prefetch(i, seg):
        nonlocal fetched
        part, meta = parts / f"{seg['id']}.mp3", parts / f"{seg['id']}.json"
        if part.exists() and meta.exists() and part.stat().st_size > 0:
            return
        async with gate:
            audio, words = await fetch(spoken_text(i, seg), voice)
            part.write_bytes(audio)
            meta.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            fetched += 1
            if fetched % 10 == 0:
                print(f"   … đã tải {fetched} đoạn, {time.perf_counter() - t0:.0f}s", flush=True)
            await asyncio.sleep(GAP)

    await asyncio.gather(*(prefetch(i, seg) for i, seg in enumerate(segments)))

    for i, seg in enumerate(segments):
        text = spoken_text(i, seg)
        part, meta = parts / f"{seg['id']}.mp3", parts / f"{seg['id']}.json"
        if part.exists() and meta.exists() and part.stat().st_size > 0:
            audio, words = part.read_bytes(), json.loads(meta.read_text(encoding="utf-8"))
        else:
            audio, words = await fetch(text, voice)
            part.write_bytes(audio)
            meta.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            fetched += 1
            await asyncio.sleep(GAP)

        x = decode_mp3(audio)
        lo, hi = trim_bounds(x)
        x = x[lo:hi]
        sentences, spans, ok = sentence_spans(text, words, len(x) / RATE + lo / RATE)
        unaligned += not ok
        seg_begin = cursor
        for k, (sent, (b, e)) in enumerate(zip(sentences, spans), start=1):
            # mốc của từ tính trên audio gốc; đổi sang timeline cuối: trừ phần đã cắt ở đầu
            sb = min(max(seg_begin, seg_begin + round((b - lo / RATE) * RATE)), seg_begin + len(x))
            se = min(max(sb, seg_begin + round((e - lo / RATE) * RATE)), seg_begin + len(x))
            if k == 1:
                sb = seg_begin
            if k == len(sentences):
                se = seg_begin + len(x)
            sent_rows.append([seg["id"], k, f"{sb / RATE:.3f}", f"{se / RATE:.3f}", sent])
        pcm.append(x)
        cursor += len(x)
        pause = np.zeros(int((HEAD_PAUSE if seg["type"] == "h1" else PARA_PAUSE) * RATE), dtype=np.float32)
        pcm.append(pause)
        cursor += len(pause)
        seg_rows.append([seg["id"], mp3_name, f"{seg_begin / RATE:.3f}", f"{cursor / RATE:.3f}"])
        if (i + 1) % 10 == 0:
            print(f"   … {i + 1}/{len(segments)} đoạn, {cursor / RATE / 60:.1f} phút audio, "
                  f"{time.perf_counter() - t0:.0f}s", flush=True)

    gen_s = time.perf_counter() - t0
    audio_s = cursor / RATE
    wav = np.clip(np.concatenate(pcm), -1.0, 1.0)
    enc = lameenc.Encoder()
    enc.set_bit_rate(BITRATE_KBPS)
    enc.set_in_sample_rate(RATE)
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

    print(f"✅ {mp3_name}: {audio_s / 60:.1f} phút, {len(seg_rows)} đoạn, {len(sent_rows)} câu "
          f"| {fetched} đoạn tải mới trong {gen_s:.0f}s (RTF {gen_s / audio_s:.3f}) | giọng {voice}"
          f" | {unaligned} đoạn phải chia mốc câu theo ký tự")
    print(f"   -> {ch_dir / mp3_name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    a = ap.parse_args()
    asyncio.run(main(a.chapter, a.voice))
