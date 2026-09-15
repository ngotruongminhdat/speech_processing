#!/usr/bin/env python3
"""Tạo preview.html cho 1 chương — mô phỏng trải nghiệm đọc DAISY trong trình duyệt.

Giao diện kiểu app đọc sách (giống Thorium Reader):
  - Sidebar MỤC LỤC (như navigation.ncx), chương đã build bấm chuyển được
  - Audio đọc tới đoạn nào thì đoạn đó tô sáng (đồng bộ SMIL)
  - Bấm vào đoạn bất kỳ để nhảy audio; thanh tiến độ đọc trên đầu trang
  - Tự đổi giao diện sáng/tối theo hệ thống

Usage: python scripts/preview_html.py 1  -> build/chapter_NN/preview.html
"""
import argparse
import csv
import json
from pathlib import Path

from extract_chapter import unit_titles

ROOT = Path(__file__).resolve().parent.parent


def gen(chapter_no: int):
    ch = ROOT / "build" / f"chapter_{chapter_no:02d}"
    data = json.loads((ch / "segments.json").read_text(encoding="utf-8"))
    with open(ch / "timestamps.csv", encoding="utf-8") as f:
        clips = {r["id"]: r for r in csv.DictReader(f)}
    meta = json.loads((ROOT / "metadata" / "book_meta.json").read_text(encoding="utf-8"))
    mp3 = f"chuong{chapter_no:02d}.mp3"
    total_s = max(float(c["clipEnd"]) for c in clips.values())
    mins, secs = divmod(int(total_s), 60)

    units = [(no, title) for no, _label, title in unit_titles()]
    last_no = units[-1][0]
    toc_items = []
    for i, title in units:
        num = "★" if i == 0 else ("✦" if i == last_no else f"{i:02d}")
        built = (ROOT / "build" / f"chapter_{i:02d}" / "preview.html").exists() or i == chapter_no
        if i == chapter_no:
            toc_items.append(f'<li class="current"><span><em>{num}</em>{title}</span></li>')
        elif built:
            toc_items.append(f'<li><a href="../chapter_{i:02d}/preview.html?autoplay=1"><em>{num}</em>{title}</a></li>')
        else:
            toc_items.append(f'<li class="missing"><span><em>{num}</em>{title}</span></li>')

    paras = []
    first_h1_seen = False
    dropcap_next = True
    for seg in data["segments"]:
        c = clips[seg["id"]]
        if seg["type"] == "h1":
            if not first_h1_seen:
                first_h1_seen = True  # tiêu đề đầu đã hiển thị to ở header chương
                continue
            # các mục con tiếp theo (Phần mở đầu có nhiều mục)
            paras.append(
                f'<h2 class="seg section" data-b="{c["clipBegin"]}" data-e="{c["clipEnd"]}">{seg["text"]}</h2>'
            )
            dropcap_next = True
            continue
        if seg["type"] == "note":
            paras.append(
                f'<p class="seg footnote" id="note_{seg["note_no"]}" data-b="{c["clipBegin"]}"'
                f' data-e="{c["clipEnd"]}">{seg["text"]}</p>'
            )
            continue
        cls = "seg dropcap" if dropcap_next else "seg"
        body_txt = seg["text"]
        for k in seg.get("noterefs", []):
            body_txt += f' <sup class="noteref"><a href="#note_{k}">[{k}]</a></sup>'
        paras.append(f'<p class="{cls}" data-b="{c["clipBegin"]}" data-e="{c["clipEnd"]}">{body_txt}</p>')
        dropcap_next = False
    h1_clip = clips["id_1"]
    header_label = data.get("label") or ("Mở đầu" if chapter_no == 0 else f"Chương {chapter_no}")

    # chương kế tiếp / liền trước đã build (tính tại thời điểm sinh trang)
    next_href, next_title = "", ""
    for j, t in units:
        if j > chapter_no and (ROOT / "build" / f"chapter_{j:02d}" / "preview.html").exists():
            next_href = f"../chapter_{j:02d}/preview.html?autoplay=1"
            next_title = t
            break
    prev_href = ""
    for j, t in reversed(units):
        if j < chapter_no and (ROOT / "build" / f"chapter_{j:02d}" / "preview.html").exists():
            prev_href = f"../chapter_{j:02d}/preview.html?autoplay=1"
            break

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta['title']} — {header_label}: {data['title']}</title>
<style>
  :root {{
    --paper: #faf6ee; --paper-2: #f2ecdd; --ink: #2c2417; --ink-soft: #7d7259;
    --accent: #b8860b; --accent-soft: #f5e5b8; --hi: #ffedad; --hi-ring: #e5c25b;
    --card: #fffdf8; --line: #e3d9c2; --shadow: 0 10px 30px rgba(90, 70, 20, .12);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --paper: #191613; --paper-2: #141210; --ink: #e8e0cf; --ink-soft: #9a8f77;
      --accent: #d4a531; --accent-soft: #3a2f14; --hi: #4a3a10; --hi-ring: #8a6d1d;
      --card: #211d18; --line: #38321f; --shadow: 0 10px 30px rgba(0, 0, 0, .5);
    }}
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    margin: 0; display: flex; background: var(--paper); color: var(--ink);
    font-family: Georgia, 'Times New Roman', serif;
  }}
  /* ---- thanh tiến độ đọc ---- */
  #progress {{ position: fixed; top: 0; left: 0; height: 3px; width: 0;
    background: linear-gradient(90deg, var(--accent), #e0b64f); z-index: 20; transition: width .3s linear; }}

  /* ---- sidebar mục lục ---- */
  nav {{
    width: 300px; min-width: 240px; height: 100vh; position: sticky; top: 0; overflow-y: auto;
    background: var(--paper-2); border-right: 1px solid var(--line); padding: 1.6rem 1rem 7rem;
  }}
  nav .brand {{ padding: 0 .4rem 1rem; border-bottom: 1px solid var(--line); margin-bottom: 1rem; }}
  nav .brand b {{ display: block; font-size: 1.02rem; line-height: 1.35; }}
  nav .brand i {{ color: var(--ink-soft); font-size: .84rem; }}
  nav h2 {{ font-size: .72rem; letter-spacing: .18em; text-transform: uppercase;
    color: var(--ink-soft); margin: 0 0 .5rem .4rem; font-family: system-ui, sans-serif; }}
  nav ol {{ list-style: none; margin: 0; padding: 0; font-size: .88rem; }}
  nav li a, nav li span {{
    display: flex; gap: .55rem; align-items: baseline; padding: .34rem .55rem;
    border-radius: 8px; text-decoration: none; color: var(--ink); line-height: 1.4;
  }}
  nav li em {{ font-style: normal; font-family: system-ui, sans-serif; font-size: .7rem;
    color: var(--ink-soft); min-width: 1.4em; }}
  nav li a:hover {{ background: var(--accent-soft); }}
  nav li.current > span {{ background: var(--accent); color: #fff8e6; font-weight: bold;
    box-shadow: var(--shadow); }}
  nav li.current em {{ color: #fff3cf; }}
  nav li.missing {{ opacity: .38; }}

  /* ---- trang sách ---- */
  main {{ flex: 1; display: flex; justify-content: center; padding: 2.2rem 1.2rem 9rem; }}
  .page {{
    max-width: 700px; width: 100%; background: var(--card); border: 1px solid var(--line);
    border-radius: 14px; box-shadow: var(--shadow); padding: 3rem clamp(1.4rem, 5vw, 3.4rem) 3.4rem;
  }}
  .kicker {{ font-family: system-ui, sans-serif; font-size: .72rem; letter-spacing: .22em;
    text-transform: uppercase; color: var(--accent); text-align: center; }}
  h1.chapter {{ text-align: center; font-size: 2rem; margin: .4rem 0 .2rem; font-weight: normal;
    cursor: pointer; }}
  h1.chapter:hover {{ color: var(--accent); }}
  .byline {{ text-align: center; color: var(--ink-soft); font-size: .88rem; font-style: italic; }}
  .flourish {{ display: flex; align-items: center; gap: .9rem; margin: 1.4rem auto 2rem;
    max-width: 420px; color: var(--accent); }}
  .flourish::before, .flourish::after {{ content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent)); }}
  .flourish::after {{ background: linear-gradient(90deg, var(--accent), transparent); }}
  .flourish i {{ font-style: normal; font-size: .95rem; transform: rotate(45deg); line-height: 1; }}
  .seg {{ font-size: 1.05rem; line-height: 1.95; margin: 0 0 1.05em; padding: .1rem .45rem;
    border-radius: 8px; cursor: pointer; transition: background .25s, box-shadow .25s; }}
  .seg:hover {{ background: var(--accent-soft); }}
  .seg.active {{ background: var(--hi); box-shadow: 0 0 0 2px var(--hi-ring); }}
  .dropcap::first-letter {{ float: left; font-size: 3.4em; line-height: .82; padding: .04em .12em 0 0;
    color: var(--accent); font-weight: bold; }}
  .endmark {{ text-align: center; color: var(--ink-soft); margin-top: 2.2rem; font-size: 1.1rem; }}
  .footnote {{ font-size: .88rem; color: var(--ink-soft); border-left: 3px solid var(--accent);
    background: var(--accent-soft); margin-top: 2rem; }}
  sup.noteref a {{ color: var(--accent); text-decoration: none; font-weight: bold; }}

  /* ---- thanh audio ---- */
  footer {{
    position: fixed; bottom: 1.1rem; left: 0; right: 0; display: flex; justify-content: center;
    pointer-events: none; z-index: 10;
  }}
  .player-card {{
    pointer-events: auto; display: flex; align-items: center; gap: .9rem;
    background: var(--card); border: 1px solid var(--line); border-radius: 999px;
    box-shadow: var(--shadow); padding: .55rem 1.1rem .55rem .8rem; max-width: 94vw;
  }}
  .player-card .info {{ font-family: system-ui, sans-serif; font-size: .74rem; color: var(--ink-soft);
    white-space: nowrap; line-height: 1.35; }}
  .player-card .info b {{ color: var(--ink); font-size: .8rem; }}
  audio {{ width: min(360px, 46vw); height: 38px; }}
  .pbtn {{ pointer-events: auto; cursor: pointer; font-family: system-ui, sans-serif;
    font-size: .74rem; font-weight: 600; color: var(--ink); background: var(--card);
    border: 1px solid var(--line); border-radius: 999px; padding: .42rem .7rem;
    text-decoration: none; white-space: nowrap; transition: background .18s ease; }}
  .pbtn:hover {{ background: var(--accent-soft); }}
  #speed {{ min-width: 3.1em; text-align: center; }}
  @media (max-width: 940px) {{ nav {{ display: none; }} }}

  /* ---- gợi ý phím tắt ---- */
  .keyhint {{ position: fixed; bottom: 1.15rem; left: 1.1rem; z-index: 9;
    font-family: system-ui, sans-serif; font-size: .68rem; color: var(--ink-soft);
    background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: .5rem .7rem; box-shadow: var(--shadow); max-width: 210px; line-height: 1.7; }}
  .keyhint b {{ color: var(--ink); background: var(--paper-2); border: 1px solid var(--line);
    border-radius: 4px; padding: 0 .32em; font-family: ui-monospace, monospace; font-size: .92em; }}
  @media (max-width: 940px) {{ .keyhint {{ display: none; }} }}

  /* ---- nút về trang bìa ---- */
  .home-btn {{ position: fixed; top: .9rem; right: .9rem; z-index: 15;
    display: inline-flex; align-items: center; gap: .45rem; text-decoration: none;
    font-family: system-ui, sans-serif; font-size: .8rem; font-weight: 600;
    color: var(--ink); background: var(--card); border: 1px solid var(--line);
    border-radius: 999px; padding: .5rem 1rem; box-shadow: var(--shadow);
    transition: transform .18s ease, background .18s ease; }}
  .home-btn:hover {{ transform: translateY(-2px); background: var(--accent-soft); }}

  /* ---- nút + bảng cài đặt đọc ---- */
  .set-btn {{ position: fixed; top: .9rem; right: 9.2rem; z-index: 15;
    display: inline-flex; align-items: center; gap: .4rem; cursor: pointer;
    font-family: system-ui, sans-serif; font-size: .8rem; font-weight: 600;
    color: var(--ink); background: var(--card); border: 1px solid var(--line);
    border-radius: 999px; padding: .5rem 1rem; box-shadow: var(--shadow);
    transition: transform .18s ease, background .18s ease; }}
  .set-btn:hover {{ transform: translateY(-2px); background: var(--accent-soft); }}
  .set-panel {{ position: fixed; top: 3.4rem; right: .9rem; z-index: 16; width: 270px;
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    box-shadow: var(--shadow); padding: 1rem 1.1rem 1.15rem;
    font-family: system-ui, sans-serif; display: none; }}
  .set-panel.open {{ display: block; }}
  .set-panel h3 {{ font-size: .68rem; letter-spacing: .14em; text-transform: uppercase;
    color: var(--ink-soft); margin: .9rem 0 .45rem; }}
  .set-panel h3:first-child {{ margin-top: 0; }}
  .set-row {{ display: flex; gap: .4rem; flex-wrap: wrap; }}
  .set-row button {{ flex: 1; min-width: 3rem; cursor: pointer; font-family: inherit;
    font-size: .8rem; color: var(--ink); background: var(--paper-2);
    border: 1px solid var(--line); border-radius: 8px; padding: .42rem .3rem;
    transition: background .15s ease; }}
  .set-row button:hover {{ background: var(--accent-soft); }}
  .set-row button[aria-pressed="true"] {{ background: var(--accent); color: #fff8e6;
    border-color: var(--accent); }}

  /* cỡ chữ đọc */
  .page {{ --rsize: 1; }}
  .seg {{ font-size: calc(1.05rem * var(--rsize)); }}
  h1.chapter {{ font-size: calc(2rem * var(--rsize)); }}
  /* chế độ font dễ đọc */
  body.legible .seg {{ font-family: system-ui, "Segoe UI", sans-serif;
    letter-spacing: .02em; word-spacing: .14em; line-height: 2.15; text-align: left; }}
  body.legible .dropcap::first-letter {{ float: none; font-size: 1em; color: inherit;
    padding: 0; font-weight: inherit; }}

  /* chủ đề tương phản */
  :root.theme-dark {{ --paper: #191613; --paper-2: #141210; --ink: #e8e0cf; --ink-soft: #9a8f77;
    --accent: #d4a531; --accent-soft: #3a2f14; --hi: #4a3a10; --hi-ring: #8a6d1d;
    --card: #211d18; --line: #38321f; --shadow: 0 10px 30px rgba(0,0,0,.5); }}
  :root.theme-paper {{ --paper: #faf6ee; --paper-2: #f2ecdd; --ink: #2c2417; --ink-soft: #7d7259;
    --accent: #b8860b; --accent-soft: #f5e5b8; --hi: #ffedad; --hi-ring: #e5c25b;
    --card: #fffdf8; --line: #e3d9c2; --shadow: 0 10px 30px rgba(90,70,20,.12); }}
  :root.theme-contrast {{ --paper: #000; --paper-2: #111; --ink: #ffe100; --ink-soft: #d9c200;
    --accent: #ffe100; --accent-soft: #333; --hi: #ffe100; --hi-ring: #fff;
    --card: #0a0a0a; --line: #ffe100; --shadow: none; }}
  :root.theme-contrast .seg.active {{ color: #000; }}

  .sleep-info {{ font-size: .72rem; color: var(--ink-soft); margin-top: .5rem; }}
</style>
</head>
<body>
<div id="progress"></div>
<a class="home-btn" href="../index.html" title="Về trang bìa">📖 Trang bìa</a>
<button class="set-btn" id="setBtn" aria-expanded="false" title="Cài đặt đọc">⚙ Cài đặt</button>
<div class="set-panel" id="setPanel" role="dialog" aria-label="Cài đặt đọc">
  <h3>Cỡ chữ</h3>
  <div class="set-row" id="sizeRow">
    <button data-size="0.9">A−</button>
    <button data-size="1" aria-pressed="true">A</button>
    <button data-size="1.2">A+</button>
    <button data-size="1.45">A++</button>
  </div>
  <h3>Nền &amp; tương phản</h3>
  <div class="set-row" id="themeRow">
    <button data-theme="paper" aria-pressed="true">Giấy</button>
    <button data-theme="dark">Tối</button>
    <button data-theme="contrast">Tương phản cao</button>
  </div>
  <h3>Kiểu chữ</h3>
  <div class="set-row" id="legRow">
    <button data-leg="0" aria-pressed="true">Mặc định</button>
    <button data-leg="1">Dễ đọc</button>
  </div>
  <h3>Hẹn giờ tắt</h3>
  <div class="set-row" id="sleepRow">
    <button data-sleep="0" aria-pressed="true">Tắt</button>
    <button data-sleep="15">15′</button>
    <button data-sleep="30">30′</button>
    <button data-sleep="60">60′</button>
  </div>
  <div class="sleep-info" id="sleepInfo"></div>
</div>
<nav>
  <div class="brand">
    <a href="../index.html" style="text-decoration:none;color:inherit">
      <b>{meta['title']}</b>
      <i>{meta['creator']}</i>
    </a>
  </div>
  <h2>Mục lục</h2>
  <ol>
{chr(10).join('    ' + li for li in toc_items)}
  </ol>
</nav>
<main>
  <article class="page">
    <div class="kicker">{header_label}</div>
    <h1 class="chapter seg" data-b="{h1_clip['clipBegin']}" data-e="{h1_clip['clipEnd']}">{data['title']}</h1>
    <div class="byline">{meta['title']} · {meta['creator']}</div>
    <div class="flourish"><i>◆</i></div>
{chr(10).join('    ' + p for p in paras)}
    <div class="endmark">✦ &nbsp; Hết {header_label.lower()} &nbsp; ✦</div>
  </article>
</main>
<footer>
  <div class="player-card">
    <div class="info"><b>{header_label}: {data['title']}</b><br>{mins}:{secs:02d} · bấm đoạn văn để nhảy tới</div>
    <audio id="player" src="{mp3}" controls preload="auto"></audio>
    <select class="pbtn" id="speed" title="Tốc độ đọc (phím ↑ / ↓)">
      <option value="0.5">0.5×</option>
      <option value="0.75">0.75×</option>
      <option value="1" selected>1×</option>
      <option value="1.25">1.25×</option>
      <option value="1.5">1.5×</option>
      <option value="2">2×</option>
    </select>
    <a class="pbtn" id="dl" href="daisy.zip" download="{meta['title']} - {header_label}.zip" title="Tải bản DAISY (.zip) mở bằng Thorium / EasyReader">⬇ DAISY</a>
  </div>
</footer>
<div class="keyhint">
  <b>Space</b> phát/dừng · <b>←</b><b>→</b> đoạn · <b>↑</b><b>↓</b> tốc độ<br>
  <b>Shift</b>+<b>→</b> phần sau · <b>Shift</b>+<b>←</b> phần trước
</div>
<script>
  const CH = {chapter_no};
  const player = document.getElementById('player');
  const bar = document.getElementById('progress');
  const segs = [...document.querySelectorAll('.seg')];
  const NEXT_HREF = "{next_href}";
  const NEXT_TITLE = "{next_title}";
  const PREV_HREF = "{prev_href}";
  const POS_KEY = 'ttc-pos-' + CH;
  const DONE_KEY = 'ttc-done';

  function getDone() {{ try {{ return JSON.parse(localStorage.getItem(DONE_KEY)) || []; }} catch (e) {{ return []; }} }}
  function markDone() {{ const d = getDone(); if (!d.includes(CH)) {{ d.push(CH); localStorage.setItem(DONE_KEY, JSON.stringify(d)); }} }}

  segs.forEach(el => el.addEventListener('click', () => {{
    player.currentTime = parseFloat(el.dataset.b) + 0.01;
    player.play();
  }}));

  // đoạn đang đọc hiện tại (dùng cho phím ← →)
  let curIdx = -1;
  player.addEventListener('timeupdate', () => {{
    const t = player.currentTime;
    if (player.duration) bar.style.width = (t / player.duration * 100) + '%';
    segs.forEach((el, i) => {{
      const on = t >= parseFloat(el.dataset.b) && t < parseFloat(el.dataset.e);
      if (on) curIdx = i;
      el.classList.toggle('active', on);
      if (on && el.dataset.scrolled !== el.dataset.b) {{
        el.dataset.scrolled = el.dataset.b;
        el.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
      }}
    }});
    // lưu vị trí đang nghe (resume) — mỗi ~3s
    if (Math.floor(t) % 3 === 0) {{ localStorage.setItem(POS_KEY, t); localStorage.setItem('ttc-last', CH); }}
  }});

  function jumpSeg(delta) {{
    let i = Math.min(Math.max(curIdx + delta, 0), segs.length - 1);
    player.currentTime = parseFloat(segs[i].dataset.b) + 0.01;
    player.play();
  }}

  // ---- tốc độ đọc ----
  const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
  const speedSel = document.getElementById('speed');
  let si = 2;
  const savedRate = parseFloat(localStorage.getItem('ttc-rate'));
  if (savedRate && speeds.includes(savedRate)) si = speeds.indexOf(savedRate);
  function applyRate() {{ player.playbackRate = speeds[si]; speedSel.value = String(speeds[si]); localStorage.setItem('ttc-rate', speeds[si]); }}
  applyRate();
  speedSel.addEventListener('change', () => {{ si = speeds.indexOf(parseFloat(speedSel.value)); applyRate(); }});

  // ---- resume: khôi phục vị trí đang nghe ----
  const savedPos = parseFloat(localStorage.getItem(POS_KEY));
  player.addEventListener('loadedmetadata', () => {{
    if (savedPos > 1 && savedPos < player.duration - 2) player.currentTime = savedPos;
  }});

  // nghe hết -> đánh dấu đã xong + tự chuyển phần kế tiếp
  player.addEventListener('ended', () => {{
    markDone();
    localStorage.removeItem(POS_KEY);
    if (!NEXT_HREF) return;
    const toast = document.createElement('div');
    toast.textContent = '▶ Tiếp theo: ' + NEXT_TITLE + ' …';
    toast.style.cssText = 'position:fixed;bottom:5.2rem;left:50%;transform:translateX(-50%);' +
      'background:var(--accent);color:#fff8e6;font-family:system-ui,sans-serif;font-size:.85rem;' +
      'padding:.6rem 1.3rem;border-radius:999px;box-shadow:var(--shadow);z-index:30';
    document.body.appendChild(toast);
    setTimeout(() => {{ location.href = NEXT_HREF; }}, 2000);
  }});

  // ---- phím tắt ---- (dùng pha capture để không bị thanh audio nuốt phím)
  document.addEventListener('keydown', (e) => {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    const next = () => {{ if (NEXT_HREF) location.href = NEXT_HREF; }};
    const prev = () => {{ if (PREV_HREF) location.href = PREV_HREF; }};
    switch (e.key) {{
      case ' ': case 'k': e.preventDefault(); player.paused ? player.play() : player.pause(); break;
      case 'ArrowRight': e.preventDefault(); e.shiftKey ? next() : jumpSeg(1); break;
      case 'ArrowLeft': e.preventDefault(); e.shiftKey ? prev() : jumpSeg(-1); break;
      case 'ArrowUp': e.preventDefault(); si = Math.min(si + 1, speeds.length - 1); applyRate(); break;
      case 'ArrowDown': e.preventDefault(); si = Math.max(si - 1, 0); applyRate(); break;
      case ']': e.preventDefault(); next(); break;
      case '[': e.preventDefault(); prev(); break;
    }}
  }}, true);

  // ---- bảng cài đặt đọc ----
  const setBtn = document.getElementById('setBtn');
  const setPanel = document.getElementById('setPanel');
  setBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    const open = setPanel.classList.toggle('open');
    setBtn.setAttribute('aria-expanded', open);
  }});
  document.addEventListener('click', (e) => {{
    if (!setPanel.contains(e.target) && e.target !== setBtn) setPanel.classList.remove('open');
  }});
  function press(row, el) {{ row.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', b === el)); }}

  // cỡ chữ
  const sizeRow = document.getElementById('sizeRow');
  const page = document.querySelector('.page');
  function applySize(v, el) {{ page.style.setProperty('--rsize', v); localStorage.setItem('ttc-size', v); if (el) press(sizeRow, el); }}
  sizeRow.querySelectorAll('button').forEach(b => b.addEventListener('click', () => applySize(b.dataset.size, b)));
  const savedSize = localStorage.getItem('ttc-size');
  if (savedSize) applySize(savedSize, [...sizeRow.children].find(b => b.dataset.size === savedSize));

  // chủ đề
  const themeRow = document.getElementById('themeRow');
  function applyTheme(t, el) {{
    document.documentElement.classList.remove('theme-paper', 'theme-dark', 'theme-contrast');
    document.documentElement.classList.add('theme-' + t);
    localStorage.setItem('ttc-theme', t); if (el) press(themeRow, el);
  }}
  themeRow.querySelectorAll('button').forEach(b => b.addEventListener('click', () => applyTheme(b.dataset.theme, b)));
  const savedTheme = localStorage.getItem('ttc-theme');
  if (savedTheme) applyTheme(savedTheme, [...themeRow.children].find(b => b.dataset.theme === savedTheme));
  else themeRow.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', 'false'));

  // font dễ đọc
  const legRow = document.getElementById('legRow');
  function applyLeg(v, el) {{ document.body.classList.toggle('legible', v === '1'); localStorage.setItem('ttc-leg', v); if (el) press(legRow, el); }}
  legRow.querySelectorAll('button').forEach(b => b.addEventListener('click', () => applyLeg(b.dataset.leg, b)));
  const savedLeg = localStorage.getItem('ttc-leg');
  if (savedLeg) applyLeg(savedLeg, [...legRow.children].find(b => b.dataset.leg === savedLeg));

  // hẹn giờ tắt (không lưu qua lần tải)
  const sleepRow = document.getElementById('sleepRow');
  const sleepInfo = document.getElementById('sleepInfo');
  let sleepTimer = null, sleepAt = 0, sleepTick = null;
  function applySleep(min, el) {{
    if (sleepTimer) clearTimeout(sleepTimer);
    if (sleepTick) clearInterval(sleepTick);
    press(sleepRow, el);
    if (min === '0') {{ sleepInfo.textContent = ''; return; }}
    sleepAt = Date.now() + min * 60000;
    sleepTimer = setTimeout(() => {{ player.pause(); sleepInfo.textContent = '⏸ Đã tắt theo hẹn giờ.'; }}, min * 60000);
    const upd = () => {{ const s = Math.max(0, Math.round((sleepAt - Date.now()) / 1000));
      sleepInfo.textContent = '⏱ Còn ' + Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }};
    upd(); sleepTick = setInterval(upd, 1000);
  }}
  sleepRow.querySelectorAll('button').forEach(b => b.addEventListener('click', () => applySleep(b.dataset.sleep, b)));

  // autoplay khi đến từ trang bìa (?autoplay=1): chờ 1s rồi tự phát
  if (new URLSearchParams(location.search).get('autoplay') === '1') {{
    setTimeout(() => {{
      player.play().catch(() => {{
        document.querySelector('.player-card').animate(
          [{{ boxShadow: '0 0 0 0 rgba(184,134,11,.65)' }},
           {{ boxShadow: '0 0 0 14px rgba(184,134,11,0)' }}],
          {{ duration: 900, iterations: 4 }});
      }});
    }}, 1000);
  }}
</script>
</body>
</html>
"""
    out = ch / "preview.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    gen(ap.parse_args().chapter)
