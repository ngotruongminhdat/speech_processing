#!/usr/bin/env python3
"""Nhập một tác phẩm thuộc phạm vi công cộng từ Wikisource tiếng Việt.

Thay cho extract_chapter.py (vốn viết riêng cho EPUB Totto-chan): tạo thư mục
sách mới books/<slug>/ với metadata và, cho mỗi trang Wikisource, một đơn vị
build/chapter_NN/{segments.json, dtbook.xml} đúng định dạng mà các bước sau
(tts_chapter, gen_smil, gen_opf_ncx, validate_daisy) đang dùng.

Chỉ nhập trang có gắn nhãn phạm vi công cộng (PVCC); trang không có nhãn bị
từ chối trừ khi truyền --allow-untagged.

Usage:
  python import_wikisource.py --slug lao-hac --author "Nam Cao" --year 1943 \
      --subject "Văn học & Tiểu thuyết" "Lão Hạc"
  # tác phẩm nhiều chương: liệt kê từng trang con theo thứ tự
  python import_wikisource.py --slug tat-den --title "Tắt đèn" --author "Ngô Tất Tố" \
      --year 1937 "Tắt đèn/Chương 1" "Tắt đèn/Chương 2"
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
API = "https://vi.wikisource.org/w/api.php"
UA = "DAISY-student-project/0.1 (educational; vi.wikisource reader)"


def fetch_page(title: str) -> dict:
    qs = urllib.parse.urlencode({
        "action": "parse", "format": "json", "formatversion": 2,
        "page": title, "prop": "wikitext|categories", "redirects": 1,
    })
    req = urllib.request.Request(f"{API}?{qs}", headers={"User-Agent": UA})
    # Tải thong thả: nghỉ giữa các yêu cầu, và nếu bị giới hạn tần suất (429) thì chờ rồi thử lại.
    for attempt in range(6):
        time.sleep(1.5)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1)
            print(f"   … Wikisource yêu cầu chậm lại, chờ {wait}s", flush=True)
            time.sleep(wait)
    if "error" in data:
        sys.exit(f"❌ Wikisource: {title!r}: {data['error'].get('info')}")
    return data["parse"]


def template_body(wikitext: str, name: str):
    """Nội dung tham số đầu của {{name|...}}, đếm ngoặc để chịu được template lồng."""
    m = re.search(r"\{\{\s*" + re.escape(name) + r"\s*\|", wikitext)
    if not m:
        return None
    depth, i = 2, m.end()
    while i < len(wikitext) and depth > 0:
        if wikitext.startswith("{{", i):
            depth += 2
            i += 2
        elif wikitext.startswith("}}", i):
            depth -= 2
            i += 2
        else:
            i += 1
    return wikitext[m.end(): i - 2]


# Template chỉ để trình bày nhưng CÓ mang chữ của tác phẩm, ví dụ {{drop cap|B}}ắt đầu.
TEXT_TEMPLATES = r"drop cap|dropcap|dc|drop initial|sc|smallcaps|larger|x-larger|smaller|giữa|center|rộng|u"


def strip_templates(text: str) -> str:
    """Giữ chữ trong các template trình bày, rồi bỏ mọi {{...}} còn lại
    (đầu đề, nhãn bản quyền, chú thích nguồn)."""
    text = re.sub(r"\{\{\s*(?:" + TEXT_TEMPLATES + r")\s*\|([^{}|]*)\}\}", r"\1", text, flags=re.I)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    return text


def clean_inline(text: str) -> str:
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?(poem|center|small|big|div|span|section)[^>]*>", "", text)
    text = re.sub(r"\[\[\s*(?:Thể loại|Category|Tập tin|File|Hình)\s*:[^\]]*\]\]", "", text)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)   # [[đích|nhãn]] -> nhãn
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)            # [[đích]] -> đích
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)                           # nghiêng/đậm
    return text


def to_paragraphs(wikitext: str):
    """-> [(type, text)] với type là 'h1' (đề mục trong trang) hoặc 'p'."""
    body = template_body(wikitext, "văn")
    if body is None:
        body = wikitext
    body = clean_inline(strip_templates(body))
    out = []
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        h = re.fullmatch(r"=+\s*(.+?)\s*=+", block)
        if h:
            out.append(("h1", h.group(1)))
            continue
        # thơ/đoạn có xuống dòng đơn: bỏ dấu ':' thụt đầu dòng, nối bằng dấu cách
        lines = [re.sub(r"^[:*#]+\s*", "", ln).strip() for ln in block.split("\n")]
        text = re.sub(r"\s+", " ", " ".join(ln for ln in lines if ln)).strip()
        text = unicodedata.normalize("NFC", text)
        if re.search(r"\w", text):
            out.append(("p", text))
    return out


def roman(text: str) -> int:
    """Giá trị của số La Mã, hoặc 0 nếu không phải số La Mã."""
    if not re.fullmatch(r"M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})", text) or not text:
        return 0
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for ch, nxt in zip(text, text[1:] + " "):
        total += -vals[ch] if nxt in vals and vals[nxt] > vals[ch] else vals[ch]
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="+", help="tên trang Wikisource, mỗi trang là một đơn vị")
    ap.add_argument("--slug", required=True, help="tên thư mục sách, ví dụ lao-hac")
    ap.add_argument("--title", help="tên sách (mặc định: tên trang đầu tiên)")
    ap.add_argument("--author", required=True)
    ap.add_argument("--year", default="")
    ap.add_argument("--subject", default="Văn học & Tiểu thuyết")
    ap.add_argument("--description", default="")
    ap.add_argument("--allow-untagged", action="store_true", help="nhập cả trang không có nhãn PVCC")
    a = ap.parse_args()

    # Tải và kiểm tra nhãn bản quyền của mọi trang trước khi ghi bất cứ thứ gì ra đĩa.
    parsed_pages, root_ok = [], {}

    def tagged(parsed) -> bool:
        return any(c["category"].startswith("PVCC") for c in parsed.get("categories", []))

    for page in a.pages:
        parsed = fetch_page(page)
        ok = tagged(parsed)
        if not ok and "/" in page:
            # Trang con (từng chương) thường không gắn nhãn riêng: nhãn nằm ở trang gốc của tác phẩm.
            root = page.split("/", 1)[0]
            if root not in root_ok:
                root_ok[root] = tagged(fetch_page(root))
            ok = root_ok[root]
        if not ok and not a.allow_untagged:
            cats = [c["category"] for c in parsed.get("categories", [])]
            sys.exit(f"❌ {page!r} không có nhãn phạm vi công cộng (PVCC). Thể loại: {cats}")
        parsed_pages.append(parsed)

    book_root = REPO / "books" / a.slug
    title = a.title or a.pages[0]
    meta = {
        "title": title,
        "creator": a.author,
        "subject": a.subject,
        "description": a.description,
        "publisher": "Wikisource tiếng Việt",
        "date": a.year,
        # Tác phẩm Wikisource không có ISBN: dùng định danh ổn định theo slug.
        "source": f"vi-wikisource-{a.slug}",
        "language": "vi",
        "note": "Văn bản thuộc phạm vi công cộng tại Việt Nam, lấy từ Wikisource.",
        "collector": "",
        "sourceURL": "https://vi.wikisource.org/wiki/" + urllib.parse.quote(a.pages[0].replace(" ", "_")),
        "narrator": "Hoài My (Microsoft Neural TTS)",
        "book_slug": a.slug,
        "submission_folder": a.slug,
    }
    (book_root / "metadata").mkdir(parents=True, exist_ok=True)
    (book_root / "metadata" / "book_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # extract_chapter đọc metadata lúc import, nên chỉ import sau khi đã ghi file.
    os.environ["DAISY_BOOK_ROOT"] = str(book_root)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from extract_chapter import write_dtbook

    single = len(a.pages) == 1
    for unit_no, (page, parsed) in enumerate(zip(a.pages, parsed_pages), start=1):
        paras = to_paragraphs(parsed["wikitext"])
        tail = page.split("/")[-1]
        if single:
            unit_title = label = title
        elif roman(tail):
            # Số La Mã mà để nguyên thì TTS đọc thành chữ cái; đổi sang số thường.
            unit_title, label = f"Chương {roman(tail)}", title
        else:
            unit_title, label = tail, f"Chương {unit_no}"

        segments = [{"id": "id_1", "type": "h1", "text": unit_title}]
        for kind, text in paras:
            segments.append({"id": f"id_{len(segments) + 1}", "type": kind, "text": text})

        out_dir = book_root / "build" / f"chapter_{unit_no:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        write_dtbook(out_dir / "dtbook.xml", unit_no, label, unit_title, segments)
        (out_dir / "segments.json").write_text(
            json.dumps({"chapter": unit_no, "label": label, "title": unit_title,
                        "segments": segments}, ensure_ascii=False, indent=2), encoding="utf-8")
        chars = sum(len(s["text"]) for s in segments)
        print(f"✅ [{unit_no}] {page}: {len(segments)} đoạn, {chars} ký tự -> {out_dir}")

    print(f"📚 Sách: {book_root}")


if __name__ == "__main__":
    main()
