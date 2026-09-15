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
        <linearGradient id="gBoiler" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#d3a951"/><stop offset=".5" stop-color="#82562a"/>
          <stop offset="1" stop-color="#3a2611"/>
        </linearGradient>
        <linearGradient id="gDark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#4c341a"/><stop offset="1" stop-color="#211508"/>
        </linearGradient>
        <radialGradient id="gWheel" cx=".38" cy=".34" r=".75">
          <stop offset="0" stop-color="#7a5527"/><stop offset="1" stop-color="#190f04"/>
        </radialGradient>
        <filter id="oil" x="-25%" y="-25%" width="150%" height="150%">
          <feTurbulence type="fractalNoise" baseFrequency="0.013 0.02" numOctaves="3" seed="7" result="n"/>
          <feDisplacementMap in="SourceGraphic" in2="n" scale="11" xChannelSelector="R" yChannelSelector="G" result="d"/>
          <feGaussianBlur in="d" stdDeviation="0.55"/>
        </filter>
      </defs>
      <!-- khói hơi nước -->
      <g fill="#f3e4c2" filter="url(#oil)">
        <circle cx="175" cy="70" r="30" opacity=".16"/>
        <circle cx="220" cy="48" r="26" opacity=".14"/>
        <circle cx="150" cy="42" r="22" opacity=".12"/>
        <circle cx="205" cy="86" r="20" opacity=".13"/>
      </g>
      <!-- bóng đổ dưới bánh -->
      <ellipse cx="300" cy="312" rx="245" ry="16" fill="#1a0f04" opacity=".45" filter="url(#oil)"/>
      <g filter="url(#oil)">
        <!-- cản trước (cowcatcher) -->
        <path d="M26 306 L96 306 L96 252 Z" fill="url(#gDark)"/>
        <!-- bệ máy -->
        <rect x="92" y="242" width="372" height="14" rx="3" fill="#2c1c0c"/>
        <!-- nồi hơi -->
        <rect x="112" y="150" width="322" height="96" rx="47" fill="url(#gBoiler)"/>
        <circle cx="132" cy="198" r="50" fill="#4b3218"/>
        <circle cx="132" cy="198" r="50" fill="none" stroke="#caa24e" stroke-width="2.5" opacity=".55"/>
        <!-- vòng đai nồi hơi -->
        <path d="M235 152 v92 M320 152 v90" stroke="#2a1b0b" stroke-width="4" opacity=".5"/>
        <!-- ống khói -->
        <path d="M150 150 L192 150 L202 96 L140 96 Z" fill="url(#gDark)"/>
        <rect x="134" y="86" width="74" height="12" rx="3" fill="#3a2611"/>
        <!-- vòm hơi + vòm cát -->
        <ellipse cx="250" cy="150" rx="27" ry="21" fill="url(#gBoiler)"/>
        <ellipse cx="322" cy="151" rx="22" ry="17" fill="url(#gBoiler)"/>
        <!-- đèn pha -->
        <circle cx="120" cy="162" r="13" fill="#f6e6ba"/>
        <circle cx="120" cy="162" r="13" fill="none" stroke="#7c5323" stroke-width="2"/>
        <!-- ca-bin -->
        <rect x="404" y="108" width="150" height="16" rx="5" fill="#37240f"/>
        <rect x="420" y="120" width="122" height="126" rx="6" fill="url(#gBoiler)"/>
        <rect x="442" y="140" width="66" height="60" rx="9" fill="#efd9a2" opacity=".72"/>
        <rect x="442" y="140" width="66" height="60" rx="9" fill="none" stroke="#2c1b0a" stroke-width="3"/>
        <!-- thanh truyền -->
        <rect x="248" y="266" width="118" height="9" rx="4" fill="#caa24e" opacity=".8"/>
        <!-- bánh xe -->
        <g stroke="#caa24e" stroke-width="2.4">
          <circle cx="152" cy="282" r="26" fill="url(#gWheel)"/>
          <circle cx="252" cy="262" r="47" fill="url(#gWheel)"/>
          <circle cx="362" cy="262" r="47" fill="url(#gWheel)"/>
          <circle cx="480" cy="278" r="31" fill="url(#gWheel)"/>
        </g>
        <g stroke="#8a6329" stroke-width="2" opacity=".7">
          <path d="M252 215 v94 M205 262 h94 M219 229 l66 66 M285 229 l-66 66"/>
          <path d="M362 215 v94 M315 262 h94 M329 229 l66 66 M395 229 l-66 66"/>
        </g>
        <circle cx="252" cy="262" r="9" fill="#caa24e"/>
        <circle cx="362" cy="262" r="9" fill="#caa24e"/>
        <!-- vệt sáng cọ (rim light) -->
        <path d="M118 153 Q273 138 430 153" fill="none" stroke="#f3e4c2" stroke-width="3" opacity=".45"/>
        <path d="M140 96 L150 150" fill="none" stroke="#f3e4c2" stroke-width="2.5" opacity=".4"/>
        <path d="M420 126 h120" fill="none" stroke="#f3e4c2" stroke-width="2.5" opacity=".35"/>
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
      </div>
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
