# Sách Nói — ứng dụng đọc sách tiếng Việt cho người khiếm thị

Đồ án cuối kỳ môn Xử lý tiếng nói (branch `main`, phát triển trên branch `final_project`), kế thừa đồ án giữa kỳ (branch `mid_term_project`, sách nói DAISY của Totto-chan).

**Dùng thử:** https://ngotruongminhdat.github.io/speech_processing/

Thư viện sách nói theo chuẩn DAISY 3, nghe trên trình duyệt điện thoại: văn bản tô sáng theo từng câu, nút lớn, đọc được bằng trình đọc màn hình, điều khiển từ màn hình khóa, nhớ chỗ đang nghe, lưu sách để nghe khi mất mạng.

## Cài đặt ứng dụng

Ứng dụng chạy ngay trên trình duyệt tại https://ngotruongminhdat.github.io/speech_processing/, không bắt buộc phải cài. Muốn có biểu tượng riêng trên màn hình chính và mở toàn màn hình:

- **Android (file APK):** tải https://ngotruongminhdat.github.io/speech_processing/SachNoi.apk (cũng là file `app/android/SachNoi-1.0.0.apk` trong repo), mở file vừa tải, cho phép "Cài ứng dụng từ nguồn không xác định". Cần Android 7 trở lên và có Chrome. Chi tiết và cách dựng lại: `app/android/README.md`.
- **Android (không cần APK):** mở trang bằng Chrome, trình đơn ba chấm, chọn "Thêm vào màn hình chính" hoặc "Cài đặt ứng dụng".
- **iPhone, iPad:** mở trang bằng Safari, nhấn nút Chia sẻ, chọn "Thêm vào Màn hình chính". Chưa có bản cài riêng cho iOS vì việc đó cần máy Mac và tài khoản Apple Developer.

Các cách cài trên chưa được thử trên điện thoại thật.

## Nhập sách của riêng bạn

Cuối Thư viện có mục "Sách của bạn": nhấn "Nhập sách DAISY từ máy" rồi chọn file zip chứa sách nói DAISY 2.02 hoặc DAISY 3. File được đọc ngay trên máy (`app/web/daisy-import.js`), sách lưu trong trình duyệt và nghe được khi không có mạng. Sách mẫu để thử: https://daisy.org/info-help/document-archive/sample-files/

## Dòng dữ liệu

```
Wikisource (phạm vi công cộng)
   │  import_wikisource.py        văn bản sạch, mỗi đoạn một id
   ▼
books/<slug>/build/chapter_NN/segments.json + dtbook.xml
   │  tts_chapter_edge.py         giọng chính của thư viện: Hoài My (Microsoft, qua edge-tts), mốc câu từ WordBoundary
   │  tts_chapter_vieneu.py       hai giọng VieNeu-TTS chạy trên máy (Ngọc Linh, Thiện Minh), nay là giọng dự phòng
   │  tts_chapter_piper.py        giọng Piper, rất nhanh, làm giọng dự phòng
   │  gen_smil.py, gen_opf_ncx.py DAISY 3: SMIL, OPF, NCX
   │  validate_daisy.py           kiểm tra chéo
   ▼
books/<slug>/voices/<nu|nam>/     mỗi giọng một bản DAISY đầy đủ, có mốc đoạn + mốc câu
   │
   ▼
build_site.py ──► site/ ──► deploy_site.py ──► GitHub Pages (branch gh-pages)
```

## Cấu trúc

| Thư mục | Nội dung | Mục chấm điểm |
|---|---|---|
| `literature/` | PDF và ghi chú 8 bài báo, khảo sát trong nước, bảng so sánh | Tổng quan 30% |
| `demo/` | Đo tốc độ TTS trên CPU và độ rõ qua ASR, trang nghe thử so sánh giọng | Demo 20% |
| `pipeline/scripts/` | Nhập sách, TTS, sinh DAISY, lắp trang web, deploy | Demo 20% |
| `app/web/` | Ứng dụng web: thư viện, trang bìa, trình phát | App 30% |
| `app/tests/` | 46 kiểm thử đầu-cuối bằng Chromium, máy chủ thử | App 30% |
| `books/` | Metadata từng cuốn, danh mục, căn cứ bản quyền | – |
| `report/` | So sánh TTS, nhật ký quyết định, bảng số liệu | Phân tích 20% |

Audio, mô hình và trang đã lắp (`books/*/build/`, `books/*/voices/`, `models/`, `site/`) không nằm trong git; dựng lại bằng các lệnh dưới đây.

## Chạy

```bash
python3 -m venv .venv
.venv/bin/pip install piper-tts vieneu lameenc numpy mutagen edge-tts   # dựng sách
.venv/bin/pip install playwright faster-whisper jiwer pillow            # kiểm thử và đo đạc

# giọng đọc: tải vi_VN-vais1000-medium.onnx và .onnx.json từ
# https://huggingface.co/rhasspy/piper-voices/tree/main/vi/vi_VN/vais1000/medium vào models/piper/

# thêm một cuốn sách thuộc phạm vi công cộng rồi dựng
python3 pipeline/scripts/import_wikisource.py --slug lao-hac --author "Nam Cao" --year 1943 "Lão Hạc"
.venv/bin/python pipeline/scripts/build_book.py lao-hac                 # bản Piper, vài chục giây
.venv/bin/python pipeline/scripts/build_voices.py lao-hac               # giọng chính Hoài My (edge-tts, cần mạng); chạy lại để làm tiếp phần bị lỗi
                                                                        # mô hình tự tải vào models/vieneu/ ở lần chạy đầu

# thử trên máy (máy chủ này hỗ trợ HTTP Range, cần để tua audio)
python3 pipeline/scripts/build_site.py
python3 app/tests/serve.py 8931 &
.venv/bin/python app/tests/e2e.py http://127.0.0.1:8931/

# deploy: chạy lại mỗi khi xong thêm một chương hay một cuốn
python3 pipeline/scripts/deploy_site.py
```

## Phần kế thừa và phần làm mới

| | Giữa kỳ | Cuối kỳ |
|---|---|---|
| Sách | 1 cuốn (Totto-chan) | Thư viện, thêm sách bằng 2 lệnh |
| Giọng đọc | edge-tts, dịch vụ ngoài, đọc từng đoạn | Vẫn giọng Hoài My (edge-tts) sau khi đã thử và đo Piper, VieNeu-TTS chạy trên máy; ứng dụng hỗ trợ nhiều giọng, phần chưa có giọng chính thì phát giọng dự phòng và nói rõ |
| Đồng bộ | Mức đoạn | Mức câu |
| Trình phát | Trang HTML sinh sẵn cho từng chương, thanh phát tràn trên điện thoại | Một ứng dụng, thiết kế cho điện thoại và trình đọc màn hình |
| Ngoại tuyến | Không | Lưu sách trên máy, cài lên màn hình chính |
| Kiểm thử | Kiểm tra cấu trúc DAISY | Thêm 46 kiểm thử giao diện trên trình duyệt thật |

Script sinh DAISY (`gen_smil.py`, `gen_opf_ncx.py`, `validate_daisy.py`, `extract_chapter.py`) và ngôn ngữ thiết kế giao diện lấy từ giữa kỳ. Xem `report/decisions.md` cho lý do của từng quyết định và `PLAN.md` cho việc còn lại.
