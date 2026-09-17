#!/usr/bin/env python3
"""Tải font Lora (OFL, đủ tiếng Việt) về build/fonts/ và sinh @font-face css.

Chạy 1 lần để self-host font, tránh lỗi thiếu glyph tiếng Việt trên máy khác.
Sinh: build/fonts/*.woff2 + scripts/_fontface_lora.css (dùng __P__ làm prefix
đường dẫn để mỗi trang tự thay '' (index) hoặc '../' (trang chương)).
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "build" / "fonts"
FONTS.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
CSS_URL = "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&display=swap"
KEEP = {"latin", "latin-ext", "vietnamese"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req).read()


def main():
    css = fetch(CSS_URL).decode("utf-8")
    # tách theo comment subset: "/* latin */\n@font-face{...}"
    blocks = re.split(r"/\* ([a-z-]+) \*/", css)
    out_faces, n = [], 0
    for i in range(1, len(blocks), 2):
        subset = blocks[i]
        face = blocks[i + 1]
        if subset not in KEEP or "@font-face" not in face:
            continue
        style = re.search(r"font-style:\s*(\w+)", face).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", face).group(1)
        urange = re.search(r"unicode-range:\s*([^;]+);", face).group(1).strip()
        woff = re.search(r"url\((https://[^)]+\.woff2)\)", face).group(1)
        name = f"lora-{weight}-{style}-{subset}.woff2"
        (FONTS / name).write_bytes(fetch(woff))
        n += 1
        out_faces.append(
            "@font-face{font-family:'Lora';font-style:%s;font-weight:%s;font-display:swap;"
            "src:url(__P__fonts/%s) format('woff2');unicode-range:%s;}"
            % (style, weight, name, urange)
        )
    (ROOT / "scripts" / "_fontface_lora.css").write_text("\n".join(out_faces) + "\n", encoding="utf-8")
    print(f"✅ tải {n} file woff2 -> build/fonts/")
    print(f"✅ scripts/_fontface_lora.css ({len(out_faces)} @font-face)")


if __name__ == "__main__":
    main()
