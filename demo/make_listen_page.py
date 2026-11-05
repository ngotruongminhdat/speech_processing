#!/usr/bin/env python3
"""Tạo trang nghe thử: cùng một đoạn văn, mỗi hệ TTS một nút phát.

Gom audio của từng hệ (thư mục chứa <id>.wav hoặc <id>.mp3) vào
demo/outputs/nghe_thu/ và ghi index.html, mở thẳng bằng trình duyệt.

Usage: .venv/bin/python demo/make_listen_page.py --ids id_2 id_7 id_9 \
         --system "Hoài My (edge-tts)=books/lao-hac/build/chapter_01/audio_parts" \
         --system "Piper vais1000=demo/outputs/piper/vi_VN-vais1000-medium"
"""
import argparse
import html
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def wav_to_mp3(path: Path, kbps: int = 96) -> bytes:
    """Nén wav thành mp3 để trang nhẹ, đưa lên web được."""
    import lameenc
    import numpy as np
    import soundfile as sf
    x, rate = sf.read(str(path), dtype="float32", always_2d=True)
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps)
    enc.set_in_sample_rate(rate)
    enc.set_channels(1)
    enc.set_quality(2)
    pcm = (np.clip(x.mean(axis=1), -1, 1) * 32767).astype(np.int16)
    return bytes(enc.encode(pcm.tobytes()) + enc.flush())

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="lao-hac")
    ap.add_argument("--ids", nargs="+", required=True)
    ap.add_argument("--system", action="append", required=True, help="tên=thư_mục_audio")
    ap.add_argument("--note", action="append", default=[], help="tên=ghi chú hiện dưới tên hệ")
    a = ap.parse_args()

    systems = [s.split("=", 1) for s in a.system]
    notes = dict(n.split("=", 1) for n in a.note)
    segs = {s["id"]: s for s in json.loads(
        (REPO / "books" / a.slug / "build" / "chapter_01" / "segments.json").read_text(encoding="utf-8"))["segments"]}
    out = REPO / "demo" / "outputs" / "nghe_thu"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    blocks = []
    for sid in a.ids:
        rows = []
        for k, (name, d) in enumerate(systems):
            src = next((REPO / d / f"{sid}{e}" for e in (".wav", ".mp3") if (REPO / d / f"{sid}{e}").exists()), None)
            if src is None:
                rows.append(f"<tr><th scope=row>{html.escape(name)}</th><td>chưa có audio</td></tr>")
                continue
            dst = out / f"s{k}" / f"{sid}.mp3"
            dst.parent.mkdir(exist_ok=True)
            if src.suffix == ".mp3":
                shutil.copyfile(src, dst)
            else:
                dst.write_bytes(wav_to_mp3(src))
            note = f"<small>{html.escape(notes[name])}</small>" if name in notes else ""
            rows.append(f"<tr><th scope=row>{html.escape(name)}{note}</th>"
                        f"<td><audio controls preload=none src='s{k}/{sid}.mp3' "
                        f"aria-label='{html.escape(name)}'></audio></td></tr>")
        blocks.append(f"<section><h2>Đoạn {sid.split('_')[1]}</h2><blockquote>{html.escape(segs[sid]['text'])}"
                      f"</blockquote><table>{''.join(rows)}</table></section>")

    (out / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nghe thử giọng đọc</title>
<style>
body{{font:17px/1.6 Georgia,serif;max-width:860px;margin:2rem auto;padding:0 1rem;background:#f6efe2;color:#2b1d14}}
h1{{font-size:1.6rem}} h2{{font-size:1.1rem;margin:2.2rem 0 .4rem;color:#7a3b1d}}
blockquote{{margin:0 0 .8rem;padding:.7rem 1rem;background:#fffaf0;border-left:4px solid #b9773f;border-radius:6px}}
table{{border-collapse:collapse;width:100%}} th{{text-align:left;font-weight:600;padding:.3rem .8rem .3rem 0;width:15rem;vertical-align:middle}}
th small{{display:block;font-weight:400;color:#6b5a4c;font-size:.8rem}} audio{{width:100%;height:36px}}
@media(max-width:640px){{tr,th,td{{display:block;width:auto}} th{{padding:.7rem 0 .15rem}}}}
</style></head><body>
<h1>Nghe thử giọng đọc trên truyện “Lão Hạc”</h1>
<p>Mỗi đoạn văn được đọc bởi từng hệ TTS. Hãy nghe ngữ điệu, chỗ ngắt nghỉ và câu thoại.</p>
{''.join(blocks)}
</body></html>""", encoding="utf-8")
    print("→", (out / "index.html"))
