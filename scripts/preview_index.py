#!/usr/bin/env python3
"""Tạo build/index.html — trang bìa của cả cuốn sách (landing page).

Gồm: hero với bìa 3D trên nền ambient, nút nghe, mục lục leader-dot
dẫn vào preview.html của từng chương đã build.

Usage: python scripts/preview_index.py
"""
import csv
import json
from pathlib import Path

from extract_chapter import unit_titles

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))


def unit_status(i: int):
    ch = ROOT / "build" / f"chapter_{i:02d}"
    ts = ch / "timestamps.csv"
    if not (ch / "preview.html").exists() or not ts.exists():
        return False, 0.0
    with open(ts, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return True, (max(float(r["clipEnd"]) for r in rows) if rows else 0.0)


def fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def gen():
    units = [(no, title) for no, _label, title in unit_titles()]
    last_no = units[-1][0]
    rows, built_n, total_s, first_built = [], 0, 0.0, None
    for i, title in units:
        built, dur = unit_status(i)
        num = "★" if i == 0 else ("✦" if i == last_no else f"{i:02d}")
        if built:
            built_n += 1
            total_s += dur
            if first_built is None:
                first_built = i
            rows.append(
                f'<li class="done"><a href="chapter_{i:02d}/preview.html?autoplay=1">'
                f'<em>{num}</em><span class="t">{title}</span><span class="dots"></span>'
                f'<b>🎧 {fmt(dur)}</b></a></li>'
            )
        else:
            rows.append(
                f'<li class="todo"><em>{num}</em><span class="t">{title}</span>'
                f'<span class="dots"></span><b>—</b></li>'
            )
    listen_href = f"chapter_{first_built:02d}/preview.html?autoplay=1" if first_built is not None else "#"

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{META['title']} — {META['creator']}</title>
<style>
  :root {{
    --paper: #f7f1e5; --ink: #2b2214; --ink-soft: #85795e;
    --accent: #c1651f; --accent-2: #b8860b; --accent-soft: #f7e3c8;
    --card: #fffdf8; --line: #e6dbc4; --shadow: 0 18px 50px rgba(90, 55, 15, .16);
    --hero-ink: #fff8ee;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --paper: #17130e; --ink: #ece3d0; --ink-soft: #a2937a;
      --accent: #e08a45; --accent-2: #d4a531; --accent-soft: #3b2b16;
      --card: #201a13; --line: #37301f; --shadow: 0 18px 50px rgba(0, 0, 0, .55);
    }}
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{ margin: 0; background: var(--paper); color: var(--ink);
    font-family: Georgia, 'Times New Roman', serif; }}
  ::selection {{ background: var(--accent-soft); }}

  /* ================= HERO ================= */
  .hero {{ position: relative; overflow: hidden; color: var(--hero-ink); }}
  .hero .bg {{ position: absolute; inset: -40px; background: url('cover.jpg') center/cover;
    filter: blur(48px) saturate(1.15) brightness(.62); transform: scale(1.25); }}
  .hero .tint {{ position: absolute; inset: 0;
    background: linear-gradient(160deg, rgba(40,18,4,.25), rgba(24,10,2,.72) 78%); }}
  .hero-in {{ position: relative; max-width: 860px; margin: 0 auto;
    padding: clamp(3rem, 7vw, 5.5rem) 1.4rem clamp(3.4rem, 7vw, 6rem);
    display: flex; gap: clamp(2rem, 5vw, 4rem); align-items: center; flex-wrap: wrap;
    justify-content: center; }}

  /* bìa sách 3D */
  .book {{ perspective: 1200px; flex-shrink: 0; animation: rise .9s ease both; }}
  .book .vol {{ position: relative; width: clamp(190px, 24vw, 250px);
    transform: rotateY(-14deg); transform-style: preserve-3d; transition: transform .5s ease; }}
  .book:hover .vol {{ transform: rotateY(-6deg); }}
  .book img {{ display: block; width: 100%; height: auto; border-radius: 3px 8px 8px 3px;
    box-shadow: 14px 24px 60px rgba(0, 0, 0, .55); }}
  .book .pages {{ position: absolute; top: 1.2%; right: -9px; width: 10px; height: 97.6%;
    transform: rotateY(28deg);
    background: repeating-linear-gradient(to bottom, #f4ecd9 0 2px, #d9cdb2 2px 3px);
    border-radius: 0 3px 3px 0; }}

  .lede {{ max-width: 480px; animation: rise .9s .12s ease both; }}
  .kicker {{ font-family: system-ui, sans-serif; font-size: .72rem; font-weight: 600;
    letter-spacing: .28em; text-transform: uppercase; opacity: .85; }}
  .lede h1 {{ font-size: clamp(2.1rem, 4.6vw, 3.1rem); line-height: 1.12;
    margin: .45rem 0 .3rem; font-weight: normal; text-wrap: balance;
    text-shadow: 0 2px 18px rgba(0,0,0,.35); }}
  .author {{ font-style: italic; font-size: 1.02rem; opacity: .9; }}
  .divider {{ display: flex; align-items: center; gap: .8rem; margin: 1.15rem 0;
    max-width: 300px; opacity: .85; }}
  .divider::before, .divider::after {{ content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, var(--hero-ink)); }}
  .divider::after {{ background: linear-gradient(90deg, var(--hero-ink), transparent); }}
  .divider i {{ font-style: normal; font-size: .8rem; transform: rotate(45deg); }}
  .lede p.desc {{ font-size: .95rem; line-height: 1.8; opacity: .92; margin: 0 0 1.4rem; }}
  .cta {{ display: flex; gap: .8rem; flex-wrap: wrap; font-family: system-ui, sans-serif; }}
  .btn {{ display: inline-flex; align-items: center; gap: .55rem; text-decoration: none;
    font-size: .88rem; font-weight: 600; border-radius: 999px; padding: .72rem 1.5rem;
    transition: transform .18s ease, box-shadow .18s ease; }}
  .btn:hover {{ transform: translateY(-2px); }}
  .btn.primary {{ background: var(--hero-ink); color: #6b3410;
    box-shadow: 0 8px 26px rgba(0,0,0,.35); }}
  .btn.ghost {{ color: var(--hero-ink); border: 1px solid rgba(255,248,238,.55); }}
  .btn.ghost:hover {{ background: rgba(255,248,238,.12); }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(18px); }}
    to {{ opacity: 1; transform: none; }} }}

  /* dải thông tin xuất bản */
  .factbar {{ position: relative; border-top: 1px solid rgba(255,248,238,.18); }}
  .factbar-in {{ max-width: 860px; margin: 0 auto; padding: .85rem 1.4rem;
    display: flex; flex-wrap: wrap; gap: .4rem 2.4rem;
    font-family: system-ui, sans-serif; font-size: .74rem; opacity: .88; }}
  .factbar b {{ font-weight: 600; }}

  /* ================= MỤC LỤC ================= */
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 3rem 1.4rem 4rem; }}
  .toc-head {{ display: flex; align-items: baseline; justify-content: space-between;
    gap: 1rem; margin-bottom: 1.1rem; flex-wrap: wrap; }}
  .toc-head h2 {{ font-size: 1.35rem; font-weight: normal; margin: 0; }}
  .toc-head h2::after {{ content: ''; display: block; width: 64px; height: 3px;
    margin-top: .45rem; border-radius: 2px;
    background: linear-gradient(90deg, var(--accent), transparent); }}
  .toc-note {{ font-family: system-ui, sans-serif; font-size: .76rem; color: var(--ink-soft); }}
  .toc-note b {{ color: var(--accent); font-weight: 600; }}

  .toc-card {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px;
    box-shadow: var(--shadow); padding: 1.1rem 1.4rem; }}
  ol {{ list-style: none; margin: 0; padding: 0;
    column-count: 2; column-gap: 2.6rem; }}
  @media (max-width: 720px) {{ ol {{ column-count: 1; }} }}
  ol li {{ break-inside: avoid; }}
  ol li a, ol li.todo {{ display: flex; align-items: baseline; gap: .6rem;
    padding: .5rem .45rem; text-decoration: none; color: var(--ink);
    border-radius: 9px; transition: background .18s ease, padding-left .18s ease; }}
  ol li a:hover {{ background: var(--accent-soft); padding-left: .8rem; }}
  ol li em {{ font-style: normal; font-family: system-ui, sans-serif; font-size: .7rem;
    font-weight: 700; color: var(--accent); min-width: 1.7em; }}
  ol li .t {{ font-size: .95rem; }}
  ol li .dots {{ flex: 1; border-bottom: 1px dotted var(--line); transform: translateY(-4px);
    min-width: 1.2rem; }}
  ol li b {{ font-family: system-ui, sans-serif; font-size: .7rem; font-weight: 500;
    color: var(--ink-soft); white-space: nowrap; }}
  ol li.done b {{ color: var(--accent); }}
  ol li.todo {{ opacity: .4; }}

  footer {{ text-align: center; color: var(--ink-soft); font-size: .78rem;
    margin-top: 2.6rem; font-family: system-ui, sans-serif; line-height: 1.8; }}
  footer .mark {{ color: var(--accent); font-size: .9rem; }}
  footer .members {{ display: inline-block; margin-top: .35rem; color: var(--ink);
    font-size: .8rem; letter-spacing: .02em; }}
