#!/usr/bin/env python3
"""Kiểm thử đầu-cuối của Sách Nói bằng Chromium không giao diện (Playwright).

Chạy trên bản đã lắp trong site/ và đang được phục vụ qua HTTP:
  python3 pipeline/scripts/build_site.py
  python3 app/tests/serve.py 8931 &          # máy chủ có hỗ trợ Range, cần để tua audio
  .venv/bin/python app/tests/e2e.py http://127.0.0.1:8931/
"""
import asyncio
import glob
import json
import os
import sys

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8931/"
SLUG = "lao-hac"
results = []


async def spoken_live(page, want, timeout=3000):
    """Nội dung vùng thông báo, sau khi chờ câu mong đợi xuất hiện (vùng này được xoá rồi ghi lại sau 60 ms)."""
    try:
        await page.wait_for_function("w => document.querySelector('#live').textContent.includes(w)", arg=want, timeout=timeout)
    except Exception:
        pass
    return await page.inner_text("#live")


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("  ✅ " if cond else "  ❌ ") + name + (f"  [{detail}]" if detail else ""))


def chromium_path():
    hits = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")))
    return hits[-1] if hits else None


async def slow_route(route):
    """Làm chậm việc tải, để kịp thấy trạng thái đang lưu."""
    await asyncio.sleep(0.15)
    await route.continue_()


