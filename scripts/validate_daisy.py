#!/usr/bin/env python3
"""Kiểm tra chéo bộ file DAISY của 1 chương trước khi đóng gói.

Check:
  1. XML well-formed (dtbook, smil, opf, ncx, res)
  2. Mọi <text src="dtbook.xml#id"> trong SMIL đều có id thật trong dtbook
  3. Mọi id trong dtbook đều được SMIL tham chiếu (không sót đoạn nào)
  4. Clip times: clipBegin < clipEnd, không chồng lấn, liên tục tăng dần
  5. Audio src trong SMIL/NCX tồn tại; mọi file trong manifest OPF tồn tại
  6. Tổng thời lượng audio khớp dtb:totalTime trong OPF (±2s)

Usage: python scripts/validate_daisy.py 1
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors, warns = [], []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def validate(chapter_no: int):
    ch = ROOT / "build" / f"chapter_{chapter_no:02d}"
    files = ["dtbook.xml", "mo0.smil", "book.opf", "navigation.ncx", "resources.res"]

    # 1. well-formed
    trees = {}
    for f in files:
        p = ch / f
        check(p.exists(), f"Thiếu file {f}")
        if p.exists():
            try:
                trees[f] = ET.parse(p)
            except ET.ParseError as e:
                errors.append(f"{f} không well-formed: {e}")
    if errors:
        return

    dtbook_ids = set(re.findall(r'\bid="(id_\d+)"', (ch / "dtbook.xml").read_text(encoding="utf-8")))

    # 2+3+4. SMIL refs & clip times
    smil = trees["mo0.smil"].getroot()
    ns = {"s": "http://www.w3.org/2001/SMIL20/"}
    pars = smil.findall(".//s:par", ns)
    referenced, prev_end, audio_srcs = set(), 0.0, set()
    for par in pars:
        text = par.find("s:text", ns)
        audio = par.find("s:audio", ns)
        check(text is not None and audio is not None, f"par {par.get('id')} thiếu text/audio")
        if text is None or audio is None:
            continue
        frag = text.get("src", "").split("#")[-1]
        referenced.add(frag)
        check(frag in dtbook_ids, f"SMIL trỏ tới id không tồn tại trong dtbook: {frag}")
        b = float(audio.get("clipBegin").rstrip("s"))
        e = float(audio.get("clipEnd").rstrip("s"))
        check(b < e, f"{frag}: clipBegin {b} >= clipEnd {e}")
        check(b >= prev_end - 0.001, f"{frag}: clip chồng lấn đoạn trước ({b} < {prev_end})")
        prev_end = e
        audio_srcs.add(audio.get("src"))

    unreferenced = dtbook_ids - referenced
    check(not unreferenced, f"{len(unreferenced)} id trong dtbook không được SMIL tham chiếu: {sorted(unreferenced)[:5]}")

    # 5. files tồn tại
    for src in audio_srcs:
        check((ch / src).exists(), f"Audio {src} không tồn tại")
    opf = trees["book.opf"].getroot()
    ons = {"o": "http://openebook.org/namespaces/oeb-package/1.0/"}
    hrefs = [i.get("href") for i in opf.findall(".//o:manifest/o:item", ons)]
    for href in hrefs:
        check((ch / href).exists(), f"Manifest khai {href} nhưng file không tồn tại")
    on_disk = {p.name for p in ch.iterdir() if p.is_file() and p.suffix in (".xml", ".smil", ".opf", ".ncx", ".res", ".mp3") and p.name != "timestamps.csv"}
    undeclared = on_disk - set(hrefs)
    if undeclared:
        warns.append(f"File có trên đĩa nhưng không có trong manifest: {sorted(undeclared)}")

    # NCX audio + content refs
    ncx = trees["navigation.ncx"].getroot()
    nns = {"n": "http://www.daisy.org/z3986/2005/ncx/"}
    for a in ncx.findall(".//n:audio", nns):
        check((ch / a.get("src")).exists(), f"NCX audio {a.get('src')} không tồn tại")
    for c in ncx.findall(".//n:content", nns):
        smil_file, _, frag = c.get("src").partition("#")
        check((ch / smil_file).exists(), f"NCX content trỏ {smil_file} không tồn tại")
        check(frag in {p.get("id") for p in pars}, f"NCX content #{frag} không có trong SMIL")

    # 6. totalTime
    total_meta = None
    for m in opf.findall(".//o:x-metadata/o:meta", ons):
        if m.get("name") == "dtb:totalTime":
            h, mi, s = m.get("content").split(":")
            total_meta = int(h) * 3600 + int(mi) * 60 + int(s)
    check(total_meta is not None, "OPF thiếu dtb:totalTime")
    if total_meta is not None:
        check(abs(prev_end - total_meta) <= 2, f"dtb:totalTime ({total_meta}s) lệch audio thực ({prev_end:.0f}s)")

    print(f"Kiểm tra chương {chapter_no}: {len(pars)} par, audio {prev_end / 60:.1f} phút")
    for w in warns:
        print(f"  ⚠️  {w}")
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    print("  ✅ PASS — sẵn sàng đóng gói")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    validate(ap.parse_args().chapter)
