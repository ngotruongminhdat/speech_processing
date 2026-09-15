# Xử lý tiếng nói — Xây dựng sách điện tử DAISY

Đồ án giữa kỳ môn Xử lý tiếng nói (K35): xây dựng sách điện tử tiếng Việt theo **tiêu chuẩn [DAISY 3](https://daisy.org/activities/standards/daisy/daisy-3/)** (Digital Talking Book) dành cho người khiếm thị.

> 📋 Yêu cầu chi tiết của đồ án: [Slide hướng dẫn xây dựng sách điện tử DAISY](https://docs.google.com/presentation/d/1JJl0Sy5eJnCZ_7IxEMl7jFcWCd-SpePr4qnL7CBc0lA/edit)

## Giới thiệu

[DAISY](https://daisy.org/) (Digital Accessible Information System) là chuẩn sách nói có điều hướng: âm thanh kèm theo cấu trúc sách (mục lục, chương, trang), cho phép tìm kiếm, nhảy nhanh đến chương/mục mong muốn và đánh dấu trang — khác với sách audio thông thường vốn rất khó điều hướng.

Project này xây dựng bộ dữ liệu sách DAISY 3 tiếng Việt từ các nguồn tài liệu khác nhau (văn bản, audio có sẵn, hoặc PDF/ảnh scan).

## Cấu trúc file DAISY 3

Mỗi cuốn sách là một tập hợp các file phối hợp với nhau:

| File | Vai trò |
|------|---------|
| `.xml` (DTBook) | Nội dung văn bản, cấu trúc chương mục, thẻ định danh (`id`) để liên kết với âm thanh |
| `.smil` | Xác định đồng bộ giữa đoạn văn bản (theo `id` trong `.xml`) và file âm thanh |
| `.opf` | Tệp gói (package/manifest) liệt kê toàn bộ tài nguyên của sách (xml, smil, ncx, mp3) và metadata |
| `.ncx` | Tệp điều hướng, tạo mục lục phân cấp, liên kết đến vị trí trong `.xml` hoặc `.smil` |
| `.mp3` | File âm thanh giọng đọc (nên chia thành nhiều file nhỏ thay vì một file lớn) |

File `.opf` là trung tâm: khai báo và liên kết đến `.xml`, `.smil`, `.ncx`, `.mp3`. Mỗi file `.smil` tham chiếu các anchor trong `.xml` và trỏ đến các đoạn `.mp3` để phát âm thanh đồng bộ với văn bản.

## Các pipeline xử lý

Tùy theo loại tài liệu nguồn:

1. **Có text nhưng chưa có audio** — bài toán Text-to-Speech (TTS), dùng [SSML](https://www.w3.org/TR/speech-synthesis11/) để điều khiển ngắt nghỉ, nhấn mạnh, tốc độ, cao độ (ví dụ: [Amazon Polly](https://aws.amazon.com/polly/), [Microsoft Azure Neural TTS](https://azure.microsoft.com/en-us/products/ai-services/text-to-speech), [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)).
2. **Có audio nhưng chưa có text** — bài toán Speech-to-Text (STT) kết hợp cắt audio khớp với từ, câu hoặc đoạn văn (nguồn: [thuviensachnoihuongduong.com](https://thuviensachnoihuongduong.com/)).
3. **Tài liệu PDF hoặc hình ảnh** — bài toán OCR → văn bản → TTS (ví dụ: sách giáo khoa, sách thiếu nhi có bố cục phức tạp).

## Quy tắc chọn sách

- Không trùng với các sách đã có, căn cứ theo mã **ISBN** — kiểm tra [danh sách tài liệu đã đăng ký](https://docs.google.com/spreadsheets/u/0/d/1L4jyXhzCIRdCxh6BBAQ_eWDfz_sKjl4tblFBBB8uYS0/htmlview) trước khi chọn (bản sao offline: `data/registered_books.csv`).
- Ưu tiên sách tiếng Việt, bản tái bản mới nhất, và các thể loại ưu tiên (đặc biệt là sách giáo khoa).
- Yêu cầu làm trọn vẹn từng cuốn sách trước khi nộp.

### Metadata bắt buộc (Dublin Core)

`title` (tên sách), `creator` (tác giả), `subject` (thể loại), `description` (mô tả sơ lược), `publisher` (nhà phát hành), `date` (định dạng `yyyy[-mm[-dd]]`), `source` (mã ISBN), `language` (`"vi"`), `note` (ghi chú), cùng hai trường mở rộng ngoài chuẩn: `collector` (người đóng góp) và `sourceURL` (URL gốc của sách).

## Định dạng nộp bài

```
MSHV1_MSHV2_MSHV3/
├── Tên_sách-Chương 1/
│   ├── Tên_sách.zip              # gồm các file .xml, .smil, .mp3, .opf, .ncx
│   └── Tên_sách_sha256sums.txt   # hash SHA-256
└── Tên_sách-Chương 2/
    ├── Tên_sách.zip
    └── Tên_sách_sha256sums.txt
```

Sách có kích thước lớn có thể chia thành các phần nhỏ hơn (chương, hồi); các phần vẫn giữ mã ISBN gốc.

## Các bước thực hiện

1. **Lựa chọn sách** — kiểm tra không trùng ISBN, thu thập đầy đủ thông tin, nguồn gốc.
2. **Tìm kiếm công cụ** — công cụ TTS, cắt/ghép audio với text, điều chỉnh giọng đọc, chuyển đổi định dạng ([DAISY Pipeline 2](https://daisy.org/activities/software/pipeline-2/)).
3. **Thực hiện thử nghiệm** — xây dựng metadata, chương đầu tiên, ước tính độ dài sách; đổi sách hoặc công cụ nếu không phù hợp.
4. **Kiểm tra chất lượng & báo cáo** — kiểm tra chất lượng audio và lỗi chính tả, phát thử bằng [Thorium Reader](https://thorium.edrlab.org/) / [Dolphin EasyReader](https://yourdolphin.com/EasyReader), sau đó tổng hợp và trình bày quá trình xây dựng bộ dữ liệu.

## Pipeline kỹ thuật (scripts/)

Bộ script sinh sách DAISY 3, chạy thử được ngay trên chương 1:

```bash
python3 -m venv .venv && .venv/bin/pip install edge-tts mutagen   # lần đầu
.venv/bin/python scripts/build_chapter.py 1                        # chạy trọn pipeline chương 1
```

| Script | Vai trò |
|--------|---------|
| `extract_chapter.py` | EPUB → `dtbook.xml` + `segments.json` (tạm thay phần của Lộc) |
| `tts_chapter.py` | Text → `chuongNN.mp3` + `timestamps.csv` bằng edge-tts (tạm thay phần của Vy) |
| `gen_smil.py` | `dtbook.xml` + `timestamps.csv` → `mo0.smil` (đồng bộ text-audio) |
| `gen_opf_ncx.py` | Sinh `book.opf` (metadata 9 trường + manifest), `navigation.ncx`, `resources.res` |
| `validate_daisy.py` | QA tự động: well-formed, id khớp 2 chiều, clip times, manifest, totalTime |
| `package_book.py` | Đóng gói `dist/MSHV.../Tên_sách-Chương N/` gồm `.zip` + `sha256sums.txt` |
| `build_chapter.py` | Orchestrator; khi có dữ liệu thật dùng `--skip-extract --skip-tts` |

Kết quả trung gian nằm ở `build/chapter_NN/`, bản nộp ở `dist/`. Quy ước bàn giao giữa các thành viên: xem `docs/TASKS.md`.

## Liên kết tham khảo

| Tài nguyên | Link |
|-----------|------|
| Slide yêu cầu đồ án | https://docs.google.com/presentation/d/1JJl0Sy5eJnCZ_7IxEMl7jFcWCd-SpePr4qnL7CBc0lA/edit |
| Danh sách tài liệu đã đăng ký (Google Sheets) | https://docs.google.com/spreadsheets/u/0/d/1L4jyXhzCIRdCxh6BBAQ_eWDfz_sKjl4tblFBBB8uYS0/htmlview |
| DAISY Consortium | https://daisy.org/ |
| Tiêu chuẩn DAISY 3 (NISO Z39.86) | https://daisy.org/activities/standards/daisy/daisy-3/ |
| DAISY Pipeline 2 (chuyển đổi định dạng) | https://daisy.org/activities/software/pipeline-2/ |
| Thorium Reader (đọc/phát, Windows/macOS/Linux) | https://thorium.edrlab.org/ |
| Dolphin EasyReader (đọc/phát, Android/iOS/Windows/macOS) | https://yourdolphin.com/EasyReader |
| Amazon Polly (TTS) | https://aws.amazon.com/polly/ |
| Microsoft Azure Neural TTS | https://azure.microsoft.com/en-us/products/ai-services/text-to-speech |
| Google Cloud Text-to-Speech | https://cloud.google.com/text-to-speech |
| Chuẩn SSML (W3C) | https://www.w3.org/TR/speech-synthesis11/ |
| Chuẩn SMIL (W3C) | https://www.w3.org/TR/SMIL3/ |
| Thư viện sách nói Hướng Dương (nguồn audio) | https://thuviensachnoihuongduong.com/ |
