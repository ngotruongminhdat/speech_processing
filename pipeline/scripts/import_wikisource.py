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
import hashlib
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
    # Bộ đệm trên đĩa (biến môi trường WS_CACHE): trang đã tải thì không hỏi lại Wikisource.
    cache = os.environ.get("WS_CACHE")
    if cache:
        f = Path(cache) / (hashlib.md5(title.encode("utf-8")).hexdigest()[:12] + ".json")
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            return {"wikitext": d["wikitext"], "text": d.get("html", ""),
                    "categories": [{"category": c} for c in d["categories"]]}
    qs = urllib.parse.urlencode({
        "action": "parse", "format": "json", "formatversion": 2,
        "page": title, "prop": "wikitext|text|categories", "redirects": 1,
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


def verse_units(wikitext: str, per_unit: int, per_para: int = 4):
    """Truyện thơ dài nằm trong một thẻ <poem>: chia thành các phần per_unit câu, mỗi đoạn
    per_para câu. Không thêm bớt chữ nào; số câu ở lề ({{số|n}}) bị bỏ.
    -> [(tên phần, [(type, text)])]"""
    # Trang song ngữ (Chinh phụ ngâm: cột chữ Nôm, cột quốc ngữ) có nhiều thẻ <poem>: lấy thẻ ít chữ Hán Nôm nhất.
    poems = re.findall(r"<poem>(.*?)</poem>", wikitext, flags=re.S)
    body = min(poems, key=lambda t: len(re.findall(r"[\u2e80-\u9fff\U00020000-\U0010ffff]", t)) / max(1, len(t)))
    # {{khác|chữ trong bản này|dị bản}}: giữ chữ của bản đang nhập
    body = re.sub(r"\{\{khác\|([^|{}]*)\|[^{}]*\}\}", r"\1", body)
    lines = [unicodedata.normalize("NFC", re.sub(r"\s+", " ", clean_inline(strip_templates(ln))).strip())
             for ln in body.split("\n")]
    lines = [ln for ln in lines if ln]
    units = []
    for a in range(0, len(lines), per_unit):
        chunk = lines[a: a + per_unit]
        # phần cuối quá ngắn thì nhập vào phần trước
        if units and len(chunk) < per_unit // 2:
            first = units[-1][2]
            chunk = lines[first:]
            units.pop()
            a = first
        paras = [("p", " ".join(chunk[i: i + per_para])) for i in range(0, len(chunk), per_para)]
        units.append((f"Từ câu {a + 1} đến câu {a + len(chunk)}", paras, a))
    return [(name, paras) for name, paras, _ in units]


def header_part(wikitext: str) -> str:
    """Tên phần ghi ở tham số 'phần' của {{đầu đề}}, đã bỏ cú pháp liên kết."""
    m = re.search(r"\|\s*phần\s*=\s*(.*)", wikitext)
    return unicodedata.normalize("NFC", clean_inline(m.group(1)).strip()) if m else ""


def page_paragraphs(parsed: dict):
    """Đoạn văn của một trang. Trang ghép từ bản quét (<pages index=.../>) không có chữ trong
    wikitext nên lấy từ HTML đã dựng; bỏ đề mục 'Chú thích' cuối trang và mọi thứ sau nó."""
    if "<pages " not in parsed["wikitext"]:
        return to_paragraphs(parsed["wikitext"])
    from ws_html import paragraphs
    out = []
    for kind, text in paragraphs(parsed.get("text", "")):
        if kind == "h1" and text.lower().startswith("chú thích"):
            break
        out.append((kind, text))
    return out


def same_title(a: str, b: str) -> bool:
    key = lambda t: re.sub(r"[\W_]+", "", t).casefold()
    return key(a) == key(b)


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
    ap.add_argument("--verse", type=int, metavar="N",
                    help="truyện thơ một trang: chia thành các phần N câu (ví dụ 250)")
    ap.add_argument("--header-titles", action="store_true",
                    help="tên đơn vị lấy từ tham số 'phần' ở đầu đề của trang")
    ap.add_argument("--poem-titles", action="store_true",
                    help="tập thơ: dòng in hoa ngắn là tên bài thơ, giữ lại làm đề mục")
    ap.add_argument("--titles", type=Path, help="file văn bản, mỗi dòng là tên một đơn vị (ghi đè tên lấy từ trang)")
    ap.add_argument("--unit-word", default="Chương", help="cách gọi một đơn vị: Chương, Phần, Truyện, Bài")
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

    single = len(a.pages) == 1 and not a.verse
    if a.verse:
        todo = [(a.pages[0] + "/" + name, paras) for name, paras in verse_units(parsed_pages[0]["wikitext"], a.verse)]
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        todo = []
        names = a.titles.read_text(encoding="utf-8").strip().split("\n") if a.titles else None
        if names and len(names) != len(a.pages):
            sys.exit(f"❌ --titles có {len(names)} dòng nhưng có {len(a.pages)} trang")
        for page, parsed in zip(a.pages, parsed_pages):
            paras = page_paragraphs(parsed)
            if not paras:
                sys.exit(f"❌ {page!r}: không rút được đoạn văn nào")
            part = header_part(parsed["wikitext"]) if a.header_titles else ""
            if part:   # tên đơn vị lấy từ đầu đề của trang, thay cho đuôi của tên trang (thường chỉ là số)
                page = page.rsplit("/", 1)[0] + "/" + part.replace("/", " ")
                # các dòng in hoa ở đầu trang (PHẦN I, CHƯƠNG I, tên chương) lặp lại tên đơn vị
                while len(paras) > 1 and (same_title(paras[0][1], part) or
                                          (not a.poem_titles and len(paras[0][1]) < 80
                                           and paras[0][1] == paras[0][1].upper())):
                    paras = paras[1:]
            if a.poem_titles:   # tập thơ: dòng in hoa ngắn là tên bài, thành đề mục để nhảy theo bài
                paras = [("h1", t.title()) if k == "p" and len(t) < 60 and t == t.upper() and re.search(r"\w", t)
                         else (k, t) for k, t in paras]
            if names:
                page = page.rsplit("/", 1)[0] + "/" + names[len(todo)].replace("/", " ")
            todo.append((page, paras))
    for unit_no, (page, paras) in enumerate(todo, start=1):
        tail = page.split("/")[-1]
        if single:
            unit_title = label = title
        elif roman(tail) and not a.header_titles:
            # Số La Mã mà để nguyên thì TTS đọc thành chữ cái; đổi sang số thường.
            unit_title, label = f"Chương {roman(tail)}", title
        else:
            unit_title, label = tail, f"{a.unit_word} {unit_no}"

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
