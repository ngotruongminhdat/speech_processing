"""Dựng video demo của ứng dụng Sách Nói.

Trình duyệt tự chạy kịch bản ở kích thước điện thoại và quay lại; lời thuyết minh thu bằng
giọng Hoài My (edge-tts); ffmpeg ghép hình, lời thuyết minh và một đoạn tiếng sách thật.

Chạy (cần site/ đã dựng và máy chủ thử đang chạy ở cổng 8931):
    python3 app/tests/serve.py 8931 &
    .venv/bin/python demo/make_demo_video.py [file-zip-DAISY-để-minh-hoạ-nhập-sách]
Kết quả: demo/outputs/video/sach-noi-demo.mp4 (bản nộp được chép sang demo/sach-noi-demo.mp4)
"""
import asyncio
import glob
import os
import subprocess
import sys
import time
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "demo" / "outputs" / "video"
BASE = "http://127.0.0.1:8931/"
VOICE = "vi-VN-HoaiMyNeural"
W, H = 1920, 1080
PHONE_W, PHONE_H = 499, 1080
PHONE_X, PANEL_X = 110, 700
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif{}.ttf"
BOOK_AUDIO = ROOT / "site" / "books" / "lao-hac" / "hm" / "01.mp3"
LISTEN_SECS = 8.0

MOCK_RECOGNIZER = """window.webkitSpeechRecognition = window.SpeechRecognition = class {
  start() { setTimeout(() => { this.onstart && this.onstart();
    setTimeout(() => { this.onresult && this.onresult({ results: [[{ transcript: window.snSay || '' }]] }); this.onend && this.onend(); }, 900); }, 20); }
  abort() { this.onend && this.onend(); } };"""
TAP_MARK = """addEventListener('pointerdown', e => {
  const d = document.createElement('div');
  d.style.cssText = `position:fixed;left:${e.clientX - 22}px;top:${e.clientY - 22}px;width:44px;height:44px;border-radius:50%;
    background:rgba(255,196,60,.55);border:2px solid rgba(255,255,255,.9);z-index:99999;pointer-events:none;transition:opacity .5s, transform .5s`;
  document.documentElement.appendChild(d);
  requestAnimationFrame(() => { d.style.opacity = '0'; d.style.transform = 'scale(1.8)'; });
  setTimeout(() => d.remove(), 600);
}, true);"""

