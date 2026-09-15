#!/usr/bin/env python3
"""Sinh mo0.smil: đồng bộ dtbook.xml với audio theo timestamps.csv.

Input  (trong build/chapter_NN/):
  - dtbook.xml       (từ Lộc / extract_chapter.py) — các thẻ có id_N
  - timestamps.csv   (từ Vy / tts_chapter.py)      — id,file_mp3,clipBegin,clipEnd
Output:
  - mo0.smil         — mỗi đoạn 1 <par id="sid_N"> chứa <text> + <audio>

Usage: python scripts/gen_smil.py 1
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def hms(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def gen_smil(chapter_no: int):
    ch_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    dtbook = ch_dir / "dtbook.xml"
    ts_csv = ch_dir / "timestamps.csv"
    for f in (dtbook, ts_csv):
        if not f.exists():
            sys.exit(f"Thiếu {f}")

    # id xuất hiện trong dtbook, theo đúng thứ tự văn bản, kèm loại thẻ (h1/sent)
    xml = dtbook.read_text(encoding="utf-8")
    id_tags = re.findall(r'<(h1|sent) id="(id_\d+)"', xml)
    dtbook_ids = [i for _, i in id_tags]
    tag_of = dict((i, t) for t, i in id_tags)

    # loại segment (p/h1/note) từ segments.json nếu có — để gắn class/customTest note
    type_of = {}
    seg_file = ch_dir / "segments.json"
    if seg_file.exists():
        for s in json.loads(seg_file.read_text(encoding="utf-8"))["segments"]:
            type_of[s["id"]] = s["type"]

    with open(ts_csv, encoding="utf-8") as f:
        clips = {r["id"]: r for r in csv.DictReader(f)}

    missing = [i for i in dtbook_ids if i not in clips]
    if missing:
        sys.exit(f"❌ {len(missing)} id trong dtbook không có timestamp: {missing[:5]}...")

    uid = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))["source"]
    total = max(float(c["clipEnd"]) for c in clips.values())

    pars = []
    for n, seg_id in enumerate(dtbook_ids, 1):
        c = clips[seg_id]
        sid = seg_id.replace("id_", "sid_")
        seg_type = type_of.get(seg_id) or ("h1" if tag_of[seg_id] == "h1" else "p")
        if seg_type == "h1":
            par_attrs = f'id="{sid}" class="h1"'
        elif seg_type == "note":
            # chú thích chia riêng: đánh dấu customTest để trình đọc cho phép skip
            par_attrs = f'id="{sid}" class="note" customTest="note"'
        else:
            par_attrs = f'id="{sid}" class="sent"'
        pars.append(f'''      <seq id="seq_{n}" class="p">
        <par {par_attrs}>
          <text src="dtbook.xml#{seg_id}"/>
          <audio src="{c['file_mp3']}" clipBegin="{float(c['clipBegin']):.3f}s" clipEnd="{float(c['clipEnd']):.3f}s"/>
        </par>
      </seq>''')

    smil = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">
<smil xmlns="http://www.w3.org/2001/SMIL20/">
  <head>
    <meta name="dtb:uid" content="{uid}-ch{chapter_no:02d}"/>
    <meta name="dtb:totalElapsedTime" content="{hms(0)}"/>
    <meta name="dtb:generator" content="totto-chan daisy scripts"/>
    <customAttributes>
      <customTest defaultState="false" id="pagenum" override="visible"/>
      <customTest defaultState="false" id="note" override="visible"/>
      <customTest defaultState="false" id="noteref" override="visible"/>
      <customTest defaultState="false" id="annotation" override="visible"/>
      <customTest defaultState="false" id="linenum" override="visible"/>
      <customTest defaultState="false" id="sidebar" override="visible"/>
      <customTest defaultState="false" id="prodnote" override="visible"/>
    </customAttributes>
  </head>
  <body>
    <seq id="root-seq">
{chr(10).join(pars)}
    </seq>
  </body>
</smil>
'''
    out = ch_dir / "mo0.smil"
    out.write_text(smil, encoding="utf-8")
    print(f"✅ mo0.smil: {len(dtbook_ids)} par, tổng audio {hms(total)}")
    print(f"   -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    gen_smil(ap.parse_args().chapter)
