#!/usr/bin/env python3
"""Kiểm thử đầu-cuối của Sách Nói bằng Chromium không giao diện (Playwright).

Chạy trên bản đã lắp trong site/ và đang được phục vụ qua HTTP:
  python3 pipeline/scripts/build_site.py
  python3 app/tests/serve.py 8931 &          # máy chủ có hỗ trợ Range, cần để tua audio
  .venv/bin/python app/tests/e2e.py http://127.0.0.1:8931/
"""
import asyncio
import glob
import os
import sys

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8931/"
SLUG = "lao-hac"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("  ✅ " if cond else "  ❌ ") + name + (f"  [{detail}]" if detail else ""))


def chromium_path():
    hits = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")))
    return hits[-1] if hits else None


AUDIO = "document.querySelector('#audio')"
STATE = f"""(() => {{ const a = {AUDIO}; const on = document.querySelector('.s.on');
  return {{ t: a.currentTime, paused: a.paused, rate: a.playbackRate, dur: a.duration, src: a.currentSrc,
           on: on ? Number(on.dataset.i) : -1, nOn: document.querySelectorAll('.s.on').length,
           n: document.querySelectorAll('.s').length }}; }})()"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chromium_path(),
                                          args=["--autoplay-policy=no-user-gesture-required"])
        ctx = await browser.new_context(viewport={"width": 390, "height": 844}, locale="vi-VN",
                                        service_workers="block")
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
        await page.click(".cta .btn.primary")
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

        await page.evaluate(f"{AUDIO}.currentTime = 30")
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
        check("nút phát đủ lớn để chạm (từ 60px)", box["width"] >= 60 and box["height"] >= 60,
              f"{box['width']:.0f}x{box['height']:.0f}")

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
                await page.evaluate(f"{AUDIO}.pause()")

        # Chọn giọng đọc: cần một cuốn đã có cả giọng nữ và giọng nam cho phần đầu.
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

            await page.click(".cta .btn.primary")
            await page.wait_for_function(f"!{AUDIO}.paused && {AUDIO}.currentSrc.includes('/nu/')", timeout=20000)
            check("mặc định phát giọng nữ", True)
            nam = await page.evaluate(
                f"fetch('{u0['voices']['nam']['data']}').then(r=>r.json()).then(d=>d.paras.flatMap(p=>p.s.map(x=>[x[0],x[1]])))")
            await page.locator(".s").nth(11).scroll_into_view_if_needed()
            await page.locator(".s").nth(11).click()          # câu số 12
            await page.wait_for_timeout(500)
            await page.click("#openSettings")
            await page.click('#optVoice button[data-v="nam"]')
            await page.wait_for_function(f"{AUDIO}.currentSrc.includes('/nam/') && {AUDIO}.currentTime > 1", timeout=20000)
            await page.wait_for_timeout(300)
            s = await page.evaluate(STATE)
            check("đổi sang giọng nam giữa chừng thì nghe tiếp đúng câu đang nghe",
                  s["on"] == 12 and nam[12][0] - 0.05 <= s["t"] < nam[13][0], f"câu {s['on']}, t={s['t']:.2f}")
            check("đổi giọng không làm dừng phát", not s["paused"])
            check("đổi giọng được thông báo bằng lời",
                  "giọng nam Thiện Minh" in await page.inner_text("#live"), await page.inner_text("#live"))
            check("nút giọng nam ở trạng thái đang chọn",
                  await page.get_attribute('#optVoice button[data-v="nam"]', "aria-pressed") == "true")
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

            await page.goto(BASE + f"#/b/{vs}")
            await page.wait_for_selector(".voice-pick button")
            await page.click('.voice-pick button[data-v="nam"]')
            await page.wait_for_function(
                "document.querySelector('.voice-pick button[data-v=\"nam\"]').getAttribute('aria-pressed') === 'true'")
            check("chọn giọng ngay trên trang bìa, nút tải DAISY đổi theo",
                  (await page.get_attribute('.cta a[href*="-daisy-"]', "href")).endswith("-daisy-nam.zip"))

        # Phần chưa có giọng đang chọn: phát giọng khác đang có và nói rõ.
        partial = next(((b, u) for b in cat["books"] for u in b.get("units", [])
                        if u["ready"] and "nam" not in u["voices"] and any(v["id"] == "nam" for v in b["voices"])), None)
        if partial:
            pb, pu = partial
            await page.evaluate("localStorage.setItem('sn:voice', JSON.stringify('nam'))")
            await page.goto(BASE + f"#/r/{pb['slug']}/{pu['no']}")
            await page.reload(wait_until="load")
            await page.wait_for_function(f"Number.isFinite({AUDIO}.duration)", timeout=20000)
            check("phần chưa có giọng nam thì phát giọng khác và báo bằng lời",
                  "chưa có giọng nam" in await page.inner_text("#live"), await page.inner_text("#live"))
            await page.evaluate(f"{AUDIO}.pause()")
        await page.evaluate("localStorage.removeItem('sn:voice')")

        print("Lưu ngoại tuyến")
        await page.goto(BASE + f"#/b/{SLUG}")
        await page.wait_for_selector("#saveBtn")
        await page.click("#saveBtn")
        await page.wait_for_function("document.querySelector('#saveBtn').innerText.includes('Đã lưu')", timeout=60000)
        check("lưu sách vào máy", True)
        await ctx.set_offline(True)
        await page.click(".cta .btn.primary")
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
