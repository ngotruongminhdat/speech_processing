#!/usr/bin/env python3
"""Extract một đơn vị (chương/phần) từ EPUB -> dtbook.xml + segments.json.

Đây là bước tạm thay cho phần của Lộc (nội dung DTBook XML), để pipeline
kỹ thuật chạy được end-to-end. Khi Lộc giao dtbook.xml thật thì bỏ qua
script này.

LƯU Ý: mục lục NCX của EPUB bị thiếu (chỉ 47 chương đầu), nên script
liệt kê nội dung theo SPINE (thứ tự file split_002..076):
  - Đơn vị 0        = Phần mở đầu (Lời UNICEF + Lời tác giả + Lời nói đầu)
  - Đơn vị 1..61    = 61 chương truyện (split_005..065)
  - Đơn vị 62       = Phần kết (Lời kết + 10 hồ sơ bạn học, split_066..076)

Footnote (GV yêu cầu "chia riêng"): dấu [n] trong bài -> thẻ <noteref>,
nội dung chú thích (nằm cuối sách sau chữ HẾT) -> khối <note> riêng có
audio clip riêng, đặt cuối chương chứa noteref.

Quy ước id: tuần tự id_1, id_2... trong mỗi đơn vị; SMIL par = sid_N.

Usage:
  python scripts/extract_chapter.py --list     # xem danh sách đơn vị
  python scripts/extract_chapter.py 1          # extract chương 1 (Nhà ga)
"""
import argparse
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
EPUB = ROOT / "sources" / "Totto-chan - Co be ben cua so - Tetsuko Kuroyanagi.epub"
META = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))

FRONT_SPLITS = [2, 3, 4]          # Lời UNICEF, Lời tác giả, Lời nói đầu
CHAPTER_SPLITS = list(range(5, 66))   # 61 chương truyện
BACK_SPLITS = list(range(66, 77))     # Lời kết + hồ sơ bạn học
NOTE_RE = re.compile(r"\s*\[(\d+)\]\s*")

# giữ tương thích import cũ
FRONT_MATTER_ENTRIES = len(FRONT_SPLITS)


def split_path(n: int) -> str:
    return f"OEBPS/Text/Totto-chan_c-uko_Kuroyanagi_split_{n:03d}.html"


class ChapterHTML(HTMLParser):
    """Lấy tiêu đề (h1) và các đoạn văn (p) từ 1 file HTML của EPUB."""

    def __init__(self):
        super().__init__()
        self.title_parts, self.paragraphs = [], []
        self._in_h1 = False
        self._cur = None

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self._in_h1 = True
        elif tag == "p":
            self._cur = []

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False
        elif tag == "p" and self._cur is not None:
            text = re.sub(r"\s+", " ", "".join(self._cur)).strip()
            if text:
                self.paragraphs.append(text)
            self._cur = None

    def handle_data(self, data):
        if self._in_h1:
            self.title_parts.append(data)
        elif self._cur is not None:
            self._cur.append(data)


def read_split(z: zipfile.ZipFile, n: int):
    """-> (title từ h1, [paragraphs])"""
    parser = ChapterHTML()
    parser.feed(z.read(split_path(n)).decode("utf-8"))
    title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    return title, parser.paragraphs


def collect_endnotes(z: zipfile.ZipFile) -> dict:
    """Chú thích cuối sách: các đoạn dạng '[n] nội dung' ở cuối split cuối."""
    notes = {}
    _, paras = read_split(z, BACK_SPLITS[-1])
    for p in paras:
        m = re.match(r"^\[(\d+)\]\s*(.+)$", p)
        if m:
            notes[int(m.group(1))] = m.group(2).strip()
    # trường hợp chú thích bị dính vào cuối đoạn văn cuối (sau chữ HẾT)
    for p in paras:
        for m in re.finditer(r"HẾT\s*\[(\d+)\]\s*(.+)$", p):
            notes[int(m.group(1))] = m.group(2).strip()
    return notes


def book_units():
    """[(unit_no, label, folder_label, [split_nos])] — không đọc file."""
    units = [(0, "Phần mở đầu", "Mở đầu", FRONT_SPLITS)]
    for i, n in enumerate(CHAPTER_SPLITS, start=1):
        units.append((i, f"Chương {i}", f"Chương {i}", [n]))
    units.append((len(CHAPTER_SPLITS) + 1, "Phần kết", "Phần kết", BACK_SPLITS))
    return units


def unit_titles():
    """[(unit_no, label, title)] — đọc h1 từ EPUB (cho --list và preview)."""
    out = []
    with zipfile.ZipFile(EPUB) as z:
        for no, label, _folder, splits in book_units():
            if len(splits) == 1:
                title, _ = read_split(z, splits[0])
            else:
                title = label
            out.append((no, label, title or label))
    return out


def strip_note_content(paragraphs, notes):
    """Bỏ các đoạn/đuôi đoạn là nội dung chú thích cuối sách."""
    cleaned = []
    for p in paragraphs:
        if re.match(r"^\[(\d+)\]", p):
            continue  # đoạn thuần chú thích
        m = re.search(r"(HẾT)\s*\[\d+\].*$", p)
        if m:
            p = p[: m.end(1)]
        cleaned.append(p)
    return cleaned


