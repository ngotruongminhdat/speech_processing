#!/usr/bin/env python3
"""Extract một chương từ EPUB -> dtbook.xml + segments.json.

Đây là bước tạm thay cho phần của Lộc (nội dung DTBook XML), để pipeline
kỹ thuật chạy được end-to-end. Khi Lộc giao dtbook.xml thật thì bỏ qua
script này.

Quy ước id (chốt với cả nhóm):
  - Tiêu đề chương:  id_1  (thẻ <h1>)
  - Đoạn văn thứ n:  id_{n+1}  (thẻ <sent> trong <p>)
  - SMIL par tương ứng: sid_N (đổi tiền tố id_ -> sid_)

Usage:
  python scripts/extract_chapter.py --list          # xem danh sách chương
  python scripts/extract_chapter.py 1               # extract chương 1 (Nhà ga)
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

# Số mục front-matter trong toc.ncx đứng trước "Chương 1 - Nhà ga"
# (title page không lọt vào regex nên chỉ còn: lời UNICEF, lời tác giả, lời nói đầu)
FRONT_MATTER_ENTRIES = 3


class ChapterHTML(HTMLParser):
    """Lấy tiêu đề (h1) và các đoạn văn (p) từ 1 file HTML của EPUB."""

    def __init__(self):
        super().__init__()
        self.title_parts, self.paragraphs = [], []
        self._in_h1 = False
        self._cur = None  # đang gom text của 1 <p>

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


def toc_entries():
    with zipfile.ZipFile(EPUB) as z:
        toc = z.read("OEBPS/toc.ncx").decode("utf-8")
    return re.findall(
        r"<text>([^<]+)</text>\s*</navLabel>\s*<content src=\"([^\"]+)\"", toc
    )


def extract(chapter_no: int):
    """chapter_no >= 1: chương chính; chapter_no == 0: Phần mở đầu (3 mục front matter)."""
    entries = toc_entries()
    if chapter_no == 0:
        sections = entries[:FRONT_MATTER_ENTRIES]
        chapter_title = "Phần mở đầu"
    else:
        idx = chapter_no + FRONT_MATTER_ENTRIES - 1
        if idx >= len(entries):
            sys.exit(f"Chương {chapter_no} không tồn tại (sách có {len(entries) - FRONT_MATTER_ENTRIES} chương).")
        sections = [entries[idx]]
        chapter_title = None

    # segments: mỗi mục 1 thẻ h1 rồi đến các đoạn văn; id đánh liên tục
    segments, n = [], 0
    with zipfile.ZipFile(EPUB) as z:
        for title, src in sections:
            html = z.read("OEBPS/" + src.split("#")[0]).decode("utf-8")
            parser = ChapterHTML()
            parser.feed(html)
            sec_title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip() or title
            if chapter_title is None:
                chapter_title = sec_title
            n += 1
            segments.append({"id": f"id_{n}", "type": "h1", "text": sec_title})
            for p in parser.paragraphs:
                n += 1
                segments.append({"id": f"id_{n}", "type": "p", "text": p})

    out_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    write_dtbook(out_dir / "dtbook.xml", chapter_no, chapter_title, segments)
    (out_dir / "segments.json").write_text(
        json.dumps({"chapter": chapter_no, "title": chapter_title, "segments": segments},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    n_h1 = sum(1 for s in segments if s["type"] == "h1")
    print(f"✅ Chương {chapter_no} \"{chapter_title}\": {n_h1} mục, {len(segments) - n_h1} đoạn văn")
    print(f"   -> {out_dir / 'dtbook.xml'}")
    print(f"   -> {out_dir / 'segments.json'}")


def unit_label(chapter_no: int, chapter_title: str) -> str:
    return "Phần mở đầu" if chapter_no == 0 else f"Chương {chapter_no}: {chapter_title}"


def write_dtbook(path: Path, chapter_no: int, chapter_title: str, segments):
    uid = f"{META['source']}-ch{chapter_no:02d}"
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
        else:
            body.append(
                f'        <p><sent id="{seg["id"]}" smilref="mo0.smil#{sid}">{escape(seg["text"])}</sent></p>'
            )
    if open_level:
        body.append("      </level1>")
    xml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">
<dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-3" xml:lang="{META['language']}">
  <head>
    <meta name="dtb:uid" content="{uid}"/>
    <meta name="dc:Title" content="{escape(META['title'])} - {escape(unit_label(chapter_no, chapter_title))}"/>
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
    ap.add_argument("chapter", nargs="?", type=int, help="số chương (1-based)")
    ap.add_argument("--list", action="store_true", help="liệt kê các chương")
    args = ap.parse_args()

    if args.list or args.chapter is None:
        entries = toc_entries()
        for i, (t, _) in enumerate(entries[FRONT_MATTER_ENTRIES:], start=1):
            print(f"{i:3d}. {t}")
    else:
        extract(args.chapter)
