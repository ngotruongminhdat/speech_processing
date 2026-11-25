#!/usr/bin/env python3
"""Dựng bìa sách từ ảnh thuộc phạm vi công cộng hoặc CC0 trên Wikimedia Commons.

Ảnh gốc và giấy phép ghi ở books/<slug>/metadata/cover_source.json. Ảnh nguồn đặt
trong thư mục truyền vào (mặc định pipeline/assets/cover_src/<slug>.jpg). Kết quả:
books/<slug>/metadata/cover.jpg, 888x1200, build_site.py chép sang site/.

Dùng:  python3 pipeline/scripts/make_covers.py [thư_mục_ảnh_nguồn]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO = Path(__file__).resolve().parent.parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "pipeline" / "assets" / "cover_src"
W, H = 888, 1200
FONT = "/usr/share/fonts/truetype/noto/NotoSerif-{}.ttf"
CREAM = (255, 246, 228)

# crop: phần ảnh giữ lại (trái, trên, phải, dưới) theo tỉ lệ, để bỏ viền kính ảnh và chữ ghi chú
# focus: tâm cắt theo tỉ lệ khi ảnh không cùng tỉ lệ với bìa
# band: vị trí chữ ("bottom" hoặc "top"); style "photo" phủ nền tối dần sau chữ, "plate" là tranh vẽ trên nền sáng
BOOKS = {
    "lao-hac": dict(title="Lão Hạc", author="Nam Cao", crop=(.05, .06, .95, .95), focus=(.62, .5), band="bottom", style="photo"),
    "hai-dua-tre": dict(title="Hai đứa trẻ", author="Thạch Lam", crop=(.05, .06, .95, .95), focus=(.5, .6), band="top", style="photo"),
    "gio-lanh-dau-mua": dict(title="Gió lạnh\nđầu mùa", author="Thạch Lam", crop=(.06, .05, .96, .95), focus=(.32, .5), band="top", style="photo"),
    "co-hang-xen": dict(title="Cô hàng xén", author="Thạch Lam", crop=(.05, .06, .95, .95), focus=(.5, .5), band="bottom", style="photo"),
    "duoi-bong-hoang-lan": dict(title="Dưới bóng\nhoàng lan", author="Thạch Lam", crop=(0, 0, 1, 1), focus=(.5, .5), band="top", style="plate"),
    "tat-den": dict(crop=(.035, .02, .965, .955), focus=(.5, .8), style="scan"),
    "truyen-kieu": dict(title="Truyện Kiều", author="Nguyễn Du", crop=(.02, .02, .86, .98), focus=(.5, .35), band="bottom", style="photo"),
    "truyen-ky-man-luc": dict(crop=(.03, .02, .97, .97), focus=(.5, .3), style="scan"),
    "chi-pheo": dict(crop=(.02, .015, .98, .955), focus=(.5, .3), style="scan"),
    "ha-noi-bam-sau-pho-phuong": dict(title="Hà Nội băm sáu\nphố phường", author="Thạch Lam", crop=(.07, .05, .97, .94), focus=(.45, .5), band="bottom", style="photo"),
    "viet-nam-su-luoc-1": dict(crop=(.02, .02, .98, .98), focus=(.5, .4), style="scan"),
    "chinh-phu-ngam": dict(title="Chinh phụ ngâm", author="Đặng Trần Côn · Đoàn Thị Điểm", crop=(0, 0, 1, 1), focus=(.5, .3), band="bottom", style="plate"),
    "tho-han-mac-tu": dict(title="Thơ Hàn Mặc Tử", author="Hàn Mặc Tử", crop=(.03, .03, .93, .9), focus=(.5, .5), band="bottom", style="photo"),
    "viet-nam-phong-tuc-1": dict(crop=(.02, .01, .98, .99), focus=(.5, .4), style="scan"),
}


def font(weight, size):
    return ImageFont.truetype(FONT.format(weight), size)


def fill(img, focus):
    """Cắt ảnh cho vừa khít bìa, giữ vùng quanh tâm focus."""
    return ImageOps.fit(img, (W, H), Image.LANCZOS, centering=focus)


def shade(img, band):
    """Phủ nền tối dần ở phía có chữ để chữ luôn đủ tương phản."""
    grad = Image.new("L", (1, H))
    for y in range(H):
        d = (y / H) if band == "bottom" else (1 - y / H)
        grad.putpixel((0, y), int(235 * max(0, (d - .42) / .58) ** 1.25))
    dark = Image.new("RGB", (W, H), (22, 14, 8))
    return Image.composite(dark, img, grad.resize((W, H)))


def text_block(draw, title, author, band, ink, rule):
    size = 108 if max(len(x) for x in title.split("\n")) <= 9 else 92
    ft, fa = font("SemiBold", size), font("Medium", 34)
    lines = title.split("\n")
    lh = int(size * 1.16)
    block = lh * len(lines) + 34 + 50
    y = 92 if band == "top" else H - 96 - block
    for ln in lines:
        draw.text((W / 2, y), ln, font=ft, fill=ink, anchor="ma")
        y += lh
    y += 22
    draw.line((W / 2 - 60, y, W / 2 + 60, y), fill=rule, width=3)
    draw.text((W / 2, y + 26), author.upper(), font=fa, fill=ink, anchor="ma")


def make(slug, spec):
    src = Image.open(SRC / f"{slug}.jpg").convert("RGB")
    w, h = src.size
    l, t, r, b = spec["crop"]
    src = src.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    if spec["style"] == "scan":                       # bìa gốc của lần in đầu: giữ nguyên, chỉ cắt lề
        out = ImageOps.fit(src, (W, H), Image.LANCZOS, centering=spec["focus"])
    elif spec["style"] == "plate":                    # tranh thực vật trên nền trắng: đặt lên nền giấy, chữ màu sẫm
        out = Image.new("RGB", (W, H), (247, 240, 222))
        pic = ImageOps.contain(src, (W - 170, H - 560), Image.LANCZOS)
        mask = ImageOps.invert(pic.convert("L")).point(lambda v: 255 if v > 14 else v * 18)
        out.paste(pic, ((W - pic.width) // 2, H - pic.height - 70), mask.filter(ImageFilter.GaussianBlur(1)))
        d = ImageDraw.Draw(out)
        text_block(d, spec["title"], spec["author"], "top", (38, 62, 30), (150, 120, 40))
    else:
        out = shade(fill(src, spec["focus"]), spec["band"])
        d = ImageDraw.Draw(out)
        text_block(d, spec["title"], spec["author"], spec["band"], CREAM, (226, 178, 84))
    d = ImageDraw.Draw(out)
    if spec["style"] != "scan":
        d.rectangle((26, 26, W - 27, H - 27), outline=(226, 178, 84) if spec["style"] == "photo" else (150, 120, 40), width=3)
    dest = REPO / "books" / slug / "metadata" / "cover.jpg"
    out.save(dest, quality=88, optimize=True, progressive=True)
    print(f"✅ {dest.relative_to(REPO)}  {dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    for slug, spec in BOOKS.items():
        if (SRC / f"{slug}.jpg").exists():
            make(slug, spec)
        else:
            print(f"⚠️  thiếu ảnh nguồn {slug}.jpg")
