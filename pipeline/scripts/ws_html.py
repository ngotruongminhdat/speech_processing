#!/usr/bin/env python3
"""Rút đoạn văn từ HTML của một trang Wikisource.

Nhiều tác phẩm trên Wikisource được ghép từ bản quét đã hiệu đính (<pages index=... />),
nên wikitext của trang không chứa chữ nào; phải lấy từ HTML đã dựng. Hàm paragraphs()
trả về [(type, text)] như to_paragraphs() của import_wikisource: 'h1' cho đề mục, 'p' cho đoạn.

Bỏ đi: số trang, chú thích cuối trang và dấu gọi chú thích, bảng, hộp bản quyền, và các dòng
chữ Hán (giọng đọc tiếng Việt không đọc được; phần phiên âm và bản dịch đi kèm vẫn giữ).
"""
import re
import unicodedata
from html.parser import HTMLParser

CJK = re.compile(r"[⺀-⿟぀-ヿ㐀-䶿一-鿿豈-﫿\U00020000-\U0002ffff]")
SKIP_CLASS = re.compile(r"\b(reference|references|mw-references-wrap|pagenum|ws-noexport|licenseContainer|"
                        r"license|noprint|mw-editsection|catlinks|ws-pagenum|header-mainblock|header_notes|"
                        r"wst-rule|printfooter)\b")
BLOCK = {"p", "div", "li", "dd", "dt", "blockquote", "h1", "h2", "h3", "h4", "h5", "tr", "center"}
HEAD = {"h2", "h3", "h4", "h5"}
VOID = {"br", "img", "hr", "input", "link", "meta", "wbr"}


class _Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.buf = [], []
        self.lines = []          # từng dòng trước khi nối thành đoạn (để giữ chỗ ngắt dòng của thơ)
        self.stack = []          # (tag, bỏ qua?, là thơ?)
        self.skip = 0
        self.head = False

    def flush(self):
        raw = "".join(self.buf)
        self.buf = []
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.split("\n")]
        # chữ Hán: bỏ chữ, giữ phần còn lại của dòng; dòng chỉ có chữ Hán thì mất hẳn
        lines = [re.sub(r"\(\s*\)", "", re.sub(r"\s+", " ", CJK.sub("", ln))).strip() for ln in lines]
        lines = [ln for ln in lines if re.search(r"\w", ln)]
        self.lines += [unicodedata.normalize("NFC", ln) for ln in lines]
        text = unicodedata.normalize("NFC", " ".join(lines)).strip()
        text = re.sub(r"\s+([,.;:!?…])", r"\1", text)
        if re.search(r"\w", text):
            self.out.append(("h1" if self.head else "p", text))
        self.head = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "br":
            self.buf.append("\n")
            return
        if tag in VOID:
            return
        cls = a.get("class") or ""
        skip = bool(SKIP_CLASS.search(cls)) or tag in ("table", "style", "script", "sup") or a.get("id") == "headerContainer"
        self.stack.append((tag, skip))
        if skip:
            self.skip += 1
        elif tag in BLOCK and not self.skip:
            self.flush()
            self.head = tag in HEAD

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, skip = self.stack.pop()
            if skip:
                self.skip -= 1
            elif t in BLOCK and not self.skip:
                self.flush()
            if t == tag:
                break

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data.replace("\n", " "))


def lines(html: str):
    """Từng dòng chữ theo thứ tự trong trang, chưa nối thành đoạn: dùng để giữ chỗ ngắt dòng của thơ."""
    i = html.find('class="prp-pages-output"')
    if i >= 0:
        html = html[html.rfind("<", 0, i):]
    p = _Extract()
    p.feed(html)
    p.flush()
    return p.lines


def paragraphs(html: str):
    i = html.find('class="prp-pages-output"')
    if i >= 0:
        html = html[html.rfind("<", 0, i):]
    p = _Extract()
    p.feed(html)
    p.flush()
    return p.out