def extract(unit_no: int):
    units = {no: (label, folder, splits) for no, label, folder, splits in book_units()}
    if unit_no not in units:
        sys.exit(f"Đơn vị {unit_no} không tồn tại (0..{max(units)}).")
    label, _folder, splits = units[unit_no]

    with zipfile.ZipFile(EPUB) as z:
        notes = collect_endnotes(z)
        segments, n, unit_title, used_notes = [], 0, None, []
        for sn in splits:
            title, paras = read_split(z, sn)
            if sn == BACK_SPLITS[-1] or unit_no == max(units):
                paras = strip_note_content(paras, notes)
            if unit_title is None:
                unit_title = title or label
            n += 1
            segments.append({"id": f"id_{n}", "type": "h1", "text": title or label})
            for p in paras:
                n += 1
                noterefs = []
                # tách dấu [k] trong đoạn -> noteref, text sạch cho TTS
                def _sub(m):
                    k = int(m.group(1))
                    if k in notes:
                        noterefs.append({"n": k, "pos": m.start()})
                        return " "
                    return m.group(0)
                clean = NOTE_RE.sub(_sub, p)
                clean = re.sub(r"\s+", " ", clean).strip()
                # pos tính lại trên text sạch: đặt tại vị trí match cũ đã thay bằng 1 space
                seg = {"id": f"id_{n}", "type": "p", "text": clean}
                if noterefs:
                    seg["noterefs"] = [d["n"] for d in noterefs]
                    used_notes += [d["n"] for d in noterefs]
                segments.append(seg)
        # khối chú thích riêng ở cuối đơn vị (GV: footnote chia riêng)
        for k in sorted(set(used_notes)):
            n += 1
            segments.append({
                "id": f"id_{n}", "type": "note", "note_no": k,
                "text": f"Chú thích {k}. {notes[k]}",
            })

    out_dir = ROOT / "build" / f"chapter_{unit_no:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_dtbook(out_dir / "dtbook.xml", unit_no, label, unit_title, segments)
    (out_dir / "segments.json").write_text(
        json.dumps({"chapter": unit_no, "label": label, "title": unit_title,
                    "segments": segments}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    n_h1 = sum(1 for s in segments if s["type"] == "h1")
    n_note = sum(1 for s in segments if s["type"] == "note")
    note_info = f", {n_note} chú thích" if n_note else ""
    print(f"✅ [{label}] \"{unit_title}\": {n_h1} mục, "
          f"{len(segments) - n_h1 - n_note} đoạn văn{note_info}")
    print(f"   -> {out_dir / 'dtbook.xml'}")
    print(f"   -> {out_dir / 'segments.json'}")


def write_dtbook(path: Path, unit_no: int, label: str, unit_title: str, segments):
    uid = f"{META['source']}-ch{unit_no:02d}"
    body, open_level = [], False
    for seg in segments:
        sid = seg["id"].replace("id_", "sid_")
        if seg["type"] == "h1":
            if open_level:
                body.append("      </level1>")
            body.append("      <level1>")
            open_level = True
            body.append(
                f'        <h1 id="{seg["id"]}" smilref="mo0.smil#{sid}">{escape(seg["text"])}</h1>'
            )
        elif seg["type"] == "note":
            body.append(
                f'        <note id="note_{seg["note_no"]}" class="footnote">'
                f'<p><sent id="{seg["id"]}" smilref="mo0.smil#{sid}">{escape(seg["text"])}</sent></p></note>'
            )
        else:
            inner = escape(seg["text"])
            for k in seg.get("noterefs", []):
                inner += (f' <noteref idref="#note_{k}" class="noteref"'
                          f' id="{seg["id"]}_ref{k}">{k}</noteref>')
            body.append(
                f'        <p><sent id="{seg["id"]}" smilref="mo0.smil#{sid}">{inner}</sent></p>'
            )
    if open_level:
        body.append("      </level1>")
    xml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">
<dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-3" xml:lang="{META['language']}">
  <head>
    <meta name="dtb:uid" content="{uid}"/>
    <meta name="dc:Title" content="{escape(META['title'])} - {escape(label)}: {escape(unit_title)}"/>
  </head>
  <book>
    <frontmatter>
      <doctitle>{escape(META['title'])}</doctitle>
      <docauthor>{escape(META['creator'])}</docauthor>
    </frontmatter>
    <bodymatter>
{chr(10).join(body)}
    </bodymatter>
  </book>
</dtbook>
'''
    path.write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", nargs="?", type=int, help="số đơn vị (0..62)")
    ap.add_argument("--list", action="store_true", help="liệt kê các đơn vị")
    args = ap.parse_args()

    if args.list or args.chapter is None:
        for no, label, title in unit_titles():
            extra = f" — {title}" if title != label else ""
            print(f"{no:3d}. {label}{extra}")
    else:
        extract(args.chapter)