# (khoá, tiêu đề, lời thuyết minh). Lời rỗng: cảnh nghe tiếng sách thật.
SCENES = [
    ("thu-vien", "Thư viện",
     "Đây là Sách Nói, thư viện sách nói tiếng Việt theo chuẩn DAISY dành cho người khiếm thị. "
     "Thư viện có mười lăm đầu sách thuộc phạm vi công cộng, đọc bằng giọng Hoài My."),
    ("tim-sach", "Tìm sách",
     "Người dùng tìm sách bằng cách gõ tên, tác giả hoặc thể loại, không cần gõ dấu. "
     "Ở đây chúng em gõ Thạch Lam, rồi lọc theo thể loại Thơ."),
    ("trang-bia", "Trang bìa và tìm trong sách",
     "Trang bìa cho biết tác giả, thời lượng và các phần của sách. "
     "Ngay tại đây có thể tìm một từ trong cả cuốn, và ứng dụng mở đúng câu chứa từ đó."),
    ("trang-doc", "Trang đọc",
     "Trên trang đọc, văn bản hiện cùng âm thanh, và câu đang đọc được tô sáng."),
    ("nghe", "Nghe thử", ""),
    ("cham-cau", "Chạm vào câu để nghe",
     "Chạm vào câu nào thì ứng dụng đọc từ câu đó."),
    ("dieu-huong", "Điều hướng",
     "Hai nút lùi và tới dùng chung một bước nhảy chọn được: câu, đoạn, ba mươi giây, phần, hoặc dấu trang. "
     "Nếu nhảy nhầm thì bấm Quay lại."),
    ("toc-do", "Tốc độ, dấu trang, hẹn giờ",
     "Tốc độ chỉnh được từ không phẩy năm đến ba lần. "
     "Người nghe đánh dấu trang, hỏi mình đang ở đâu, và hẹn giờ tắt."),
    ("thi-luc-kem", "Dành cho người thị lực kém",
     "Với người thị lực kém, phần cài đặt có ba nền, bốn cỡ chữ, kiểu chữ dễ đọc, và nhiều cách tô câu đang đọc."),
    ("tho", "Sách thơ",
     "Với sách thơ như Truyện Kiều, mỗi câu thơ nằm trên một dòng."),
    ("don-gian", "Chế độ chạm đơn giản",
     "Chế độ chạm đơn giản thay cả màn hình bằng vài nút rất lớn, chạm một lần là chạy, "
     "và ứng dụng tự đọc lời nhắc bằng giọng Hoài My. "
     "Khi đang nghe, nút ở góc dưới đổi chức năng của hai nút lớn: tua, chọn phần, tốc độ, dấu trang, hẹn giờ."),
    ("giong-noi", "Điều khiển bằng giọng nói",
     "Người dùng cũng ra lệnh được bằng giọng nói: bấm nút micro rồi nói, ví dụ, mở Truyện Kiều, hoặc, nhanh hơn. "
     "Trong video này, câu lệnh được đưa vào bằng một bộ nhận dạng giả lập."),
    ("nhap-sach", "Nhập sách của riêng mình",
     "Người dùng nhập được sách nói DAISY của riêng mình từ một file zip. "
     "File được đọc ngay trên máy, không gửi lên mạng, và nghe được như mọi cuốn khác."),
    ("ngoai-tuyen", "Nghe ngoại tuyến và cài đặt",
     "Từng cuốn lưu được vào máy để nghe khi mất mạng. "
     "Ứng dụng cài được lên Android bằng file A P K, và lên iPhone qua Safari."),
    ("ket", "Sách Nói",
     "Sách Nói đang chạy tại địa chỉ hiện trên màn hình. Cảm ơn thầy cô đã theo dõi."),
]
NOTES = {
    "nghe": "Tiếng sách thật: truyện Lão Hạc, giọng Hoài My.",
    "giong-noi": "Câu lệnh trong cảnh này do bộ nhận dạng giả lập đưa vào, không phải micro thật.",
    "nhap-sach": "Sách mẫu của DAISY Consortium.",
    "ket": "ngotruongminhdat.github.io/speech_processing",
}


async def narrate(key, text):
    path = OUT / f"loi-{key}.mp3"
    if not path.exists():
        for attempt in range(40):
            try:
                await asyncio.wait_for(edge_tts.Communicate(text, VOICE).save(str(path)), 40)
                if path.stat().st_size > 2000:
                    break
            except Exception:  # dịch vụ hay từ chối: thử lại ngay
                path.unlink(missing_ok=True)
                await asyncio.sleep(0.5)
        else:
            raise RuntimeError(f"không thu được lời thuyết minh: {key}")
    return MP3(path).info.length


