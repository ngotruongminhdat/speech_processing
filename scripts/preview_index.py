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
                f'<li class="done" data-ch="{i}"><a href="chapter_{i:02d}/preview.html?autoplay=1">'
                f'<em>{num}</em><span class="t">{title}</span><span class="dots"></span>'
                f'<b>🎧 {fmt(dur)}</b></a></li>'
            )
        else:
            rows.append(
                f'<li class="todo"><em>{num}</em><span class="t">{title}</span>'
                f'<span class="dots"></span><b>—</b></li>'
            )
    listen_href = f"chapter_{first_built:02d}/preview.html?autoplay=1" if first_built is not None else "#"

    # bản đồ số phần -> tiêu đề (chỉ phần đã build) cho nút "Nghe tiếp" phía client
    toc_titles_json = json.dumps(
        {str(i): t for i, t in units if unit_status(i)[0]}, ensure_ascii=False
    )

    # nút tải cả cuốn (nếu đã gộp bằng bundle_book.py)
    bundle = ROOT / "build" / f"{META['book_slug']}-DAISY.zip"
    if bundle.exists():
        dl_all = (f'<a class="btn ghost" href="{bundle.name}" '
                  f'download="{META["title"]} - Toàn bộ (DAISY).zip">'
                  f'⬇ Tải cả cuốn · {bundle.stat().st_size / 1e6:.0f} MB</a>')
    else:
        dl_all = ""

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
  .hero-in {{ position: relative; z-index: 2; max-width: 1020px; margin: 0 auto;
    padding: clamp(3rem, 7vw, 5.5rem) 1.4rem clamp(3.4rem, 7vw, 6rem);
    display: flex; gap: clamp(2rem, 5vw, 4rem); align-items: center; flex-wrap: wrap;
    justify-content: center; }}

  /* bìa sách 3D — rê chuột để mở bìa như lật sách */
  .book {{ perspective: 1400px; flex-shrink: 0; animation: rise .9s ease both;
    display: block; text-decoration: none; }}
  .book .vol {{ position: relative; width: clamp(230px, 30vw, 330px);
    transform: rotateY(-14deg); transform-style: preserve-3d;
    animation: float 5.5s ease-in-out infinite; }}
  @keyframes float {{ 0%, 100% {{ transform: rotateY(-14deg) translateY(0); }}
    50% {{ transform: rotateY(-14deg) translateY(-9px); }} }}
  .book .inner {{ aspect-ratio: 444 / 600; border-radius: 3px 8px 8px 3px;
    background: linear-gradient(105deg, #efe6d0, #fbf5e6 22%);
    box-shadow: 14px 24px 60px rgba(0, 0, 0, .55), inset 12px 0 18px -12px rgba(70, 50, 10, .45);
    display: flex; flex-direction: column; justify-content: center; gap: 1rem;
    padding: 1.6rem 1.4rem; color: #5b4a26; text-align: center; }}
  .book .inner q {{ quotes: none;  font-family: Georgia, serif; font-style: italic;
    font-size: clamp(.82rem, 1.3vw, 1rem); line-height: 1.75; }}
  .book .inner .who {{ font-size: .68rem; font-family: system-ui, sans-serif;
    letter-spacing: .12em; text-transform: uppercase; opacity: .65; }}
  .book .inner .credits {{ font-family: Georgia, serif; font-size: .7rem; line-height: 1.65;
    color: #6d5a30; padding-top: .8rem; margin-top: .2rem; position: relative; }}
  .book .inner .credits b {{ font-weight: 700; color: #55431e; }}
  .book .inner .credits::before {{ content: ''; position: absolute; top: 0; left: 50%;
    transform: translateX(-50%); width: 46px; height: 1px; background: #c9ae76; }}
  .book .inner .credits i {{ display: block; font-style: normal;
    font-family: system-ui, sans-serif; font-size: .58rem; font-weight: 600;
    letter-spacing: .14em; text-transform: uppercase; opacity: .6; margin-bottom: .3rem; }}
  .book .inner .play-hint {{ font-family: system-ui, sans-serif; font-size: .74rem;
    font-weight: 600; color: #a06a10; }}
  .book .leaf {{ position: absolute; inset: 0; transform-origin: left center;
    transform-style: preserve-3d; transition: transform 1s cubic-bezier(.25, .75, .3, 1); }}
  .book:hover .leaf {{ transform: rotateY(-138deg); }}
  .book .leaf img {{ display: block; width: 100%; height: 100%;
    border-radius: 3px 8px 8px 3px; backface-visibility: hidden;
    box-shadow: 10px 16px 40px rgba(0, 0, 0, .4); }}
  .book .leaf .backside {{ position: absolute; inset: 0; transform: rotateY(180deg);
    backface-visibility: hidden; border-radius: 8px 3px 3px 8px;
    background: linear-gradient(255deg, #efe6d0, #f9f2e2 30%);
    box-shadow: inset -10px 0 16px -10px rgba(70, 50, 10, .4); }}
  .book .pages {{ position: absolute; top: 1.2%; right: -9px; width: 10px; height: 97.6%;
    transform: rotateY(28deg);
    background: repeating-linear-gradient(to bottom, #f4ecd9 0 2px, #d9cdb2 2px 3px);
    border-radius: 0 3px 3px 0; }}
  @media (hover: none) {{ .book .leaf {{ transition: none; }} }}

  .lede {{ max-width: 520px; animation: rise .9s .12s ease both; }}
  .kicker {{ font-family: system-ui, sans-serif; font-size: .72rem; font-weight: 600;
    letter-spacing: .28em; text-transform: uppercase; opacity: .85; }}
  .lede h1 {{ font-size: clamp(2.1rem, 4.9vw, 3.42rem); line-height: 1.12;
    margin: .45rem 0 .3rem; font-weight: normal; white-space: nowrap;
    text-shadow: 0 2px 18px rgba(0,0,0,.35); }}
  @media (max-width: 700px) {{ .lede h1 {{ white-space: normal; }} }}
  .author {{ font-style: italic; font-size: 1.02rem; opacity: .9; }}
  .divider {{ display: flex; align-items: center; gap: .8rem; margin: 1.15rem auto;
    max-width: 300px; opacity: .85; }}
  .divider::before, .divider::after {{ content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, var(--hero-ink)); }}
  .divider::after {{ background: linear-gradient(90deg, var(--hero-ink), transparent); }}
  .divider i {{ font-style: normal; font-size: .8rem; transform: rotate(45deg); }}
  .lede p.desc {{ font-size: .95rem; line-height: 1.8; opacity: .92; margin: 0 0 1.4rem; text-align: justify; }}
  .cta {{ display: flex; gap: .8rem; flex-wrap: wrap; font-family: system-ui, sans-serif; margin-top: 1.5rem; }}
  .btn {{ display: inline-flex; align-items: center; gap: .55rem; text-decoration: none;
    font-size: .88rem; font-weight: 600; border-radius: 999px; padding: .72rem 1.5rem;
    transition: transform .18s ease, box-shadow .18s ease; }}
  .btn:hover {{ transform: translateY(-2px); }}
  .btn.primary {{ background: var(--hero-ink); color: #6b3410;
    box-shadow: 0 8px 26px rgba(0,0,0,.35); }}
  .btn.ghost {{ color: var(--hero-ink); border: 1px solid rgba(255,248,238,.55); }}
  .btn.ghost:hover {{ background: rgba(255,248,238,.12); }}
  .btn.resume {{ background: var(--accent); color: #fff8ee; box-shadow: 0 8px 26px rgba(0,0,0,.3); }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(18px); }}
    to {{ opacity: 1; transform: none; }} }}
  @media (prefers-reduced-motion: reduce) {{ .book, .lede, .book .vol {{ animation: none; }} }}

  /* thông tin xuất bản — khối nhỏ trong hero, dưới nút bấm */
  .metas {{ margin-top: .2rem; font-family: system-ui, sans-serif; font-size: .8rem;
    border-top: 1px solid rgba(255,248,238,.22); }}
  .metas div {{ display: flex; gap: 1rem; padding: .42rem 0; align-items: baseline;
    border-bottom: 1px solid rgba(255,248,238,.13); }}
  .metas span {{ flex: 0 0 108px; font-size: .66rem; font-weight: 600;
    letter-spacing: .12em; text-transform: uppercase; opacity: .62; }}
  .metas b {{ font-weight: 500; opacity: .95; }}

  /* ---- mural đầu tàu hơi nước (tranh sơn dầu) hòa vào nền trái ---- */
  .hero-art {{ position: absolute; left: 0; bottom: 0; width: min(62%, 720px); z-index: 1;
    pointer-events: none; opacity: .9;
    mask-image: linear-gradient(105deg, #000 30%, transparent 82%);
    -webkit-mask-image: linear-gradient(105deg, #000 30%, transparent 82%); }}
  .hero-art svg {{ display: block; width: 100%; height: auto; }}
  @media (max-width: 780px) {{ .hero-art {{ opacity: .5; width: 90%; }} }}

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
  .reset-btn {{ display: none; cursor: pointer; font-family: system-ui, sans-serif;
    font-size: .74rem; color: var(--ink-soft); background: transparent;
    border: 1px solid var(--line); border-radius: 999px; padding: .34rem .8rem;
    transition: background .15s ease, color .15s ease; }}
  .reset-btn:hover {{ background: var(--accent-soft); color: var(--ink); }}

  ol li.seen .t::after {{ content: ' ✓'; color: #3a9d5d; font-weight: 700; }}
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
  .metas .hitcount {{ height: 21px; vertical-align: -5px; border-radius: 4px; }}
</style>
</head>
<body>

<section class="hero">
  <div class="bg"></div>
  <div class="tint"></div>
  <div class="hero-art" aria-hidden="true">
    <svg viewBox="0 0 620 400" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <!-- nồi hơi: dải sáng kim loại gần đỉnh, tối dần xuống đáy -->
        <linearGradient id="gBoiler" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#7a5426"/><stop offset=".16" stop-color="#c99a4c"/>
          <stop offset=".26" stop-color="#e6c074"/><stop offset=".42" stop-color="#8a5f2e"/>
          <stop offset=".72" stop-color="#4a3016"/><stop offset="1" stop-color="#241608"/>
        </linearGradient>
        <linearGradient id="gCab" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#6a481f"/><stop offset=".28" stop-color="#9a6c33"/>
          <stop offset=".6" stop-color="#4a3016"/><stop offset="1" stop-color="#20140a"/>
        </linearGradient>
        <linearGradient id="gDark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#3d2913"/><stop offset="1" stop-color="#170d05"/>
        </linearGradient>
        <radialGradient id="gSmoke" cx=".36" cy=".32" r=".85">
          <stop offset="0" stop-color="#6f4c24"/><stop offset=".6" stop-color="#2e1e0d"/>
          <stop offset="1" stop-color="#140c04"/>
        </radialGradient>
        <radialGradient id="gWheel" cx=".36" cy=".3" r=".85">
          <stop offset="0" stop-color="#6a4a22"/><stop offset=".55" stop-color="#2c1c0c"/>
          <stop offset="1" stop-color="#120b03"/>
        </radialGradient>
        <linearGradient id="gRod" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#c9b48a"/><stop offset=".5" stop-color="#6d5a38"/>
          <stop offset="1" stop-color="#2c2214"/>
        </linearGradient>
        <filter id="oil" x="-28%" y="-28%" width="156%" height="156%">
          <feTurbulence type="fractalNoise" baseFrequency="0.011 0.017" numOctaves="3" seed="11" result="n"/>
          <feDisplacementMap in="SourceGraphic" in2="n" scale="8" xChannelSelector="R" yChannelSelector="G" result="d"/>
          <feGaussianBlur in="d" stdDeviation="0.5"/>
        </filter>
        <filter id="soft" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="7"/>
        </filter>
      </defs>
      <!-- khói hơi nước: tản mềm, dày dần lên cao -->
      <g fill="#efe0be" filter="url(#soft)">
        <circle cx="168" cy="78" r="34" opacity=".13"/>
        <circle cx="150" cy="40" r="26" opacity=".10"/>
        <circle cx="214" cy="52" r="30" opacity=".11"/>
        <circle cx="196" cy="92" r="22" opacity=".12"/>
        <circle cx="250" cy="34" r="22" opacity=".08"/>
      </g>
      <!-- bóng đổ dưới máy -->
      <ellipse cx="300" cy="314" rx="250" ry="15" fill="#120a03" opacity=".5" filter="url(#soft)"/>
      <g filter="url(#oil)">
        <!-- xà đỡ + cản trước -->
        <path d="M26 308 L98 308 L98 250 Z" fill="url(#gDark)"/>
        <rect x="94" y="240" width="376" height="16" rx="3" fill="#231506"/>
        <rect x="94" y="240" width="376" height="4" fill="#7a5a2e" opacity=".4"/>
        <!-- nồi hơi -->
        <rect x="112" y="150" width="322" height="96" rx="47" fill="url(#gBoiler)"/>
        <!-- gờ đai + đổ bóng dưới bụng nồi hơi -->
        <path d="M235 151 v94 M312 151 v92" stroke="#1d1207" stroke-width="5" opacity=".45"/>
        <path d="M118 232 q156 20 308 0 v10 q-156 20 -308 0 Z" fill="#160d04" opacity=".4"/>
        <!-- mặt trước (smokebox) khối cầu -->
        <circle cx="132" cy="198" r="50" fill="url(#gSmoke)"/>
        <path d="M104 168 a50 50 0 0 1 44 -18" fill="none" stroke="#c39a52" stroke-width="4" opacity=".35"/>
        <circle cx="132" cy="198" r="11" fill="#241708"/>
        <!-- ống khói -->
        <path d="M150 150 L192 150 L201 98 L141 98 Z" fill="url(#gDark)"/>
        <path d="M143 100 L152 150" stroke="#a9803f" stroke-width="3" opacity=".3"/>
        <ellipse cx="171" cy="96" rx="33" ry="7" fill="#2c1c0c"/>
        <ellipse cx="171" cy="94" rx="33" ry="6" fill="#5c4022" opacity=".7"/>
        <!-- vòm hơi + vòm cát (khối cầu nhỏ) -->
        <ellipse cx="250" cy="149" rx="27" ry="22" fill="url(#gBoiler)"/>
        <ellipse cx="243" cy="140" rx="9" ry="5" fill="#eccf86" opacity=".5"/>
        <ellipse cx="320" cy="150" rx="22" ry="18" fill="url(#gBoiler)"/>
        <!-- đèn pha -->
        <circle cx="119" cy="160" r="13" fill="#221606"/>
        <circle cx="119" cy="160" r="8" fill="#f4e3ab" opacity=".85"/>
        <!-- ca-bin -->
        <path d="M404 122 h150 l-8 -14 h-134 Z" fill="url(#gDark)"/>
        <rect x="420" y="120" width="122" height="126" rx="5" fill="url(#gCab)"/>
        <rect x="442" y="140" width="66" height="60" rx="8" fill="#0f0a04"/>
        <rect x="446" y="176" width="58" height="22" rx="4" fill="#c79a4e" opacity=".28"/>
        <path d="M456 236 h70" stroke="#1a1006" stroke-width="6" opacity=".5"/>
        <!-- thanh truyền kim loại -->
        <rect x="246" y="267" width="122" height="8" rx="4" fill="url(#gRod)"/>
        <rect x="246" y="267" width="122" height="2" fill="#e4d3a6" opacity=".55"/>
        <!-- bánh xe: lốp tối, vành, đối trọng, nan hoa -->
        <g>
          <circle cx="152" cy="282" r="26" fill="#140c04"/>
          <circle cx="152" cy="282" r="20" fill="url(#gWheel)"/>
          <circle cx="252" cy="262" r="47" fill="#140c04"/>
          <circle cx="252" cy="262" r="39" fill="url(#gWheel)"/>
          <circle cx="362" cy="262" r="47" fill="#140c04"/>
          <circle cx="362" cy="262" r="39" fill="url(#gWheel)"/>
          <circle cx="480" cy="278" r="31" fill="#140c04"/>
          <circle cx="480" cy="278" r="24" fill="url(#gWheel)"/>
        </g>
        <g stroke="#3f2c14" stroke-width="2.4" opacity=".85" stroke-linecap="round">
          <path d="M252 226 v72 M216 262 h72 M227 237 l50 50 M277 237 l-50 50"/>
          <path d="M362 226 v72 M326 262 h72 M337 237 l50 50 M387 237 l-50 50"/>
        </g>
        <!-- đối trọng -->
        <path d="M252 262 m0 30 a30 30 0 0 1 -22 -12 l22 -18 Z" fill="#241708" opacity=".9"/>
        <path d="M362 262 m0 30 a30 30 0 0 1 -22 -12 l22 -18 Z" fill="#241708" opacity=".9"/>
        <circle cx="252" cy="262" r="7" fill="#8a6c3c"/>
        <circle cx="362" cy="262" r="7" fill="#8a6c3c"/>
        <!-- vệt sáng bóng đổ trên lốp trên-trái -->
        <g fill="none" stroke="#caa257" stroke-width="3" opacity=".3" stroke-linecap="round">
          <path d="M234 236 a40 40 0 0 1 20 -13"/>
          <path d="M344 236 a40 40 0 0 1 20 -13"/>
        </g>
      </g>
    </svg>
  </div>
  <div class="hero-in">
    <a class="book" href="{listen_href}" title="Bấm để bắt đầu nghe">
      <div class="vol">
        <div class="inner">
          <q>“Hãy để các cháu phát triển tự nhiên. Đừng cản trở khát vọng của các cháu. Ước mơ của các cháu lớn hơn mơ ước của các cô.”</q>
          <div class="who">— Thầy hiệu trưởng Kobayashi —</div>
          <div class="credits">
            <i>Nhóm Totto-chan thực hiện</i>
            <b>{"</b><br><b>".join(m.strip() for m in META['collector'].split(','))}</b>
          </div>
          <div class="play-hint">▶ Bấm để bắt đầu nghe</div>
        </div>
        <div class="leaf">
          <img src="cover.jpg" alt="Bìa sách {META['title']}">
          <div class="backside"></div>
        </div>
        <div class="pages"></div>
      </div>
    </a>
    <div class="lede">
      <div class="kicker">Sách nói DAISY · {META['subject']}</div>
      <h1>{META['title']}</h1>
      <div class="author">{META['creator']}</div>
      <div class="divider"><i>◆</i></div>
      <p class="desc">{META['description']}</p>
      <div class="metas">
        <div><span>Tác giả</span><b>{META['creator']}</b></div>
        <div><span>ISBN</span><b>{META['source']}</b></div>
        <div><span>Nhà xuất bản</span><b>{META['publisher']}</b></div>
        <div><span>Năm xuất bản</span><b>{META['date']}</b></div>
        <div><span>Ngôn ngữ</span><b>Tiếng Việt</b></div>
        <div><span>Thể loại</span><b>{META['subject']}</b></div>
        <div><span>Giọng đọc</span><b>{META.get('narrator', '')}</b></div>
        <div><span>Định dạng</span><b>Sách nói DAISY 3 (Audio MP3)</b></div>
        <div><span>Thời lượng</span><b>{fmt(total_s)}</b></div>
        <div><span>Lượt xem</span><b><img class="hitcount" src="https://hits.sh/ngotruongminhdat.github.io/speech_processing.svg?label=%20&color=b8860b&labelColor=00000000" alt="lượt xem"></b></div>
      </div>
      <div class="cta">
        <a class="btn primary" href="{listen_href}">▶&nbsp; Bắt đầu nghe</a>
        <a class="btn resume" id="resume" href="#" style="display:none"></a>
        <a class="btn ghost" href="#muc-luc">Mục lục</a>
        {dl_all}
      </div>
    </div>
  </div>
</section>

<div class="wrap" id="muc-luc">
  <div class="toc-head">
    <h2>Mục lục</h2>
    <button class="reset-btn" id="resetProg" title="Xoá vị trí đang nghe và dấu đã nghe của mọi phần">↺ Đặt lại tiến độ</button>
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
<script>
  // đánh dấu ✓ các phần đã nghe xong + nút "Nghe tiếp" (lưu trong máy người xem)
  (function () {{
    let done = [];
    try {{ done = JSON.parse(localStorage.getItem('ttc-done')) || []; }} catch (e) {{}}
    done.forEach(ch => {{
      const li = document.querySelector('li[data-ch="' + ch + '"]');
      if (li) li.classList.add('seen');
    }});
    const last = localStorage.getItem('ttc-last');
    const titles = {toc_titles_json};
    if (last !== null && document.querySelector('li[data-ch="' + last + '"]') && titles[last]) {{
      const r = document.getElementById('resume');
      r.textContent = '⏵ Nghe tiếp: ' + titles[last];
      r.href = 'chapter_' + String(last).padStart(2, '0') + '/preview.html?autoplay=1';
      r.style.display = '';
    }}
    // nút đặt lại tiến độ — chỉ hiện khi có tiến độ đã lưu
    const hasProgress = done.length || last !== null ||
      Object.keys(localStorage).some(k => k.indexOf('ttc-pos-') === 0);
    const resetBtn = document.getElementById('resetProg');
    if (hasProgress) resetBtn.style.display = 'inline-block';
    resetBtn.addEventListener('click', () => {{
      if (!confirm('Đặt lại toàn bộ tiến độ nghe về 0?\\n(Vị trí đang nghe và dấu ✓ của mọi phần sẽ bị xoá. Cài đặt cỡ chữ, giao diện vẫn giữ nguyên.)')) return;
      Object.keys(localStorage).filter(k => k === 'ttc-done' || k === 'ttc-last' || k.indexOf('ttc-pos-') === 0)
        .forEach(k => localStorage.removeItem(k));
      location.reload();
    }});
  }})();
</script>
</body>
</html>
"""
    out = ROOT / "build" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ {out} ({built_n}/{len(units)} phần, {fmt(total_s)} audio)")


if __name__ == "__main__":
    gen()
