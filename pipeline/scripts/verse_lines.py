#!/usr/bin/env python3
"""Lấy lại chỗ ngắt dòng của sách thơ.

import_wikisource.py nối các dòng thơ thành đoạn để giọng đọc đọc liền mạch, nên trang đọc hiện thơ
như văn xuôi. Script này tải lại các trang Wikisource của cuốn sách, rút từng dòng thơ theo đúng thứ tự
và ghi vào books/<slug>/metadata/verse_lines.json. build_site.py dùng file đó để đánh dấu chỗ xuống
dòng trong từng câu; văn bản, âm thanh và mốc thời gian không đổi.

Usage:
  python verse_lines.py truyen-kieu "Truyện Kiều"
  python verse_lines.py tho-han-mac-tu "Thơ Hàn Mặc Tử/Thơ Đường luật" "Thơ Hàn Mặc Tử/Gái quê"
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_wikisource import REPO, clean_inline, fetch_page, strip_templates, template_body  # noqa: E402


def page_lines(parsed: dict):
    if "<pages " in parsed["wikitext"]:          # trang ghép từ bản quét: chữ chỉ có trong HTML
        from ws_html import lines as html_lines
        return html_lines(parsed.get("text", ""))
    body = template_body(parsed["wikitext"], "văn")
    if body is None:
        body = parsed["wikitext"]
    body = re.sub(r"\{\{khác\|([^|{}]*)\|[^{}]*\}\}", r"\1", body)
    out = []
    for ln in clean_inline(strip_templates(body)).split("\n"):
        ln = unicodedata.normalize("NFC", re.sub(r"\s+", " ", re.sub(r"^[:*#]+\s*", "", ln.strip()))).strip()
        if re.search(r"\w", ln):
            out.append(ln)
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    slug, pages = sys.argv[1], sys.argv[2:]
    meta = REPO / "books" / slug / "metadata"
    if not meta.is_dir():
        sys.exit(f"❌ không có sách {slug}")
    lines = []
    for page in pages:
        got = page_lines(fetch_page(page))
        print(f"   {page}: {len(got)} dòng")
        lines += got
    (meta / "verse_lines.json").write_text(json.dumps({"pages": pages, "lines": lines}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"✅ {slug}: {len(lines)} dòng thơ")


if __name__ == "__main__":
    main()