def panel(index, key, title, text):
    img = Image.new("RGBA", (W - PANEL_X, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    small, big, body = (ImageFont.truetype(FONT.format(s), n) for s, n in (("", 26), ("-Bold", 58), ("", 34)))
    d.text((0, 150), f"SÁCH NÓI  ·  {index}/{len(SCENES)}", font=small, fill="#c9a36a")
    y = 205
    for line in wrap(d, title, big, W - PANEL_X - 90):
        d.text((0, y), line, font=big, fill="#fff6e6")
        y += 76
    y += 40
    for line in wrap(d, text, body, W - PANEL_X - 110):
        d.text((0, y), line, font=body, fill="#e8dcc8")
        y += 52
    if key in NOTES:
        y += 36
        for line in wrap(d, NOTES[key], small, W - PANEL_X - 110):
            d.text((0, y), line, font=small, fill="#c9a36a")
            y += 40
    path = OUT / f"bang-{key}.png"
    img.save(path)
    return path


def wrap(d, text, font, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=font) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


async def record(durations, sample_zip):
    exe = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")))[-1]
    starts = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe, args=["--autoplay-policy=no-user-gesture-required"])
        ctx = await browser.new_context(viewport={"width": 390, "height": 844}, locale="vi-VN",
                                        record_video_dir=str(OUT / "raw"), record_video_size={"width": 390, "height": 844})
        await ctx.add_init_script(MOCK_RECOGNIZER + TAP_MARK +
                                  "if (!localStorage.getItem('sn:autoplay')) localStorage.setItem('sn:autoplay', '\"0\"');")
        page = await ctx.new_page()
        t0 = time.monotonic()
        wait = page.wait_for_timeout

        async def tap(sel, after=900):
            loc = page.locator(sel).first
            await loc.scroll_into_view_if_needed()
            await loc.click()
            await wait(after)

        async def scroll(y, after=900):
            await page.evaluate("y => (document.scrollingElement).scrollTo({ top: y, behavior: 'smooth' })", y)
            await wait(after)

        async def setting(group, value, after=1300):
            await tap("#openSettings", 700)
            await tap(f"#{group} [data-v='{value}']", 600)
            await tap("#settings .set-close", after)

        async def scene(key, actions):
            start = time.monotonic() - t0
            starts[key] = start
            await actions()
            left = start + durations[key] + 0.5 - (time.monotonic() - t0)
            if left > 0:
                await wait(left * 1000)

        await page.goto(BASE)
        await wait(2500)

        async def s_library():
            await wait(3000); await scroll(700, 2500); await scroll(1500, 2500); await scroll(0)
        await scene("thu-vien", s_library)

        async def s_search():
            await page.locator("#q").scroll_into_view_if_needed()
            await page.locator("#q").click()
            await page.keyboard.type("thach lam", delay=140)
            await wait(600); await scroll(520, 2200)
            await page.fill("#q", ""); await scroll(250, 500)
            await page.select_option("#genre", "Thơ"); await wait(800); await scroll(560, 2200)
            await page.select_option("#genre", "")
        await scene("tim-sach", s_search)

        async def s_cover():
            await page.goto(BASE + "#/b/lao-hac"); await wait(2200)
            await scroll(520, 2200)
            await page.locator("#findQ").scroll_into_view_if_needed()
            await page.locator("#findQ").click()
            await page.keyboard.type("con cho", delay=140)
            await page.keyboard.press("Enter"); await wait(2500)
            await tap("#findList a", 1500)
        await scene("trang-bia", s_cover)

        async def s_reader():
            await page.goto(BASE + "#/r/lao-hac/1"); await wait(1500)
            await page.wait_for_function("document.querySelector('#audio').readyState >= 3", timeout=20000)
            await page.evaluate("document.querySelector('#audio').currentTime = 0")
        await scene("trang-doc", s_reader)

        async def s_listen():
            await page.evaluate("document.querySelector('#audio').currentTime = 0")
            await page.click("#play")
        await scene("nghe", s_listen)
        print("thời điểm âm thanh sau cảnh nghe:", await page.evaluate("document.querySelector('#audio').currentTime"))

        async def s_tap_sentence():
            await page.click("#play"); await wait(500)
            await tap("#text .s >> nth=6", 1500)
        await scene("cham-cau", s_tap_sentence)

        async def s_navigate():
            await tap("#next"); await tap("#next")
            await page.select_option("#step", "para"); await wait(700); await tap("#next")
            await page.select_option("#step", "time"); await wait(700); await tap("#next")
            await page.select_option("#step", "sent"); await wait(500); await tap("#undo", 1200)
        await scene("dieu-huong", s_navigate)

        async def s_speed():
            await page.select_option("#speed", "1.5"); await wait(1500)
            await tap("#mark", 1800); await tap("#where", 2200)
            await tap("#openSettings", 800); await tap("#optSleep [data-v='15']", 1300); await tap("#settings .set-close", 600)
        await scene("toc-do", s_speed)

        async def s_low_vision():
            await setting("optTheme", "dark"); await setting("optTheme", "contrast")
            await setting("optSize", "1.45"); await setting("optHl", "blue", 1500)
        await scene("thi-luc-kem", s_low_vision)
        for group, value in (("optTheme", "paper"), ("optSize", "1"), ("optHl", "default"), ("optSleep", "0")):
            await page.evaluate("([g, v]) => document.querySelector(`#${g} [data-v='${v}']`).click()", [group, value])
        await page.select_option("#speed", "1")

        async def s_verse():
            await page.goto(BASE + "#/r/truyen-kieu/1"); await wait(2000); await scroll(260)
        await scene("tho", s_verse)

        async def s_simple():
            await page.goto(BASE + "#/"); await wait(1500)
            await tap("#simpleOn", 2500); await tap("#sNext", 1500); await tap("#sNext", 1500)
            await tap("#sMain", 3500)
            for _ in range(4):
                await tap("#sMode", 1700)
            await tap("#sMode", 1200); await tap("#sNext", 1200)
        await scene("don-gian", s_simple)

        async def s_voice():
            await page.evaluate("window.snSay = 'Mở Truyện Kiều.'"); await wait(2500)
            await tap("#sVoice", 5500)
            await page.evaluate("window.snSay = 'nhanh hơn'")
            await tap("#sVoice", 3000)
        await scene("giong-noi", s_voice)
        await page.evaluate("document.querySelector('#audio').pause(); localStorage.setItem('sn:simple', '\"0\"')")
        await page.reload()

        async def s_import():
            await page.goto(BASE + "#/"); await wait(1500)
            await page.locator("#importBtn").scroll_into_view_if_needed(); await wait(1500)
            await page.set_input_files("#importFile", sample_zip)
            await page.wait_for_function("(JSON.parse(localStorage.getItem('sn:imported') || '[]')).length > 0", timeout=60000)
            await wait(1500); await scroll(620, 2500)
            await tap("#bookList a", 2500)
        await scene("nhap-sach", s_import)

        async def s_offline():
            await page.goto(BASE + "#/b/gio-lanh-dau-mua"); await wait(1800)
            await tap("#saveBtn", 3500)
            await page.goto(BASE + "#/"); await wait(1200)
            await tap("[data-help]", 1200)
            await page.evaluate("document.querySelector('#apkLink').scrollIntoView({ behavior: 'smooth', block: 'center' })")
        await scene("ngoai-tuyen", s_offline)

        async def s_end():
            await page.keyboard.press("Escape"); await scroll(0)
        await scene("ket", s_end)
        await wait(800)
        total = time.monotonic() - t0
        video = await page.video.path()
        await ctx.close()
        await browser.close()
    return Path(video), starts, total


def compose(video, starts, durations, total):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    keys = [k for k, _, _ in SCENES]
    cmd = [ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x1c1410:s={W}x{H}:d={total:.2f}:r=25", "-i", str(video)]
    for i, (key, title, text) in enumerate(SCENES, 1):
        cmd += ["-i", str(panel(i, key, title, text))]
    spoken = [k for k, _, t in SCENES if t]
    for key in spoken:
        cmd += ["-i", str(OUT / f"loi-{key}.mp3")]
    cmd += ["-t", str(LISTEN_SECS), "-i", str(BOOK_AUDIO)]
    filt = [f"[1:v]scale={PHONE_W}:{PHONE_H}:flags=lanczos[ph]", f"[0:v][ph]overlay={PHONE_X}:0[v0]"]
    for i, key in enumerate(keys):
        end = starts[keys[i + 1]] if i + 1 < len(keys) else total
        filt.append(f"[v{i}][{i + 2}:v]overlay={PANEL_X}:0:enable='between(t,{starts[key]:.2f},{end:.2f})'[v{i + 1}]")
    base = 2 + len(keys)
    for j, key in enumerate(spoken):
        ms = int((starts[key] + 0.3) * 1000)
        filt.append(f"[{base + j}:a]adelay={ms}:all=1[a{j}]")
    ms = int(starts["nghe"] * 1000)
    filt.append(f"[{base + len(spoken)}:a]afade=t=out:st={LISTEN_SECS - 1}:d=1,adelay={ms}:all=1[ab]")
    filt.append("".join(f"[a{j}]" for j in range(len(spoken))) + f"[ab]amix=inputs={len(spoken) + 1}:normalize=0[aout]")
    out = OUT / "sach-noi-demo.mp4"
    cmd += ["-filter_complex", ";".join(filt), "-map", f"[v{len(keys)}]", "-map", "[aout]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sample = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "site/books/duoi-bong-hoang-lan/duoi-bong-hoang-lan-daisy-hm.zip")
    durations = {}
    for key, _, text in SCENES:
        durations[key] = await narrate(key, text) if text else LISTEN_SECS
    print("tổng lời thuyết minh: %.1f giây" % sum(durations.values()))
    video, starts, total = await record(durations, sample)
    out = compose(video, starts, durations, total)
    print(out, "%.1f giây" % total)


if __name__ == "__main__":
    asyncio.run(main())
