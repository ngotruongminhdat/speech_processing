#!/usr/bin/env python3
"""Sinh book.opf + navigation.ncx + resources.res cho 1 chương.

- book.opf       : metadata 9 trường (Dublin Core, theo đăng ký của nhóm)
                   + manifest liệt kê đủ mọi file + spine
- navigation.ncx : mục lục điều hướng (navPoint trỏ vào mo0.smil)
- resources.res  : file tài nguyên chuẩn DAISY (template cố định)

Usage: python scripts/gen_opf_ncx.py 1
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))


def hms(seconds: float) -> str:
    h, rem = divmod(int(round(seconds)), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def gen(chapter_no: int):
    ch_dir = ROOT / "build" / f"chapter_{chapter_no:02d}"
    seg = json.loads((ch_dir / "segments.json").read_text(encoding="utf-8"))
    chapter_title = seg["title"]
    uid = f"{META['source']}-ch{chapter_no:02d}"
    mp3_name = f"chuong{chapter_no:02d}.mp3"

    with open(ch_dir / "timestamps.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("timestamps.csv rỗng")
    total_time = max(float(r["clipEnd"]) for r in rows)
    clips = {r["id"]: r for r in rows}

    # mỗi mục h1 trong chương = 1 navPoint (chương thường có 1, Phần mở đầu có 3)
    headings = [s for s in seg["segments"] if s["type"] == "h1"]
    base_label = seg.get("label") or ("Phần mở đầu" if chapter_no == 0 else f"Chương {chapter_no}")
    unit_label = base_label if base_label == chapter_title else f"{base_label}: {chapter_title}"

    # ---------- book.opf ----------
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/" unique-identifier="uid">
  <metadata>
    <dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
      <dc:Format>ANSI/NISO Z39.86-2005</dc:Format>
      <dc:Title>{escape(META["title"])} - {escape(unit_label)}</dc:Title>
      <dc:Creator>{escape(META["creator"])}</dc:Creator>
      <dc:Subject>{escape(META["subject"])}</dc:Subject>
      <dc:Description>{escape(META["description"])}</dc:Description>
      <dc:Publisher>{escape(META["publisher"])}</dc:Publisher>
      <dc:Date>{escape(META["date"])}</dc:Date>
      <dc:Source>{escape(META["source"])}</dc:Source>
      <dc:Language>{escape(META["language"])}</dc:Language>
      <dc:Identifier id="uid">{uid}</dc:Identifier>
    </dc-metadata>
    <x-metadata>
      <meta name="dtb:multimediaType" content="audioFullText"/>
      <meta name="dtb:multimediaContent" content="audio,text"/>
      <meta name="dtb:totalTime" content="{hms(total_time)}"/>
      <meta name="dtb:audioFormat" content="MP3"/>
      <meta name="note" content={quoteattr(META["note"] or "")}/>
      <meta name="collector" content={quoteattr(META["collector"])}/>
      <meta name="sourceURL" content={quoteattr(META["sourceURL"])}/>
    </x-metadata>
  </metadata>
  <manifest>
    <item href="book.opf" id="opf" media-type="text/xml"/>
    <item href="dtbook.xml" id="dtbook" media-type="application/x-dtbook+xml"/>
    <item href="mo0.smil" id="mo0" media-type="application/smil"/>
    <item href="{mp3_name}" id="audio1" media-type="audio/mpeg"/>
    <item href="navigation.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>
    <item href="resources.res" id="resource" media-type="application/x-dtbresource+xml"/>
  </manifest>
  <spine>
    <itemref idref="mo0"/>
  </spine>
</package>
'''
    (ch_dir / "book.opf").write_text(opf, encoding="utf-8")

    # ---------- navigation.ncx ----------
    nav_parts = []
    for order, h in enumerate(headings, start=1):
        c = clips[h["id"]]
        sid = h["id"].replace("id_", "sid_")
        label = f"{base_label}: {escape(h['text'])}" if len(headings) == 1 and base_label != h["text"] else escape(h["text"])
        nav_parts.append(f'''    <navPoint id="nav_{order}" playOrder="{order}" class="h1">
      <navLabel>
        <text>{label}</text>
        <audio src="{mp3_name}" clipBegin="{float(c["clipBegin"]):.3f}s" clipEnd="{float(c["clipEnd"]):.3f}s"/>
      </navLabel>
      <content src="mo0.smil#{sid}"/>
    </navPoint>''')
    nav_points = "\n".join(nav_parts)

    ncx = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="{META["language"]}">
  <head>
    <meta name="dtb:uid" content="{uid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
    <meta name="dtb:generator" content="totto-chan daisy scripts"/>
    <smilCustomTest defaultState="false" id="pagenum" override="visible" bookStruct="PAGE_NUMBER"/>
    <smilCustomTest defaultState="false" id="note" override="visible" bookStruct="NOTE"/>
    <smilCustomTest defaultState="false" id="noteref" override="visible" bookStruct="NOTE_REFERENCE"/>
    <smilCustomTest defaultState="false" id="annotation" override="visible" bookStruct="ANNOTATION"/>
    <smilCustomTest defaultState="false" id="linenum" override="visible" bookStruct="LINE_NUMBER"/>
    <smilCustomTest defaultState="false" id="sidebar" override="visible" bookStruct="OPTIONAL_SIDEBAR"/>
    <smilCustomTest defaultState="false" id="prodnote" override="visible" bookStruct="OPTIONAL_PRODUCER_NOTE"/>
  </head>
  <docTitle>
    <text>{escape(META["title"])}</text>
  </docTitle>
  <docAuthor>
    <text>{escape(META["creator"])}</text>
  </docAuthor>
  <navMap>
{nav_points}
  </navMap>
</ncx>
'''
    (ch_dir / "navigation.ncx").write_text(ncx, encoding="utf-8")

    # ---------- resources.res ----------
    res = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE resources PUBLIC "-//NISO//DTD resource 2005-1//EN" "http://www.daisy.org/z3986/2005/resource-2005-1.dtd">
<resources xmlns="http://www.daisy.org/z3986/2005/resource/" version="2005-1">
  <scope nsuri="http://www.daisy.org/z3986/2005/ncx/">
    <nodeSet id="ns001" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']">
      <resource xml:lang="vi"><text>Trang</text></resource>
    </nodeSet>
    <nodeSet id="ns002" select="//smilCustomTest[@bookStruct='NOTE']">
      <resource xml:lang="vi"><text>Ghi chú</text></resource>
    </nodeSet>
    <nodeSet id="ns003" select="//smilCustomTest[@bookStruct='NOTE_REFERENCE']">
      <resource xml:lang="vi"><text>Tham chiếu ghi chú</text></resource>
    </nodeSet>
    <nodeSet id="ns004" select="//smilCustomTest[@bookStruct='ANNOTATION']">
      <resource xml:lang="vi"><text>Chú thích</text></resource>
    </nodeSet>
    <nodeSet id="ns005" select="//smilCustomTest[@bookStruct='LINE_NUMBER']">
      <resource xml:lang="vi"><text>Dòng</text></resource>
    </nodeSet>
    <nodeSet id="ns006" select="//smilCustomTest[@bookStruct='OPTIONAL_SIDEBAR']">
      <resource xml:lang="vi"><text>Ghi chú bên lề</text></resource>
    </nodeSet>
    <nodeSet id="ns007" select="//smilCustomTest[@bookStruct='OPTIONAL_PRODUCER_NOTE']">
      <resource xml:lang="vi"><text>Ghi chú nhà sản xuất</text></resource>
    </nodeSet>
  </scope>
</resources>
'''
    (ch_dir / "resources.res").write_text(res, encoding="utf-8")

    print(f"✅ book.opf (totalTime {hms(total_time)}), navigation.ncx, resources.res")
    print(f"   -> {ch_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    gen(ap.parse_args().chapter)
