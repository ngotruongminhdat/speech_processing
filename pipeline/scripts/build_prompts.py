#!/usr/bin/env python3
"""Thu sẵn lời nhắc của chế độ chạm đơn giản bằng giọng Hoài My (edge-tts), cùng giọng với sách.

Ứng dụng tự đọc lời nhắc khi người dùng không bật trình đọc màn hình. Giọng tiếng Việt có sẵn
trên máy thì nơi có nơi không (máy không có sẽ đọc chữ Việt bằng giọng tiếng Anh), nên mọi câu
được thu trước thành mp3. Danh sách câu do chính ứng dụng liệt kê (hàm promptList trong app.js,
tính từ danh mục sách), script này mở ứng dụng bằng trình duyệt không giao diện để lấy danh sách đó.

  prompts/index.json     { "câu": "tên file mp3" }
  prompts/<sha1>.mp3     mỗi câu một file; câu đã thu rồi thì không thu lại

build_site.py chép thư mục prompts/ vào site/. Chạy lại script này mỗi khi thêm sách hoặc sửa lời nhắc.

Usage: .venv/bin/python pipeline/scripts/build_prompts.py   (cần site/catalog.json: chạy build_site.py trước)
"""
import asyncio
import functools
import glob
import hashlib
import http.server
import json
import os
import shutil
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts_chapter_edge import fetch  # noqa: E402  (tải có thử lại và kiểm tra audio cụt, dùng chung với sách)
WEB, SITE, OUT = REPO / "app" / "web", REPO / "site", REPO / "prompts"
VOICE = "vi-VN-HoaiMyNeural"
PARALLEL = 3


def chromium_path():
    hits = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")))
    return hits[-1] if hits else None


async def list_sentences():
    """Mở app/web với danh mục của site/ rồi hỏi ứng dụng danh sách câu cần thu."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    catalog = (SITE / "catalog.json").read_text(encoding="utf-8")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(executable_path=chromium_path())
            ctx = await browser.new_context(service_workers="block")
            await ctx.route("**/catalog.json", lambda r: r.fulfill(status=200, content_type="application/json", body=catalog))
            page = await ctx.new_page()
            await page.goto(f"http://127.0.0.1:{srv.server_address[1]}/")
            await page.wait_for_selector("#bookList li")
            sentences = await page.evaluate("window.snPrompts()")
            await browser.close()
    finally:
        srv.shutdown()
    return sentences


async def synth(text, path, sem, count):
    async with sem:
        try:
            audio, _ = await fetch(text, VOICE)
            path.write_bytes(audio)
            ok = True
        except Exception as e:
            print(f"  ❌ {text!r}: {e}", flush=True)
            ok = False
        count[0] += 1
        if count[0] % 50 == 0:
            print(f"  … {count[0]} câu", flush=True)
        return ok


async def main():
    if not (SITE / "catalog.json").exists():
        sys.exit("Chưa có site/catalog.json. Hãy chạy pipeline/scripts/build_site.py trước.")
    sentences = await list_sentences()
    OUT.mkdir(exist_ok=True)
    index = {s: hashlib.sha1(f"{VOICE}|{s}".encode("utf-8")).hexdigest()[:16] + ".mp3" for s in sentences}
    todo = [(s, OUT / f) for s, f in index.items() if not (OUT / f).exists()]
    print(f"{len(index)} câu, cần thu {len(todo)} câu bằng {VOICE}", flush=True)
    sem = asyncio.Semaphore(PARALLEL)
    count = [0]
    done = await asyncio.gather(*(synth(s, f, sem, count) for s, f in todo))
    index = {s: f for s, f in index.items() if (OUT / f).exists()}          # câu thu hỏng thì ứng dụng tự dùng cách khác
    for old in OUT.glob("*.mp3"):
        if old.name not in index.values():
            old.unlink()
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if SITE.exists():
        shutil.rmtree(SITE / "prompts", ignore_errors=True)
        shutil.copytree(OUT, SITE / "prompts")
    size = sum(f.stat().st_size for f in OUT.glob("*.mp3"))
    print(f"✅ prompts/: {len(index)} câu, {size / 1e6:.1f} MB" + (f", {done.count(False)} câu thu hỏng" if False in done else ""))
    sys.exit(1 if False in done else 0)


if __name__ == "__main__":
    asyncio.run(main())
