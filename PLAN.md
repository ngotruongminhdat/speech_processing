# Kế hoạch thực hiện đồ án

**Đề tài:** Ứng dụng đọc sách tiếng Việt cho người khiếm thị trên thiết bị di động
**Hướng chọn:** Ứng dụng (3b) — web app chạy trên điện thoại
**Sản phẩm:** Sách Nói, thư viện sách nói DAISY — https://ngotruongminhdat.github.io/speech_processing/

## Thay đổi hướng (05/11/2026)

Kế hoạch ban đầu (04/11) đặt trọng tâm vào OCR sách giấy. Sau khi xem lại đồ án giữa kỳ, hướng được đổi thành **kế thừa giữa kỳ**: giữa kỳ tạo ra sách nói DAISY, cuối kỳ làm ứng dụng để người khiếm thị nghe những cuốn sách đó trên điện thoại. OCR chuyển thành phần mở rộng, không còn là lõi.

```
Giữa kỳ:   EPUB ──► văn bản ──► TTS ──► DAISY 3 (một cuốn, trang web từng chương)
Cuối kỳ:   nhiều nguồn sách ──► TTS chạy cục bộ ──► DAISY 3 + mốc từng câu ──► thư viện trên điện thoại
```

Ràng buộc máy dev: không có CUDA → mọi mô hình phải chạy được trên CPU.

---

## Stage 0 — Khởi tạo ✅

- [x] Branch `final_project`, khung thư mục, kiểm tra môi trường

## Stage 1 — Tổng quan tài liệu (30%) · bản nháp ✅, cần chỉnh theo hướng mới

- [x] 8 ghi chú bài báo, khảo sát trong nước, bảng so sánh (`literature/notes/`)
- [ ] **Thay 2 bài OCR** (ViTextVQA, OmniDocBench) bằng bài về: đồng bộ văn bản với âm thanh (forced alignment), TTS nhẹ chạy trên thiết bị (VITS, là kiến trúc của Piper), chuẩn hóa văn bản tiếng Việt cho TTS. Giữ ViOCRVQA làm phần mở rộng "đọc bìa sách".
- [ ] Viết lại `20_comparison.md` mục khoảng trống: nhấn vào (1) sách nói tiếng Việt có điều hướng cho người khiếm thị, (2) TTS tiếng Việt chạy CPU chưa được đo, (3) đồng bộ mức câu.
- [ ] Rút mỗi ghi chú còn khoảng 1 trang cho báo cáo.

## Stage 2 — Demo (20%) · phần lõi ✅

- [x] Chạy lại pipeline giữa kỳ, tổng quát hóa cho nhiều sách (`pipeline/scripts/`)
- [x] So sánh TTS trên cùng 22 đoạn của "Lão Hạc": tốc độ trên CPU và độ rõ qua ASR (`report/tts_comparison.md`)
- [ ] Thêm 1–2 engine vào bảng so sánh: VieNeu-TTS, F5-TTS tiếng Việt
- [ ] Nghe thử có chấm điểm (MOS) với 5–10 người

## Stage 3 — Ứng dụng chạy được (30%) · bản đầu ✅ đã deploy

- [x] Thư viện nhiều sách, trang bìa từng cuốn, trình phát đồng bộ từng câu (`app/web/`)
- [x] Trợ năng: nhãn cho mọi nút, vùng thông báo, focus theo màn hình, phím tắt, nền tương phản cao, cỡ chữ
- [x] Di động: thanh phát hai hàng nút lớn, điều khiển ở màn hình khóa (Media Session), cài lên màn hình chính (PWA)
- [x] Nhớ vị trí từng cuốn, nghe tiếp, hẹn giờ tắt, lưu sách nghe ngoại tuyến
- [x] 46 kiểm thử đầu-cuối bằng Chromium (`app/tests/e2e.py`)
- [x] Deploy dần từng chương, từng cuốn (`pipeline/scripts/deploy_site.py`)
- [ ] **Thử với TalkBack và VoiceOver trên điện thoại thật** — kiểm thử tự động không thay được bước này
- [ ] Thử với người dùng khiếm thị (hoặc bịt mắt), ghi lại số thao tác và thời gian tới khi nghe được
- [ ] Tìm kiếm bằng giọng nói; đánh dấu trang

## Stage 4 — Phân tích sâu và cải tiến (20%)

Giải pháp được chọn để phân tích: **TTS VITS/Piper cho sách nói tiếng Việt**. Đã có số liệu nền (nhanh gấp 27–40 lần thời gian thực trên CPU, WER 10,0% so với 5,3% của edge-tts). Các hướng cải tiến, xếp theo giá trị trên công sức:

- [ ] **Chuẩn hóa văn bản trước TTS**: số, ngày tháng, số La Mã, viết tắt, từ nước ngoài. Đo WER trước và sau trên các câu có số.
- [ ] **Ngắt nghỉ theo dấu câu và hội thoại**: hiện câu thoại ngắn ("Vâng!") chỉ dài 0,2 giây. Thử thêm khoảng lặng, đo lại.
- [ ] **Tốc độ đọc**: hiện 245 âm tiết/phút, cao hơn mức 201 của PhoAudiobook. Thử `length_scale` 1,1–1,2.
- [ ] **Phân tích lỗi của Piper**: từ nào ASR nghe sai, có tập trung ở thanh điệu nào không.
- [ ] (Nếu có GPU trên Colab) fine-tune giọng Piper trên dữ liệu sách nói.

## Stage 5 — Báo cáo và trình bày

- [ ] Báo cáo theo 4 mục chấm điểm; ghi rõ phần kế thừa giữa kỳ và phần làm mới
- [ ] Slide, video demo quay trên điện thoại thật
- [ ] Câu hỏi phản biện dự kiến: vì sao web mà không phải app gốc, chất lượng giọng Piper, bản quyền sách

---

## Lệnh thường dùng

```bash
# thêm một cuốn sách thuộc phạm vi công cộng
python3 pipeline/scripts/import_wikisource.py --slug <slug> --author "<tác giả>" --year <năm> "<tên trang Wikisource>"
.venv/bin/python pipeline/scripts/build_book.py <slug> [--only 1-9]

# deploy (chạy lại mỗi khi xong thêm chương hoặc sách)
python3 pipeline/scripts/deploy_site.py

# thử trên máy
python3 pipeline/scripts/build_site.py && python3 app/tests/serve.py 8931 &
.venv/bin/python app/tests/e2e.py http://127.0.0.1:8931/
```