</style>
</head>
<body>

<section class="hero">
  <div class="bg"></div>
  <div class="tint"></div>
  <div class="hero-in">
    <div class="book">
      <div class="vol">
        <img src="cover.jpg" alt="Bìa sách {META['title']}">
        <div class="pages"></div>
      </div>
    </div>
    <div class="lede">
      <div class="kicker">Sách nói DAISY · {META['subject']}</div>
      <h1>{META['title']}</h1>
      <div class="author">{META['creator']}</div>
      <div class="divider"><i>◆</i></div>
      <p class="desc">{META['description']}</p>
      <div class="cta">
        <a class="btn primary" href="{listen_href}">▶&nbsp; Bắt đầu nghe</a>
        <a class="btn ghost" href="#muc-luc">Mục lục</a>
      </div>
    </div>
  </div>
  <div class="factbar">
    <div class="factbar-in">
      <div>ISBN&nbsp;<b>{META['source']}</b></div>
      <div><b>{META['publisher']}</b></div>
      <div>Năm&nbsp;<b>{META['date']}</b></div>
      <div>Ngôn ngữ&nbsp;<b>Tiếng Việt</b></div>
      <div>Giọng đọc&nbsp;<b>{META.get('narrator', '')}</b></div>
      <div>Định dạng&nbsp;<b>Sách nói DAISY 3 (MP3)</b></div>
      <div>Thời lượng&nbsp;<b>🎧 {fmt(total_s)}</b></div>
    </div>
  </div>
</section>

<div class="wrap" id="muc-luc">
  <div class="toc-head">
    <h2>Mục lục</h2>
  </div>
  <div class="toc-card">
    <ol>
{chr(10).join('      ' + r for r in rows)}
    </ol>
  </div>
  <footer>
    <div class="mark">◆</div>
    Bộ dữ liệu sách nói DAISY dành cho người khiếm thị<br>
    Đồ án giữa kỳ Xử lý tiếng nói K35 · Nhóm Totto-chan<br>
    <span class="members">{" · ".join(m.strip() for m in META['collector'].split(','))}</span>
  </footer>
</div>
</body>
</html>
"""
    out = ROOT / "build" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ {out} ({built_n}/{len(units)} phần, {fmt(total_s)} audio)")


if __name__ == "__main__":
    gen()