AUDIO = "document.querySelector('#audio')"
STATE = f"""(() => {{ const a = {AUDIO}; const on = document.querySelector('.s.on');
  return {{ t: a.currentTime, paused: a.paused, rate: a.playbackRate, dur: a.duration, src: a.currentSrc,
           on: on ? Number(on.dataset.i) : -1, nOn: document.querySelectorAll('.s.on').length,
           n: document.querySelectorAll('.s').length }}; }})()"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chromium_path(),
                                          args=["--autoplay-policy=no-user-gesture-required",
                                                # đầu ra âm thanh giả: không phát ra loa, và đồng hồ phát không
                                                # bị khựng khi thiết bị âm thanh thật của máy đang bận
                                                "--disable-audio-output",
                                                # micro giả, để thử ghi âm ghi chú cho dấu trang
                                                "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"])
        ctx = await browser.new_context(viewport={"width": 390, "height": 844}, locale="vi-VN",
                                        service_workers="block", permissions=["microphone"])
        # Nhận dạng giọng nói giả: "nghe" được đúng một câu rồi dừng, để thử nút tìm bằng giọng nói.
        await ctx.add_init_script("""window.webkitSpeechRecognition = window.SpeechRecognition = class {
          start() { setTimeout(() => { this.onstart && this.onstart();
            setTimeout(() => { this.onresult && this.onresult({ results: [[{ transcript: 'Thạch Lam.' }]] }); this.onend && this.onend(); }, 150); }, 20); }
          abort() { this.onend && this.onend(); } };""")
        if "127.0.0.1" in BASE:
            # bìa cuốn giữa kỳ chỉ có trên trang đã deploy (thư mục build/), bản lắp cục bộ không có
            await ctx.route("**/build/cover.jpg", lambda r: r.fulfill(status=200, content_type="image/jpeg", body=b""))
        page = await ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append("PAGEERROR " + str(e)))
        page.on("response", lambda r: errors.append(f"HTTP {r.status} {r.url}") if r.status >= 400 else None)

        print("Thư viện")
        await page.goto(BASE, wait_until="networkidle")
        n_books = await page.locator("#bookList li").count()
        check("kệ sách có từ 5 cuốn trở lên", n_books >= 5, f"{n_books} cuốn")
        check("trang khai báo tiếng Việt", await page.evaluate("document.documentElement.lang") == "vi")
        labels = await page.locator("#bookList a").evaluate_all("els => els.map(e => e.getAttribute('aria-label'))")
        check("mỗi cuốn có nhãn đọc được: tên, tác giả, thời lượng",
              all(l and "phút" in l for l in labels), labels[0])
        await page.fill("#q", "thach lam")
        await page.wait_for_timeout(200)
        n = await page.locator("#bookList li").count()
        check("tìm không dấu 'thach lam' ra đúng sách Thạch Lam", 1 <= n < n_books, f"{n} cuốn")
        check("kết quả tìm được thông báo cho trình đọc màn hình",
              "cuốn khớp" in await page.inner_text("#live"), await page.inner_text("#live"))
        await page.fill("#q", "zzzz")
        await page.wait_for_timeout(200)
        check("tìm không ra thì báo rõ", await page.locator("#noResult").is_visible())
        await page.fill("#q", "")

        print("Trang bìa")
        await page.click(f'#bookList a[href="#/b/{SLUG}"]')
        await page.wait_for_selector("#h-book")
        check("mở trang bìa, tiêu đề đúng", await page.inner_text("#h-book") == "Lão Hạc")
        await page.wait_for_timeout(150)
        check("focus chuyển vào tiêu đề màn hình mới",
              await page.evaluate("document.activeElement && document.activeElement.id") == "h-book")
        check("có bảng thông tin và nút tải DAISY",
              await page.locator(".metas div").count() >= 6 and await page.locator('.cta a[href*="-daisy-"]').count() == 1)

        print("Trang đọc và đồng bộ câu")
        await page.click("#bookHero .btn.primary")
        await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentTime > 1.6", timeout=20000)
        s = await page.evaluate(STATE)
        check("chạm Bắt đầu nghe là phát ngay", not s["paused"], f"t={s['t']:.2f}s")
        check("văn bản tách theo câu", s["n"] > 200, f"{s['n']} câu")
        check("đúng một câu được tô sáng", s["nOn"] == 1, f"câu số {s['on']}")
        check("nút phát đổi nhãn thành Tạm dừng", await page.get_attribute("#play", "aria-label") == "Tạm dừng")

        # dữ liệu mốc câu của đúng giọng đang phát (đường dẫn audio và dữ liệu chỉ khác đuôi file)
        sents = await page.evaluate(f"fetch({AUDIO}.currentSrc.replace(/\\.mp3$/, '.json')).then(r=>r.json()).then(d=>d.paras.flatMap(p=>p.s.map(x=>[x[0],x[1]])))")
        # mốc câu trong dữ liệu khớp với câu đang tô sáng tại nhiều thời điểm
        ok, tried = 0, 0
        for target in (10.0, 95.5, 300.2, 611.0, 880.0):
            await page.evaluate(f"{AUDIO}.currentTime = {target}")
            await page.wait_for_timeout(350)
            s = await page.evaluate(STATE)
            # data-i đếm trên toàn bộ câu của phần, kể cả câu tiêu đề (số 0) hiển thị ở đầu trang
            i = s["on"]
            tried += 1
            ok += 1 if (i > 0 and sents[i][0] - 0.05 <= s["t"] < (sents[i + 1][0] if i + 1 < len(sents) else 1e9)) else 0
        check("câu tô sáng khớp mốc thời gian ở 5 vị trí thử", ok == tried, f"{ok}/{tried}")

        # Thử ở giữa hai câu dài liền nhau, để lúc đọc trạng thái không rơi đúng ranh giới câu
        # (mốc câu khác nhau theo giọng, một mốc thời gian cố định có thể nằm sát ranh giới).
        k = next(i for i in range(5, len(sents) - 2)
                 if sents[i][1] - sents[i][0] > 4 and sents[i + 1][1] - sents[i + 1][0] > 4.5)
        await page.evaluate(f"{AUDIO}.currentTime = {sents[k][0] + 0.8:.2f}")
        await page.wait_for_timeout(300)
        before = await page.evaluate(STATE)
        await page.click("#next")
        await page.wait_for_timeout(300)
        after = await page.evaluate(STATE)
        check("nút Câu sau nhảy đúng một câu", after["on"] == before["on"] + 1, f"{before['on']} -> {after['on']}")
        await page.wait_for_timeout(1800)          # nghe quá 1,5 giây
        mid = await page.evaluate(STATE)
        await page.click("#prev")
        await page.wait_for_timeout(250)
        back = await page.evaluate(STATE)
        check("Câu trước sau khi nghe quá 1,5 giây thì quay về đầu câu đang nghe",
              back["on"] == mid["on"] and back["t"] < mid["t"], f"t {mid['t']:.1f} -> {back['t']:.1f}")
        await page.click("#prev")
        await page.wait_for_timeout(250)
        back2 = await page.evaluate(STATE)
        check("nhấn Câu trước lần nữa thì lùi một câu", back2["on"] == back["on"] - 1)

        await page.locator(".s").nth(40).scroll_into_view_if_needed()
        await page.locator(".s").nth(40).click()
        await page.wait_for_timeout(300)
        s = await page.evaluate(STATE)
        # phần tử .s thứ 40 trong DOM là câu số 41 (câu số 0 là tiêu đề)
        check("chạm vào một câu thì nghe từ câu đó", s["on"] == 41 and abs(s["t"] - sents[41][0]) < 0.6,
              f"câu {s['on']}, t={s['t']:.2f}")

        print("Tốc độ, bàn phím, cài đặt")
        await page.select_option("#speed", "1.5")
        await page.wait_for_timeout(200)
        s = await page.evaluate(STATE)
        check("đổi tốc độ 1,5 lần", s["rate"] == 1.5)
        check("tốc độ được thông báo bằng lời", "1 phẩy 5" in await page.inner_text("#live"))
        await page.locator("#h-reader").focus()
        await page.keyboard.press("Space")
        await page.wait_for_timeout(200)
        check("phím cách tạm dừng", (await page.evaluate(STATE))["paused"])
        b = (await page.evaluate(STATE))["on"]
        await page.keyboard.press("ArrowRight")
        await page.wait_for_timeout(200)
        check("mũi tên phải sang câu sau", (await page.evaluate(STATE))["on"] == b + 1)
        await page.keyboard.press("ArrowDown")
        check("mũi tên xuống giảm tốc độ", (await page.evaluate(STATE))["rate"] == 1.25)

        await page.click("#openSettings")
        check("hộp cài đặt mở dạng hộp thoại", await page.evaluate("document.querySelector('#settings').open"))
        await page.click('#optTheme button[data-v="contrast"]')
        await page.click('#optSize button[data-v="1.45"]')
        check("đổi nền tương phản cao",
              await page.evaluate("document.documentElement.classList.contains('theme-contrast')"))
        check("đổi cỡ chữ rất lớn",
              await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--rsize').trim()") == "1.45")
        await page.keyboard.press("Escape")
        check("phím Escape đóng hộp cài đặt", not await page.evaluate("document.querySelector('#settings').open"))
        overflow = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check("không tràn ngang trên màn hình 390px với chữ rất lớn", overflow <= 1, f"tràn {overflow}px")
        card = await page.locator(".player-card").bounding_box()
        kids = await page.evaluate("""() => Math.max(...[...document.querySelectorAll('.player-card *')]
          .filter(e => e.offsetParent !== null).map(e => e.getBoundingClientRect().right))""")
        check("thanh phát nằm gọn trong màn hình 390px", card["x"] >= 0 and card["x"] + card["width"] <= 390.5 and kids <= 390.5,
              f"mép phải thẻ {card['x'] + card['width']:.0f}px, phần tử xa nhất {kids:.0f}px")
        box = await page.locator("#play").bounding_box()
        await page.set_viewport_size({"width": 320, "height": 640})
        await page.wait_for_timeout(200)
        sizes = await page.evaluate("""() => ['#prev', '#play', '#next', '#step', '#speed', '#where', '#mark', '#undo'].map((q) => {
          const r = document.querySelector(q).getBoundingClientRect(); return [q, Math.round(r.width), Math.round(r.height), Math.round(r.right)]; })""")
        play = next(x for x in sizes if x[0] == "#play")
        check("màn hình 320px: mọi nút trên thanh phát từ 44px, nút Phát vẫn tròn, không tràn",
              all(w >= 44 and h >= 44 and r <= 320 for _, w, h, r in sizes) and play[1] == play[2], str(sizes))
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(200)
        check("nút phát đủ lớn để chạm (từ 60px)", box["width"] >= 60 and box["height"] >= 60,
              f"{box['width']:.0f}x{box['height']:.0f}")

        print("Dùng với trình đọc màn hình")
        order = await page.evaluate("""() => { const f = (a, b) => !!(document.querySelector(a).compareDocumentPosition(document.querySelector(b)) & 4);
          return [f('#openSettings', '#h-reader'), f('#h-reader', '#play'), f('#play', '#text')]; }""")
        check("thứ tự đọc: Cài đặt, tên phần, nút điều khiển, rồi mới tới nội dung", all(order), str(order))

        para_of = "i => { const e = document.querySelector(`.s[data-i='${i}']`); return e ? [...document.querySelectorAll('#text .seg')].indexOf(e.parentElement) : -1; }"
        before = await page.evaluate(STATE)
        await page.select_option("#step", "para")
        lbl = await spoken_live(page, "đoạn trước")
        check("đổi bước nhảy thì báo bằng lời và đổi tên hai nút",
              "đoạn trước" in lbl and await page.get_attribute("#next", "aria-label") == "Đoạn sau", lbl)
        await page.click("#next")
        await page.wait_for_timeout(300)
        after = await page.evaluate(STATE)
        pb, pa = await page.evaluate(para_of, before["on"]), await page.evaluate(para_of, after["on"])
        first = await page.evaluate("i => document.querySelector(`.s[data-i='${i}']`).previousElementSibling === null", after["on"])
        check("bước nhảy Đoạn: nút tới nhảy sang đầu đoạn văn kế tiếp", pa == pb + 1 and first, f"đoạn {pb} -> {pa}")

        await page.select_option("#step", "time")
        t0 = (await page.evaluate(STATE))["t"]
        await page.click("#next")
        await page.wait_for_timeout(200)
        t1 = (await page.evaluate(STATE))["t"]
        check("bước nhảy 30 giây: nút tới nhảy 30 giây", 29.5 < t1 - t0 < 32, f"{t0:.1f} -> {t1:.1f}")
        await page.keyboard.press("j")
        await page.wait_for_timeout(200)
        t2 = (await page.evaluate(STATE))["t"]
        check("phím J lùi 30 giây", 28 < t1 - t2 < 30.5, f"{t1:.1f} -> {t2:.1f}")

        await page.select_option("#step", "sent")
        await page.evaluate(f"{AUDIO}.pause()")
        await page.wait_for_timeout(200)
        await page.click("#next")
        await page.wait_for_function("document.querySelector('.s.on') && document.querySelector('#live').textContent === document.querySelector('.s.on').textContent", timeout=3000)
        said = await page.inner_text("#live")
        check("đang tạm dừng mà nhảy câu thì đọc câu đó lên", said == await page.inner_text(".s.on") and len(said) > 3, said[:60])
        s = await page.evaluate(STATE)
        check("nhảy câu khi tạm dừng thì vẫn tạm dừng", s["paused"])

        await page.click("#where")
        w = await spoken_live(page, "Tốc độ")
        check("nút Đang ở đâu đọc tên sách, thời điểm, thời gian còn lại và tốc độ",
              all(x in w for x in ("Lão Hạc", "Đang tạm dừng ở", "còn", "Tốc độ")), w)

        await page.select_option("#speed", "3")
        check("tốc độ lên được 3 lần", (await page.evaluate(STATE))["rate"] == 3)
        await page.select_option("#speed", "1.5")

        marked = (await page.evaluate(STATE))["on"]
        await page.click("#mark")
        m = await spoken_live(page, "Đã đánh dấu")
        check("nút Đánh dấu ghi nhớ câu đang nghe và báo bằng lời",
              "Đã đánh dấu" in m and await page.get_attribute("#mark", "aria-pressed") == "true", m)
        await page.goto(BASE + "#/b/lao-hac")
        await page.wait_for_selector(".marks a")
        check("trang bìa liệt kê dấu trang", await page.locator(".marks a").count() == 1, (await page.inner_text(".marks a"))[:70])
        await page.evaluate(f"{AUDIO}.currentTime = 0")
        await page.click(".marks a")
        await page.wait_for_function(f"{AUDIO}.readyState > 0 && document.querySelector('.s.on')", timeout=20000)
        await page.wait_for_timeout(400)
        s = await page.evaluate(STATE)
        check("mở dấu trang thì nghe từ đúng câu đã đánh dấu", s["on"] in (marked, marked + 1) and page.url.endswith("/r/lao-hac/1"),
              f"câu {s['on']}, đánh dấu ở câu {marked}, {page.url.split('#')[1]}")
        await page.goto(BASE + "#/b/lao-hac")
        await page.wait_for_selector(".marks button[data-act='del']")
        await page.click(".marks button[data-act='del']")
        await page.wait_for_timeout(200)
        check("xoá được dấu trang", await page.locator(".marks a").count() == 0 and await page.is_hidden("#bookMarks"))

        await page.keyboard.press("?")
        await page.wait_for_timeout(200)
        focus = await page.evaluate("document.activeElement.id")
        check("phím ? mở hướng dẫn sử dụng và đưa focus vào tiêu đề", await page.evaluate("document.querySelector('#help').open") and focus == "h-help", focus)
        await page.keyboard.press("Escape")
        check("phím Esc đóng hướng dẫn", not await page.evaluate("document.querySelector('#help').open"))

        print("Quay lại, tiếng báo hiệu, tốc độ từng cuốn, màu tô câu, ghi chú bằng giọng nói")
        ready = lambda slug: f"{AUDIO}.currentSrc.includes('{slug}') && {AUDIO}.readyState > 0 && {AUDIO}.duration > 0"
        await page.goto(BASE + "#/r/lao-hac/1")
        await page.wait_for_function(ready("lao-hac") + f" && !{AUDIO}.paused", timeout=20000)
        await page.evaluate(f"{AUDIO}.currentTime = 100")
        await page.wait_for_timeout(300)
        await page.select_option("#step", "time")
        t0 = (await page.evaluate(STATE))["t"]
        await page.click("#next")
        await page.wait_for_timeout(200)
        t1 = (await page.evaluate(STATE))["t"]
        await page.click("#undo")
        u = await spoken_live(page, "Đã quay lại")
        t2 = (await page.evaluate(STATE))["t"]
        check("nút Quay lại đưa về chỗ trước cú nhảy", t1 - t0 > 29 and abs(t2 - t0) < 1.5 and "Đã quay lại" in u
              and await page.get_attribute("#undo", "aria-disabled") == "true", f"{t0:.1f} -> {t1:.1f} -> {t2:.1f}; {u}")
        cues = await page.evaluate("window.snCues.slice()")
        check("quay lại có tiếng báo hiệu", cues and cues[-1] == "undo", str(cues[-4:]))
        await page.select_option("#step", "sent")

        await page.keyboard.press("[")
        lim = await spoken_live(page, "Đây là phần đầu")
        check("tới giới hạn thì có tiếng báo và lời báo", "Đây là phần đầu" in lim and (await page.evaluate("window.snCues.at(-1)")) == "limit", lim)
        await page.click("#openSettings")
        await page.click("#optCue button[data-v='0']")
        off = await spoken_live(page, "Tiếng báo hiệu")
        await page.keyboard.press("Escape")
        n0 = await page.evaluate("window.snCues.length")
        await page.keyboard.press("[")
        await page.wait_for_timeout(200)
        check("tắt tiếng báo hiệu trong Cài đặt thì không còn tiếng báo", await page.evaluate("window.snCues.length") == n0 and "Tắt" in off, off)
        await page.click("#openSettings")
        await page.click("#optCue button[data-v='1']")

        await page.click("#optHl button[data-v='line']")
        await page.keyboard.press("Escape")
        await page.wait_for_selector(".s.on")
        await page.wait_for_timeout(500)          # chờ hiệu ứng chuyển màu nền kết thúc
        bg, deco = await page.evaluate("(() => { const c = getComputedStyle(document.querySelector('.s.on')); return [c.backgroundColor, c.textDecorationLine]; })()")
        check("chọn Gạch chân thì câu đang đọc được gạch chân thay cho tô nền", bg == "rgba(0, 0, 0, 0)" and "underline" in deco, f"{bg}, {deco}")
        await page.click("#openSettings")
        await page.click("#optHl button[data-v='default']")
        await page.keyboard.press("Escape")

        # tốc độ riêng từng cuốn: Lão Hạc đang ở 1,5 lần; chỉnh Tắt đèn lên 2 lần
        await page.goto(BASE + "#/r/tat-den/1")
        await page.wait_for_function(ready("tat-den"), timeout=20000)
        await page.select_option("#speed", "2")
        await page.keyboard.press("]")
        await page.wait_for_function("location.hash.endsWith('/tat-den/2')", timeout=20000)
        await page.wait_for_function(ready("tat-den") + " && document.querySelector('#h-reader').textContent.length > 0", timeout=20000)
        await page.wait_for_timeout(600)
        await page.keyboard.press("z")
        await page.wait_for_timeout(1200)
        check("Quay lại sau khi nhảy sang phần khác thì về phần cũ", page.url.endswith("/tat-den/1"), page.url.split("#")[1])
        await page.goto(BASE + "#/r/lao-hac/1")
        await page.wait_for_function(ready("lao-hac"), timeout=20000)
        r1 = (await page.evaluate(STATE))["rate"]
        await page.goto(BASE + "#/r/tat-den/1")
        await page.wait_for_function(ready("tat-den"), timeout=20000)
        r2 = (await page.evaluate(STATE))["rate"]
        check("tốc độ nhớ riêng từng cuốn", r1 == 1.5 and r2 == 2, f"Lão Hạc {r1}, Tắt đèn {r2}")
        await page.evaluate("localStorage.removeItem('sn:rate:tat-den'); localStorage.setItem('sn:rate', '1.5'); localStorage.removeItem('sn:pos:tat-den')")

        await page.goto(BASE + "#/r/lao-hac/1")
        await page.wait_for_function(ready("lao-hac") + " && document.querySelector('.s.on')", timeout=20000)
        await page.click("#mark")
        await spoken_live(page, "Đã đánh dấu")
        check("đánh dấu có tiếng báo hiệu", (await page.evaluate("window.snCues.at(-1)")) == "mark")
        gap = await page.evaluate("""() => { const t = document.querySelector('#toast').getBoundingClientRect();
          return Math.min(...[...document.querySelectorAll('.top-pills > *')].map((e) => t.top - e.getBoundingClientRect().bottom)); }""")
        check("thông báo nổi không che các nút Cài đặt, Hướng dẫn, Trang bìa", gap >= 0, f"cách {gap:.0f}px")
        await page.goto(BASE + "#/b/lao-hac")
        await page.wait_for_selector(".marks button[data-act='rec']")
        await page.click(".marks button[data-act='rec']")
        rec = await spoken_live(page, "Đang ghi âm")
        await page.wait_for_timeout(1500)
        await page.click(".marks button[data-act='rec']")
        saved = await spoken_live(page, "Đã lưu ghi chú", 8000)
        has_play = await page.locator(".marks button[data-act='play']").count()
        label = await page.get_attribute(".marks a", "aria-label") or ""
        check("ghi âm được ghi chú bằng giọng nói cho dấu trang", "Đang ghi âm" in rec and "Đã lưu ghi chú" in saved and has_play == 1
              and "có ghi chú bằng giọng nói" in label, f"{saved} | {label[:60]}")
        size = await page.evaluate("""() => new Promise((res) => { const r = indexedDB.open('sach-noi', 1);
          r.onsuccess = () => { const q = r.result.transaction('units').objectStore('units').getAllKeys();
            q.onsuccess = async () => { const k = q.result.find((x) => String(x).startsWith('note:lao-hac'));
              if (!k) return res(0); const g = r.result.transaction('units').objectStore('units').get(k); g.onsuccess = () => res(g.result.blob.size); }; }; })""")
        check("ghi chú được lưu trên máy dưới dạng âm thanh", size > 200, f"{size} byte")
        await page.click(".marks button[data-act='play']")
        await page.wait_for_timeout(300)
        check("nghe lại được ghi chú", (await page.inner_text(".marks button[data-act='play']")) == "Dừng nghe")
        await page.click(".marks button[data-act='play']")
        await page.click(".marks button[data-act='del']")
        await page.wait_for_timeout(300)
        left = await page.evaluate("""() => new Promise((res) => { const r = indexedDB.open('sach-noi', 1);
          r.onsuccess = () => { const q = r.result.transaction('units').objectStore('units').getAllKeys();
            q.onsuccess = () => res(q.result.filter((x) => String(x).startsWith('note:')).length); }; })""")
        check("xoá dấu trang thì xoá luôn ghi chú", left == 0 and await page.locator(".marks a").count() == 0, f"còn {left} ghi chú")

        await page.goto(BASE + "#/")
        await page.wait_for_selector("#bookList li")
        await page.click("#voiceSearch")
        v = await spoken_live(page, "Bạn nói")
        n = await page.locator("#bookList li").count()
        check("tìm sách bằng giọng nói: điền điều nghe được và đọc số kết quả",
              await page.input_value("#q") == "Thạch Lam" and f"Bạn nói: Thạch Lam. {n} cuốn khớp." in v and 0 < n < 6, v)
        await page.fill("#q", "")

        print("Thể loại")
        genres = await page.evaluate("[...document.querySelectorAll('#genre option')].map((o) => o.value).filter(Boolean)")
        check("thư viện có từ ba thể loại trở lên", len(genres) >= 3, ", ".join(genres))
        all_n = await page.locator("#bookList li").count()
        await page.select_option("#genre", "Thơ")
        g = await spoken_live(page, "cuốn khớp")
        names = await page.locator("#bookList li b").all_inner_texts()
        check("chọn thể loại Thơ thì chỉ còn sách thơ và có đọc số kết quả", "Truyện Kiều" in names and "Tắt đèn" not in names and 0 < len(names) < all_n
              and f"{len(names)} cuốn khớp" in g, f"{names} | {g}")
        await page.select_option("#genre", "")
        await page.fill("#q", "tiểu thuyết")
        await page.wait_for_timeout(150)
        names = await page.locator("#bookList li b").all_inner_texts()
        check("gõ tên thể loại vào ô tìm cũng ra sách", names == ["Tắt đèn"], str(names))
        await page.fill("#q", "")
        await page.wait_for_timeout(150)
        check("bỏ lọc thì đủ sách trở lại", await page.locator("#bookList li").count() == all_n)
        label = await page.get_attribute("#bookList li a[href='#/b/truyen-kieu']", "aria-label") or ""
        check("nhãn đọc của mỗi cuốn có thể loại", "Nguyễn Du, Thơ" in label, label)

        await page.goto(BASE + "#/r/tat-den/1")
        # chờ đúng audio của phần này (audio của cuốn trước có thể còn nằm trong thẻ audio)
        await page.wait_for_function(f"{AUDIO}.currentSrc.includes('tat-den') && {AUDIO}.readyState > 0 && {AUDIO}.duration > 0", timeout=20000)
        await page.click("#openSettings")
        await page.click("#optSleep button[data-v='-1']")
        await page.keyboard.press("Escape")
        await page.evaluate(f"{AUDIO}.currentTime = {AUDIO}.duration - 1; {AUDIO}.play()")
        await page.wait_for_function("location.hash.endsWith('/tat-den/2')", timeout=60000)
        h = await spoken_live(page, "tạm dừng theo hẹn giờ", 8000)
        await page.wait_for_timeout(800)
        s = await page.evaluate(STATE)
        check("hẹn giờ Hết phần: mở phần sau nhưng không tự phát, có báo bằng lời", s["paused"] and "tạm dừng theo hẹn giờ" in h, h)
        await page.evaluate("localStorage.removeItem('sn:pos:tat-den'); localStorage.removeItem('sn:seen:tat-den')")

        await page.goto(BASE + "#/r/lao-hac/1")
        await page.wait_for_function(f"{AUDIO}.currentSrc.includes('lao-hac') && {AUDIO}.readyState > 0 && {AUDIO}.duration > 100 && !{AUDIO}.paused", timeout=20000)

        print("Nhớ vị trí")
        await page.evaluate(f"{AUDIO}.currentTime = 200")
        await page.wait_for_timeout(300)
        await page.evaluate(f"{AUDIO}.pause()")
        await page.goto(BASE + "#/")
        await page.wait_for_selector("#resume a")
        txt = await page.inner_text("#resume a")
        check("thư viện hiện nút Nghe tiếp", "Nghe tiếp: Lão Hạc" in txt, txt.strip())
        await page.reload(wait_until="networkidle")
        await page.click("#resume a")
        await page.wait_for_function(f"{AUDIO}.currentTime > 195", timeout=20000)
        s = await page.evaluate(STATE)
        check("mở lại nghe tiếp đúng chỗ cũ (200 giây)", 195 < s["t"] < 215, f"t={s['t']:.1f}")

        print("Hết sách")
        await page.evaluate(f"{AUDIO}.playbackRate = 1; {AUDIO}.currentTime = {AUDIO}.duration - 1.2; {AUDIO}.play()")
        await page.wait_for_function(f"{AUDIO}.ended", timeout=15000)
        await page.wait_for_timeout(300)
        check("hết sách thì báo bằng lời", "Đã nghe hết" in await page.inner_text("#live"))

        print("Nhãn trợ năng")
        for route in ("#/", f"#/b/{SLUG}", f"#/r/{SLUG}/1"):
            await page.goto(BASE + route)
            await page.wait_for_timeout(700)
            await page.evaluate(f"{AUDIO}.pause()")
            unnamed = await page.evaluate("""() => [...document.querySelectorAll('button, a, input, select')]
              .filter(e => e.offsetParent !== null)
              .filter(e => !(e.getAttribute('aria-label') || e.innerText.trim() || (e.labels && e.labels.length)))
              .map(e => e.outerHTML.slice(0, 80))""")
            h1 = await page.evaluate("[...document.querySelectorAll('h1')].filter(e => e.offsetParent !== null).length")
            check(f"{route}: mọi nút và liên kết đều có tên, đúng một tiêu đề chính", not unnamed and h1 == 1,
                  f"thiếu tên: {unnamed}" if unnamed else f"h1={h1}")

        # Sách nhiều phần (nếu thư viện có): mục lục, phần chưa có audio, tự sang phần sau.
        cat = await page.evaluate("fetch('catalog.json').then(r => r.json())")
        multi = next((b for b in cat["books"] if len(b.get("units", [])) > 1), None)
        if multi:
            print(f"Sách nhiều phần: {multi['title']}")
            ms, units = multi["slug"], multi["units"]
            ready = [u for u in units if u["ready"]]
            todo = [u for u in units if not u["ready"]]
            await page.goto(BASE + f"#/b/{ms}")
            await page.wait_for_selector(".toc-card li")
            check("mục lục liệt kê đủ mọi phần", await page.locator(".toc-card li").count() == len(units), f"{len(units)} phần")
            check("phần chưa có audio hiện là đang chuẩn bị, không bấm được",
                  await page.locator(".toc-card li.todo").count() == len(todo)
                  and await page.locator(".toc-card li.todo a").count() == 0, f"{len(todo)} phần chờ")
            if len(ready) >= 2:
                a, b = ready[0], ready[1]
                await page.evaluate("localStorage.setItem('sn:rate', '1')")
                await page.goto(BASE + f"#/r/{ms}/{a['no']}")
                # chờ đúng audio của phần này nạp xong (audio của trang trước có thể còn đó)
                await page.wait_for_function(
                    f"/\\/{ms}\\/[^/]+\\/{a['no']:02d}\\.mp3$/.test({AUDIO}.currentSrc) && Number.isFinite({AUDIO}.duration)", timeout=20000)
                check("trang đọc hiện đúng tên phần", await page.inner_text("#h-reader") == a["title"])
                await page.evaluate(f"{AUDIO}.currentTime = {AUDIO}.duration - 1.0; {AUDIO}.play()")
                await page.wait_for_function(f"location.hash.endsWith('/{b['no']}')", timeout=15000)
                await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentTime > 0.3", timeout=20000)
                check("nghe hết một phần thì tự sang phần sau và phát tiếp",
                      await page.inner_text("#h-reader") == b["title"])
                seen = await page.evaluate(f"JSON.parse(localStorage.getItem('sn:seen:{ms}') || '[]')")
                check("phần vừa nghe xong được đánh dấu đã nghe", a["no"] in seen)
                await page.locator("#h-reader").focus()
                await page.keyboard.press("BracketLeft")
                await page.wait_for_function(f"location.hash.endsWith('/{a['no']}')", timeout=5000)
                check("phím [ quay về phần trước", True)
                await page.wait_for_function(
                    f"/\\/{a['no']:02d}\\.mp3$/.test({AUDIO}.currentSrc) && Number.isFinite({AUDIO}.duration)", timeout=20000)
                half = min(a["duration"], b["duration"]) / 2
                await page.evaluate(f"{AUDIO}.currentTime = {half:.1f}; {AUDIO}.play()")
                await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentTime > {half:.1f} + 0.3", timeout=20000)
                await page.locator("#h-reader").focus()
                await page.keyboard.press("BracketRight")
                await page.wait_for_function(
                    f"/\\/{b['no']:02d}\\.mp3$/.test({AUDIO}.currentSrc) && !{AUDIO}.paused && {AUDIO}.currentTime > 0.2", timeout=20000)
                await page.wait_for_timeout(300)
                t = await page.evaluate(f"{AUDIO}.currentTime")
                said = await page.inner_text("#live")
                check("đang nghe giữa phần mà sang phần sau thì phần sau bắt đầu từ đầu",
                      t < 8 and "Nghe tiếp từ" not in said, f"t={t:.1f}, {said or '(không thông báo)'}")
                pos = await page.evaluate(f"JSON.parse(localStorage.getItem('sn:pos:{ms}'))")
                check("vị trí đã lưu là của phần đang nghe", pos["unit"] == b["no"] and pos["t"] < 8, json.dumps(pos))
                await page.evaluate(f"{AUDIO}.pause()")

        # Chọn giọng đọc: chỉ chạy khi thư viện có cả hai giọng VieNeu nu và nam (voices.py). Từ 16/11/2026
        # thư viện dùng một giọng Hoài My nên khối này tự bỏ qua; giữ lại cho lúc thêm giọng thứ hai.
        both = next((b for b in cat["books"] if b.get("units")
                     and {"nu", "nam"} <= set(b["units"][0].get("voices", {}))), None)
        if both:
            print(f"Chọn giọng đọc: {both['title']}")
            vs, u0 = both["slug"], both["units"][0]
            await page.evaluate("localStorage.removeItem('sn:voice'); localStorage.setItem('sn:rate', '1')")
            await page.evaluate(f"localStorage.removeItem('sn:pos:{vs}')")
            await page.goto(BASE + f"#/b/{vs}")
            await page.reload(wait_until="networkidle")
            await page.wait_for_selector(".voice-pick button")
            pressed = await page.locator(".voice-pick button").evaluate_all(
                "els => els.map(e => [e.dataset.v, e.getAttribute('aria-pressed'), e.innerText.trim()])")
            check("trang bìa có hai lựa chọn giọng, mặc định giọng nữ",
                  [x[:2] for x in pressed] == [["nu", "true"], ["nam", "false"]], str(pressed))
            check("nút tải DAISY đi theo giọng đang chọn",
                  (await page.get_attribute('.cta a[href*="-daisy-"]', "href")).endswith("-daisy-nu.zip"))

            await page.click("#bookHero .btn.primary")
            await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('/nu/')", timeout=20000)
            check("mặc định phát giọng nữ", True)
            nam = await page.evaluate(
                f"fetch('{u0['voices']['nam']['data']}').then(r=>r.json()).then(d=>d.paras.flatMap(p=>p.s.map(x=>[x[0],x[1]])))")
            nu = await page.evaluate(
                f"fetch('{u0['voices']['nu']['data']}').then(r=>r.json()).then(d=>d.paras.flatMap(p=>p.s.map(x=>[x[0],x[1]])))")
            # một câu dài ở cả hai giọng, để lúc bấm đổi giọng vẫn còn trong câu đó dù máy đang chậm
            K = next(i for i in range(5, len(nu) - 2) if nu[i][1] - nu[i][0] > 6 and nam[i][1] - nam[i][0] > 5)
            await page.locator(".s").nth(K - 1).scroll_into_view_if_needed()
            await page.locator(".s").nth(K - 1).click()       # câu số K (câu số 0 là tiêu đề)
            await page.wait_for_timeout(500)
            await page.click("#openSettings")
            await page.click('#optVoice button[data-v="nam"]')
            await page.wait_for_function(f"{AUDIO}.currentSrc.includes('/nam/') && {AUDIO}.currentTime > 1", timeout=20000)
            await page.wait_for_timeout(300)
            s = await page.evaluate(STATE)
            check("đổi sang giọng nam giữa chừng thì nghe tiếp đúng câu đang nghe",
                  s["on"] == K and nam[K][0] - 0.05 <= s["t"] < nam[K + 1][0], f"câu {s['on']} (mong đợi {K}), t={s['t']:.2f}")
            check("đổi giọng không làm dừng phát", not s["paused"])
            said = await spoken_live(page, "giọng nam Thiện Minh")
            check("đổi giọng được thông báo bằng lời", "giọng nam Thiện Minh" in said, said)
            check("nút giọng nam ở trạng thái đang chọn",
                  await page.get_attribute('#optVoice button[data-v="nam"]', "aria-pressed") == "true")
            tbox = await page.locator("#toast").bounding_box()
            check("đổi giọng có thông báo nhìn thấy được, hiện cả khi hộp Cài đặt đang mở",
                  await page.locator("#toast").is_visible() and tbox and tbox["height"] > 10
                  and await page.evaluate("document.querySelector('#toast').matches(':popover-open')")
                  and "giọng nam Thiện Minh" in await page.inner_text("#toast"), await page.inner_text("#toast"))
            check("trang đọc ghi rõ giọng đang phát",
                  "giọng nam Thiện Minh" in await page.inner_text("#readerByline"), await page.inner_text("#readerByline"))
            await page.keyboard.press("Escape")

            await page.evaluate(f"{AUDIO}.currentTime = {{}}".format("%.2f" % (nam[20][0] + 0.4)))
            await page.wait_for_timeout(300)
            await page.evaluate(f"{AUDIO}.pause()")
            await page.evaluate("localStorage.setItem('sn:voice', JSON.stringify('nu'))")
            await page.reload(wait_until="load")
            await page.wait_for_function(f"{AUDIO}.currentSrc.includes('/nu/') && {AUDIO}.currentTime > 1", timeout=20000)
            await page.wait_for_timeout(300)
            s = await page.evaluate(STATE)
            check("vị trí lưu ở giọng nam, mở lại bằng giọng nữ vẫn về đúng câu", s["on"] == 20, f"câu {s['on']}")
            await page.evaluate(f"{AUDIO}.pause()")

            print("Đổi giọng khi audio mới còn đang nạp")

            async def slow(route):
                await asyncio.sleep(1.5)
                try:
                    await route.continue_()
                except Exception:
                    pass          # yêu cầu đã bị huỷ vì người nghe đổi sang giọng khác

            await page.evaluate(f"localStorage.removeItem('sn:pos:{vs}')")
            await page.reload(wait_until="load")
            await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('/nu/') && {AUDIO}.currentTime > 0.2", timeout=20000)
            await page.locator(".s").nth(K - 1).scroll_into_view_if_needed()
            await page.locator(".s").nth(K - 1).click()
            await page.wait_for_timeout(600)
            await page.route("**/nam/*.mp3", slow)
            await page.click("#openSettings")
            await page.click('#optVoice button[data-v="nam"]')
            await page.wait_for_timeout(400)                    # audio giọng nam chưa về tới
            pos = await page.evaluate(f"JSON.parse(localStorage.getItem('sn:pos:{vs}'))")
            check("giọng mới chưa nạp xong thì vị trí đã lưu vẫn đúng câu đang nghe",
                  pos and pos.get("s") == K and (nu if pos.get("v") == "nu" else nam)[K][0] - 0.2 <= pos["t"] < (nu if pos.get("v") == "nu" else nam)[K + 1][0],
                  json.dumps(pos))
            await page.click('#optVoice button[data-v="nu"]')   # đổi lại ngay, khi giọng nam chưa nạp xong
            await page.wait_for_function(f"{AUDIO}.currentSrc.includes('/nu/') && !{AUDIO}.paused && {AUDIO}.currentTime > 1", timeout=20000)
            await page.wait_for_timeout(300)
            s = await page.evaluate(STATE)
            check("đổi giọng qua lại thật nhanh vẫn giữ đúng câu đang nghe", s["on"] == K, f"câu {s['on']} (mong đợi {K}), t={s['t']:.2f}")
            await page.keyboard.press("Escape")
            await page.unroute("**/nam/*.mp3")
            await page.evaluate(f"{AUDIO}.pause()")

            await page.goto(BASE + f"#/b/{vs}")
            await page.wait_for_selector(".voice-pick button")
            await page.click('.voice-pick button[data-v="nam"]')
            await page.wait_for_function(
                "document.querySelector('.voice-pick button[data-v=\"nam\"]').getAttribute('aria-pressed') === 'true'")
            check("chọn giọng ngay trên trang bìa, nút tải DAISY đổi theo",
                  (await page.get_attribute('.cta a[href*="-daisy-"]', "href")).endswith("-daisy-nam.zip"))

        # Phần chưa có giọng đang chọn: phát giọng khác đang có và nói rõ.
        # Các giọng chính của thư viện (không tính giọng dự phòng). Thư viện một giọng thì không có gì để chọn.
        prim = list({v["id"]: v for b in cat["books"] for v in b.get("voices", [])
                     if not v.get("fallback") and v["id"] != "piper"}.values())
        P = prim[0] if prim else None
        p_txt = f"{P['label'].lower()} {P['name']}" if P else ""
        partial = next(((b, u) for b in cat["books"] for u in b.get("units", [])
                        if P and u["ready"] and P["id"] not in u["voices"]), None)
        if partial:
            pb, pu = partial
            print(f"Phần chưa có giọng chính: {pb['title']}")
            await page.evaluate(f"localStorage.setItem('sn:voice', JSON.stringify('{P['id']}'))")
            await page.evaluate(f"localStorage.removeItem('sn:pos:{pb['slug']}')")
            await page.goto(BASE + f"#/b/{pb['slug']}")
            await page.reload(wait_until="load")
            await page.wait_for_selector("#h-book")
            if not any(P["id"] in u["voices"] for u in pb["units"]):
                note = await page.inner_text(".voice-note")
                check("trang bìa ghi rõ giọng chính đang được chuẩn bị", P["name"] in note and "đang được chuẩn bị" in note, note)
            await page.goto(BASE + f"#/r/{pb['slug']}/{pu['no']}")
            await page.wait_for_function(f"Number.isFinite({AUDIO}.duration)", timeout=20000)
            said = await spoken_live(page, f"chưa có {p_txt}")
            check("phần chưa có giọng chính thì phát giọng khác và báo bằng lời", f"chưa có {p_txt}" in said, said)
            check("thông báo đó cũng hiện ra cho người nhìn màn hình",
                  await page.locator("#toast").is_visible()
                  and f"chưa có {p_txt}" in await page.inner_text("#toast"), await page.inner_text("#toast"))
            byline = await page.inner_text("#readerByline")
            check("trang đọc ghi rõ đang phát giọng nào", "giọng" in byline and P["name"] not in byline, byline)
            await page.evaluate(f"{AUDIO}.pause()")
            await page.click("#openSettings")
            check("hộp Cài đặt giải thích vì sao chưa nghe được giọng chính",
                  f"chưa có {p_txt}" in await page.inner_text("#voiceInfo"), await page.inner_text("#voiceInfo"))
            await page.keyboard.press("Escape")
            # đang nghe dở: câu "Nghe tiếp từ…" không được đè mất ghi chú về giọng
            await page.evaluate(f"{AUDIO}.currentTime = 65")
            await page.wait_for_timeout(300)
            await page.evaluate(f"{AUDIO}.pause()")
            await page.goto(BASE + "#/")
            await page.wait_for_selector("#resume a")
            await page.goto(BASE + f"#/r/{pb['slug']}/{pu['no']}")
            await page.wait_for_function(f"{AUDIO}.currentTime > 60", timeout=20000)
            await page.wait_for_timeout(300)
            live = await page.inner_text("#live")
            check("mở lại cuốn nghe dở: báo cả giọng đang phát lẫn vị trí nghe tiếp",
                  f"chưa có {p_txt}" in live and "Nghe tiếp từ" in live, live)
            await page.evaluate(f"{AUDIO}.pause()")
        done = next((b for b in cat["books"] if P and b.get("units") and all(P["id"] in u["voices"] for u in b["units"])), None)
        if done:
            await page.goto(BASE + f"#/b/{done['slug']}")
            await page.wait_for_selector("#h-book")
            check("cuốn đã đủ giọng chính thì trang bìa không còn ghi chú hay nút chọn giọng (khi chỉ có một giọng)",
                  len(prim) > 1 or (await page.locator(".voice-note").count() == 0 and await page.locator(".voice-pick").count() == 0))
            await page.click("#bookHero .btn.primary")
            await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('/{P['id']}/')", timeout=20000)
            byline = await page.inner_text("#readerByline")
            check("cuốn đã có giọng chính thì phát đúng giọng đó", P["name"] in byline, byline)
            await page.evaluate(f"{AUDIO}.pause()")
            if len(prim) < 2:
                await page.click("#openSettings")
                check("thư viện một giọng thì hộp Cài đặt không hiện mục chọn giọng",
                      not await page.locator("#optVoice").is_visible() and not await page.locator("#l-voice").is_visible())
                await page.keyboard.press("Escape")
        await page.evaluate("localStorage.removeItem('sn:voice')")

        # Lệnh phát bị ngắt (rời trang đọc, mở phần khác) không được hiện lời nhắc nhấn Phát;
        # chỉ khi trình duyệt chặn tự phát mới nhắc.
        print("Lời nhắc nhấn Phát")
        for err, expect in (("AbortError", False), ("NotAllowedError", True)):
            await page.goto(BASE + "#/")
            await page.wait_for_function("document.body.dataset.view !== 'reader'")
            await page.evaluate("document.querySelector('#live').textContent = ''")
            await page.evaluate(f"""(() => {{ const a = {AUDIO}; const real = a.play;
                a.play = () => {{ a.play = real; return Promise.reject(new DOMException('thử', '{err}')); }}; }})()""")
            await page.goto(BASE + f"#/r/{SLUG}/1")
            await page.wait_for_function(f"{AUDIO}.currentSrc.includes('{SLUG}') && Number.isFinite({AUDIO}.duration)", timeout=20000)
            await page.wait_for_timeout(400)
            said = await spoken_live(page, "Nhấn nút Phát", 1500 if expect else 300)
            check("trình duyệt chặn tự phát thì nhắc nhấn nút Phát" if expect
                  else "lệnh phát bị ngắt giữa chừng thì không hiện lời nhắc nhấn Phát",
                  ("Nhấn nút Phát" in said) == expect, said or "(trống)")
            await page.evaluate(f"{AUDIO}.pause()")

        print("Chế độ chạm đơn giản")
        await page.goto(BASE + "#/")
        await page.wait_for_selector("#bookList li")
        said = lambda: page.evaluate("window.snSpoken.at(-1) || ''")
        await page.click("#simpleOn")
        await page.wait_for_timeout(300)
        box = await page.evaluate("""() => { const r = (s) => document.querySelector(s).getBoundingClientRect();
          const ids = ['#sInfo', '#sPrev', '#sNext', '#sMain', '#sAlt'];
          return { min: Math.min(...ids.map((s) => Math.min(r(s).width, r(s).height))), main: r('#sMain').height,
                   scroll: getComputedStyle(document.body).overflow !== 'hidden' || r('#simple').height > innerHeight + 1, focus: document.activeElement.id,
                   inert: [...document.querySelectorAll('.view')].every((v) => v.inert),
                   n: document.querySelectorAll('#simple button:not([hidden])').length }; }""")
        check("chế độ đơn giản: năm nút lớn phủ kín màn hình, không phải cuộn",
              box["n"] == 5 and box["min"] >= 90 and box["main"] >= 250 and not box["scroll"], str(box))
        check("chế độ đơn giản: giao diện đầy đủ bên dưới bị khoá, focus nằm ở nút lớn", box["inert"] and box["focus"] == "sMain")
        s0 = await said()
        check("chế độ đơn giản: vừa bật là tự đọc cách dùng và cuốn đang chọn", "Chạm một lần là chạy" in s0 and "Đang chọn:" in s0 and "trên 14" in s0, s0[-70:])
        import re
        at = int(re.search(r"cuốn (\d+) trên 14", s0).group(1))
        wrap = lambda k: (k - 1) % 14 + 1
        await page.click("#sNext")
        await page.wait_for_timeout(150)
        s1 = await said()
        await page.click("#sPrev")
        await page.click("#sPrev")
        await page.wait_for_timeout(150)
        s2 = await said()
        check("chế độ đơn giản: chạm Sách sau, Sách trước thì đọc tên từng cuốn",
              f"cuốn {wrap(at + 1)} trên 14" in s1 and f"cuốn {wrap(at - 1)} trên 14" in s2, f"{s1} | {s2}")
        for _ in range(14):
            if "Chí Phèo" in await page.inner_text("#sInfo b"):
                break
            await page.click("#sNext")
        await page.click("#sMain")
        await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('chi-pheo')", timeout=20000)
        check("chế độ đơn giản: một lần chạm nút lớn là sách phát", "/r/chi-pheo/" in page.url
              and (await page.inner_text("#sMain b")) == "Tạm dừng" and (await page.inner_text("#sNext b")) == "Tới 30 giây")
        await page.wait_for_function(f"{AUDIO}.currentTime > 0.3")
        t0 = (await page.evaluate(STATE))["t"]
        await page.click("#sNext")
        await page.wait_for_timeout(200)
        t1 = (await page.evaluate(STATE))["t"]
        check("chế độ đơn giản: khi đang nghe, nút tới nhảy 30 giây", 29 < t1 - t0 < 32, f"{t0:.1f} -> {t1:.1f}")
        await page.click("#sInfo")
        await page.wait_for_timeout(150)
        w = await said()
        check("chế độ đơn giản: nút trên cùng đọc đang ở đâu rồi đọc hướng dẫn", "Chí Phèo" in w and "Đang nghe tới" in w and "Hướng dẫn:" in w, w)
        await page.click("#sMain")
        await page.wait_for_timeout(200)
        check("chế độ đơn giản: chạm lần nữa thì tạm dừng và nói Tạm dừng",
              (await page.evaluate(STATE))["paused"] and (await said()) == "Tạm dừng." and (await page.inner_text("#sMain b")) == "Phát")
        await page.click("#sAlt")
        await page.wait_for_function("location.hash === '#/'")
        await page.wait_for_timeout(300)
        b = await said()
        check("chế độ đơn giản: Chọn sách khác đưa về chỗ chọn sách, nhớ cuốn vừa nghe",
              b.startswith("Chọn sách. Chí Phèo") and (await page.inner_text("#sMain b")) == "Nghe tiếp", b)
        await page.reload()
        await page.wait_for_function("document.querySelector('#sInfo').textContent.includes('Chí Phèo')", timeout=10000)
        check("chế độ đơn giản: mở lại ứng dụng vẫn ở chế độ đơn giản", not await page.evaluate("document.querySelector('#simple').hidden"))
        await page.click("#sAlt")
        out = await spoken_live(page, "giao diện đầy đủ")
        check("chế độ đơn giản: thoát được về giao diện đầy đủ",
              await page.evaluate("document.querySelector('#simple').hidden && !document.querySelector('#view-library').inert")
              and "giao diện đầy đủ" in out and await page.evaluate("document.activeElement.id") == "h-library", out)
        await page.evaluate("localStorage.removeItem('sn:pos:chi-pheo')")

        print("Chế độ chạm đơn giản: chọn phần và đổi tốc độ")
        await page.goto(BASE + "#/")
        await page.wait_for_selector("#bookList li")
        await page.evaluate("localStorage.removeItem('sn:rate:truyen-kieu'); localStorage.removeItem('sn:marks:truyen-kieu'); localStorage.setItem('sn:rate', '1')")
        await page.click("#simpleOn")
        check("khi chọn sách chưa có nút đổi chức năng", await page.is_hidden("#sMode"))
        for _ in range(14):
            if "Truyện Kiều" in await page.inner_text("#sInfo b"):
                break
            await page.click("#sNext")
        await page.click("#sMain")
        await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('truyen-kieu')", timeout=20000)
        u0 = int(page.url.rsplit("/", 1)[1])
        await page.click("#sMode")
        await page.wait_for_timeout(150)
        m = await said()
        check("nút đổi chức năng: lần chạm đầu chuyển sang chọn phần và nói rõ",
              "phần trước" in m and "phần sau" in m and "trên 13" in m and (await page.inner_text("#sNext b")) == "Phần sau", m)
        await page.click("#sNext")
        await page.wait_for_function(f"location.hash.endsWith('/truyen-kieu/{u0 + 1}') && !{AUDIO}.paused && {AUDIO}.currentSrc.includes('/{u0 + 1:02d}.mp3')", timeout=20000)
        sp = await page.evaluate("window.snSpoken.slice(-2).join(' | ')")
        check("chọn phần: một lần chạm sang phần sau, đọc tên phần và phát tiếp", f"phần {u0 + 1} trên 13" in sp, sp)
        await page.click("#sPrev")
        await page.wait_for_function(f"location.hash.endsWith('/truyen-kieu/{u0}') && !{AUDIO}.paused", timeout=20000)
        check("chọn phần: nút bên trái về phần trước", True)
        await page.click("#sMode")
        await page.wait_for_timeout(150)
        m = await said()
        check("nút đổi chức năng: lần chạm thứ hai chuyển sang tốc độ", "chậm hơn" in m and "nhanh hơn" in m and "Tốc độ hiện tại 1 lần" in m, m)
        await page.click("#sNext")
        await page.wait_for_timeout(150)
        r = (await page.evaluate(STATE))["rate"]
        check("đổi tốc độ: nút bên phải nhanh hơn một nấc và đọc tốc độ mới", r == 1.25 and "1 phẩy 25" in await said(), f"{r}; {await said()}")
        await page.click("#sPrev")
        await page.click("#sPrev")
        await page.wait_for_timeout(150)
        check("đổi tốc độ: nút bên trái chậm hơn", (await page.evaluate(STATE))["rate"] == 0.75)
        await page.click("#sNext")
        await page.click("#sMode")
        await page.wait_for_timeout(150)
        m = await said()
        check("nút đổi chức năng: lần chạm thứ ba chuyển sang dấu trang", "tới dấu trang" in m and "đánh dấu" in m and "chưa có dấu trang" in m, m)
        await page.click("#sPrev")
        await page.wait_for_timeout(150)
        check("dấu trang: chưa có dấu trang nào thì nói rõ", "chưa có dấu trang" in await said(), await said())
        await page.evaluate(f"{AUDIO}.currentTime = 20")
        await page.wait_for_timeout(300)
        await page.click("#sNext")
        await page.wait_for_timeout(150)
        marks = await page.evaluate("JSON.parse(localStorage.getItem('sn:marks:truyen-kieu') || '[]')")
        check("dấu trang: nút bên phải đánh dấu chỗ đang nghe", len(marks) == 1 and "Đã đánh dấu" in await said(), await said())
        await page.evaluate(f"{AUDIO}.currentTime += 40")
        await page.click("#sPrev")
        await page.wait_for_timeout(300)
        s = await page.evaluate(STATE)
        check("dấu trang: nút bên trái đưa về chỗ đã đánh dấu và vẫn phát",
              "Dấu trang 1 trên 1" in await said() and s["on"] == marks[0]["s"] and not s["paused"], f"{await said()}; câu {s['on']}, dấu trang ở câu {marks[0]['s']}")
        await page.click("#sMode")
        await page.wait_for_timeout(150)
        m = await said()
        check("nút đổi chức năng: lần chạm thứ tư chuyển sang hẹn giờ tắt", "bớt giờ" in m and "thêm giờ" in m and "Hẹn giờ đang tắt" in m, m)
        await page.click("#sNext")
        await page.wait_for_timeout(150)
        check("hẹn giờ: nút bên phải đặt 15 phút", "Sẽ tự dừng sau 15 phút" in await said(), await said())
        await page.click("#sPrev")
        await page.wait_for_timeout(150)
        check("hẹn giờ: nút bên trái tắt hẹn giờ", "Đã tắt hẹn giờ" in await said(), await said())
        await page.click("#sPrev")
        await page.wait_for_timeout(150)
        check("hẹn giờ: đang tắt mà bớt nữa thì nói rõ", "Hẹn giờ đang tắt" in await said(), await said())
        await page.evaluate("localStorage.removeItem('sn:marks:truyen-kieu')")
        await page.click("#sMode")
        await page.wait_for_timeout(150)
        check("nút đổi chức năng: chạm lần nữa quay về 30 giây", (await page.inner_text("#sNext b")) == "Tới 30 giây" and "30 giây" in await said())
        fit = await page.evaluate("""() => ['#sMode', '#sAlt'].map((s) => { const r = document.querySelector(s).getBoundingClientRect(); return Math.min(r.width, r.height); })""")
        check("hai nút hàng dưới vẫn đủ lớn", min(fit) >= 60, str(fit))
        await page.click("#sAlt")
        await page.wait_for_function("location.hash === '#/'")
        await page.click("#sAlt")
        await page.evaluate("localStorage.removeItem('sn:pos:truyen-kieu'); localStorage.removeItem('sn:rate:truyen-kieu'); localStorage.setItem('sn:rate', '1.5')")

        print("Nhảy theo dấu trang, tốc độ 0,5 lần, lùi về đầu câu khi nghe tiếp")
        await page.evaluate("""localStorage.setItem('sn:marks:truyen-kieu', JSON.stringify([
          { unit: 1, s: 5, t: 18, text: 'câu năm', at: 1 }, { unit: 1, s: 12, t: 50, text: 'câu mười hai', at: 2 },
          { unit: 2, s: 3, t: 8, text: 'ở phần hai', at: 3 }]))""")
        await page.goto(BASE + "#/r/truyen-kieu/1")
        await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('truyen-kieu') && {AUDIO}.currentTime > 0.2", timeout=20000)
        await page.select_option("#step", "mark")
        check("bước nhảy dấu trang: hai nút đổi tên", await page.get_attribute("#next", "aria-label") == "Dấu trang sau")
        await page.click("#next")
        m = await spoken_live(page, "Dấu trang 1 trên 3")
        check("nút tới nhảy đến dấu trang đầu tiên phía sau", "Dấu trang 1 trên 3" in m and (await page.evaluate(STATE))["on"] == 5, m)
        await page.click("#next")
        await spoken_live(page, "Dấu trang 2 trên 3")
        check("nhấn tiếp thì tới dấu trang kế", (await page.evaluate(STATE))["on"] == 12)
        await page.click("#next")
        m = await spoken_live(page, "Dấu trang 3 trên 3")
        await page.wait_for_function(f"location.hash.endsWith('/truyen-kieu/2') && {AUDIO}.currentSrc.includes('/02.mp3') && !{AUDIO}.paused && {AUDIO}.currentTime > 0.2", timeout=20000)
        on = (await page.evaluate(STATE))["on"]
        check("dấu trang ở phần khác: mở đúng phần, đúng câu, đọc tên phần", on == 3 and "Dấu trang 3 trên 3, " in m, f"câu {on}; {m}")
        await page.click("#next")
        m = await spoken_live(page, "Không còn dấu trang")
        check("hết dấu trang phía sau thì báo", "Không còn dấu trang nào phía sau" in m, m)
        await page.click("#prev")
        await page.wait_for_function(f"location.hash.endsWith('/truyen-kieu/1') && {AUDIO}.currentSrc.includes('/01.mp3') && !{AUDIO}.paused", timeout=20000)
        await page.wait_for_timeout(300)
        check("nút lùi về dấu trang trước, ở phần trước", (await page.evaluate(STATE))["on"] == 12)
        await page.select_option("#step", "sent")
        await page.evaluate("localStorage.removeItem('sn:marks:truyen-kieu')")

        await page.select_option("#speed", "0.5")
        await page.locator("#h-reader").focus()
        await page.keyboard.press("ArrowDown")
        m = await spoken_live(page, "chậm nhất")
        check("tốc độ xuống được 0,5 lần và đó là mức chậm nhất", (await page.evaluate(STATE))["rate"] == 0.5 and "chậm nhất" in m, m)
        await page.select_option("#speed", "1")

        starts = await page.evaluate("fetch('books/truyen-kieu/hm/01.json').then((r) => r.json()).then((d) => d.paras.flatMap((p) => p.s.map((x) => x[0])))")
        await page.evaluate("window.snOff = 0; window.snNow = Date.now; Date.now = () => window.snNow() + window.snOff")
        async def pause_mid(i):
            await page.evaluate(f"{AUDIO}.pause()")
            await page.wait_for_timeout(100)
            await page.evaluate(f"{AUDIO}.currentTime = {starts[i] + 2.6}")
            await page.wait_for_timeout(200)
            await page.evaluate(f"{AUDIO}.play()")
            await page.wait_for_function(f"!{AUDIO}.paused")
            await page.evaluate(f"{AUDIO}.pause()")
            await page.wait_for_timeout(200)
            return (await page.evaluate(STATE))["t"]
        t0 = await pause_mid(20)
        await page.evaluate("window.snOff += 60000")
        await page.click("#play")
        await page.wait_for_function(f"!{AUDIO}.paused")
        await page.wait_for_timeout(300)
        t1 = (await page.evaluate(STATE))["t"]
        check("dừng lâu rồi nghe tiếp: lùi về đầu câu đang nghe dở", starts[20] - 0.1 <= t1 < starts[20] + 1.5 and t0 > starts[20] + 2.5,
              f"dừng ở {t0:.1f}, nghe tiếp từ {t1:.1f}, đầu câu {starts[20]:.1f}")
        t0 = await pause_mid(24)
        await page.click("#play")
        await page.wait_for_function(f"!{AUDIO}.paused")
        await page.wait_for_timeout(300)
        t1 = (await page.evaluate(STATE))["t"]
        check("dừng một chút rồi nghe tiếp: không lùi", t0 - 0.05 <= t1 < t0 + 1.5, f"{t0:.1f} -> {t1:.1f}")
        await page.evaluate("document.querySelector('#optRewind button[data-v=\"0\"]').click()")
        t0 = await pause_mid(28)
        await page.evaluate("window.snOff += 60000")
        await page.click("#play")
        await page.wait_for_function(f"!{AUDIO}.paused")
        await page.wait_for_timeout(300)
        t1 = (await page.evaluate(STATE))["t"]
        check("tắt trong Cài đặt thì nghe tiếp đúng chỗ đã dừng", t0 - 0.05 <= t1 < t0 + 1.5, f"{t0:.1f} -> {t1:.1f}")
        await page.evaluate("document.querySelector('#optRewind button[data-v=\"1\"]').click(); document.querySelector('#optAuto button[data-v=\"0\"]').click()")
        t0 = await pause_mid(32)
        await page.goto(BASE + "#/")
        await page.wait_for_selector("#bookList li")
        await page.goto(BASE + "#/r/truyen-kieu/1")
        m = await spoken_live(page, "Nghe tiếp từ", 20000)
        t1 = (await page.evaluate(STATE))["t"]
        check("mở lại sách: nghe tiếp từ đầu câu đang nghe dở", abs(t1 - starts[32]) < 0.1 and "Nghe tiếp từ" in m, f"dừng ở {t0:.1f}, mở lại ở {t1:.1f}, đầu câu {starts[32]:.1f}; {m}")
        await page.evaluate("document.querySelector('#optAuto button[data-v=\"1\"]').click(); Date.now = window.snNow; localStorage.removeItem('sn:pos:truyen-kieu')")

        print("Tìm trong sách")
        await page.goto(BASE + "#/b/truyen-kieu")
        await page.wait_for_selector("#findQ")
        await page.fill("#findQ", "tram nam trong coi")
        await page.press("#findQ", "Enter")
        await page.wait_for_selector("#findList li")
        info = await spoken_live(page, "Tìm thấy")
        first = page.locator("#findList li a").first
        check("tìm không dấu vẫn ra câu có dấu, báo số câu bằng lời",
              "Tìm thấy" in info and "Trăm năm trong cõi" in await first.inner_text() and (await first.get_attribute("href")).endswith("/truyen-kieu/1/s2"),
              f"{info}; {await first.get_attribute('href')}")
        check("chữ tìm thấy được tô trong kết quả", (await page.inner_text("#findList li mark")) == "Trăm năm trong cõi")
        await page.fill("#findQ", "nang")
        await page.press("#findQ", "Enter")
        await page.wait_for_function("document.querySelector('#findInfo').textContent.includes('“nang”')")
        info = await page.inner_text("#findInfo")
        n = await page.locator("#findList li").count()
        units = await page.evaluate("new Set([...document.querySelectorAll('#findList a')].map((a) => a.getAttribute('href').split('/')[3])).size")
        check("tìm trong cả cuốn, qua nhiều phần, hiện tối đa 50 câu", n == 50 and units > 1 and "hiện 50 câu đầu" in info, f"{n} câu, {units} phần; {info}")
        hit = page.locator("#findList li a").nth(7)
        href, text = await hit.get_attribute("href"), (await hit.locator("span").inner_text()).strip("…")
        await hit.click()
        try:      # câu được tô đúng là câu trong liên kết, sau khi audio nạp xong
            await page.wait_for_function("i => document.querySelector('.s.on')?.dataset.i === i", arg=href.rsplit("/s", 1)[1], timeout=20000)
        except Exception:
            pass
        on = await page.inner_text(".s.on")
        norm = lambda x: " ".join(x.split())
        check("chọn một kết quả thì mở đúng câu đó", norm(text)[:40] in norm(on), f"{href}: {text[:60]!r} / {on[:60]!r}")
        await page.goto(BASE + "#/b/truyen-kieu")
        await page.wait_for_selector("#findList li")
        check("quay lại trang bìa vẫn còn ô tìm và danh sách kết quả", await page.input_value("#findQ") == "nang" and await page.locator("#findList li").count() == 50)
        await page.fill("#findQ", "xyzq")
        await page.press("#findQ", "Enter")
        info = await spoken_live(page, "Không tìm thấy")
        check("không có kết quả thì nói rõ", "Không tìm thấy “xyzq”" in info and await page.locator("#findList li").count() == 0, info)
        await page.fill("#findQ", "a")
        await page.press("#findQ", "Enter")
        info = await spoken_live(page, "ít nhất hai")
        check("gõ quá ngắn thì nhắc", "ít nhất hai chữ cái" in info, info)
        await page.evaluate("localStorage.removeItem('sn:pos:truyen-kieu')")

        print("Trang bìa với trình đọc màn hình")
        await page.goto(BASE + "#/b/truyen-kieu")
        await page.wait_for_selector("#tocJump")
        await page.click("#tocJump")
        check("nút Mục lục đưa focus tới mục lục", await page.evaluate("document.activeElement.id") == "h-toc")
        await page.route("**/books/truyen-kieu/**", lambda r: asyncio.ensure_future(slow_route(r)))
        await page.click("#saveBtn")
        st = await spoken_live(page, "Đang lưu Truyện Kiều")
        check("bấm Lưu thì báo ngay là đang lưu, nút vẫn giữ focus",
              "Đang lưu Truyện Kiều, 13 phần" in st and await page.evaluate("document.activeElement.id") == "saveBtn"
              and await page.get_attribute("#saveBtn", "aria-disabled") == "true", st)
        prog = await spoken_live(page, "trên 13 phần", 30000)
        check("đang lưu thì báo tiến độ bằng lời", "trên 13 phần" in prog, prog)
        await page.wait_for_function("document.querySelector('#saveBtn').innerText.includes('Đã lưu')", timeout=120000)
        await page.unroute("**/books/truyen-kieu/**")
        await page.click("#saveBtn")
        await spoken_live(page, "Đã xoá bản lưu")

        print("Lưu ngoại tuyến")
        await page.goto(BASE + f"#/b/{SLUG}")
        await page.wait_for_selector("#saveBtn")
        await page.click("#saveBtn")
        await page.wait_for_function("document.querySelector('#saveBtn').innerText.includes('Đã lưu')", timeout=60000)
        check("lưu sách vào máy", True)
        await ctx.set_offline(True)
        await page.click("#bookHero .btn.primary")
        await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.startsWith('blob:')", timeout=15000)
        t0 = (await page.evaluate(STATE))["t"]
        await page.wait_for_timeout(1500)
        s = await page.evaluate(STATE)
        check("mất mạng vẫn phát được từ bản đã lưu", s["t"] > t0 and s["n"] > 200, f"t {t0:.1f} -> {s['t']:.1f}")
        await ctx.set_offline(False)
        check("không có lỗi JavaScript trong suốt phiên", not errors, "; ".join(errors[:3]))
        await ctx.close()

        print("Service worker")
        ctx2 = await browser.new_context(viewport={"width": 390, "height": 844}, locale="vi-VN")
        page2 = await ctx2.new_page()
        await page2.goto(BASE, wait_until="networkidle")
        await page2.evaluate("navigator.serviceWorker.ready.then(() => true)")
        await page2.wait_for_timeout(1500)
        await page2.reload(wait_until="networkidle")     # lần tải thứ hai đi qua service worker
        await ctx2.set_offline(True)
        await page2.reload()
        await page2.wait_for_selector("#bookList li", timeout=10000)
        check("mất mạng vẫn mở được thư viện nhờ service worker", await page2.locator("#bookList li").count() >= 5)
        await ctx2.close()
        await browser.close()

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} đạt")
    sys.exit(1 if failed else 0)


asyncio.run(main())
