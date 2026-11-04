# Kế hoạch thực hiện đồ án

**Đề tài:** Ứng dụng đọc sách tiếng Việt cho người khiếm thị trên thiết bị di động
**Hướng chọn:** Ứng dụng (3b) — web/app chạy được
**Ràng buộc máy dev:** không có CUDA → mô hình chạy CPU hoặc API; việc nặng GPU làm trên Colab/Kaggle

Thời lượng ước tính tổng: ~7 tuần. Các stage 1 và 2 có thể chạy song song.

```
Stage 0 ──► Stage 1 (Lit review) ─────────────────────┐
        └─► Stage 2 (Demo) ──► Stage 3 (App) ──► Stage 4 (Cải tiến) ──► Stage 5 (Báo cáo)
```

---

## Stage 0 — Khởi tạo  ✅ (04/11/2026)

- [x] Branch `final_project`, khung thư mục, README
- [x] Tải 8 PDF, lập danh sách bài báo
- [x] Kiểm tra môi trường (CPU 16 nhân, 62 GB RAM, không CUDA)

---

## Stage 1 — Tổng quan tài liệu (30%) · ~1.5 tuần  ✅ bản nháp xong 04/11/2026

**Mục tiêu:** 6 bài tóm tắt + 1 bảng so sánh + 1 phần "trong nước".

| Bước | Việc | Đầu ra |
|---|---|---|
| ✅ 1.1 | Đọc survey Vietnamese DAR (bài 8) để nắm bức tranh OCR tiếng Việt | `notes/08_survey.md` (ghi chú ngắn) |
| ✅ 1.2 | Đọc và tóm tắt 3 bài TTS: PhoAudiobook, F5-TTS, MobileSpeech | `notes/01..03_*.md` theo khung 7 mục |
| ✅ 1.3 | Đọc và tóm tắt 2 bài OCR tiếng Việt: ViTextVQA, ViOCRVQA | `notes/04..05_*.md` |
| ✅ 1.4 | Đọc và tóm tắt @BENCH (trợ năng) | `notes/06_*.md` |
| ✅ 1.5 | Khảo sát giải pháp trong nước: VLSP TTS, FPT.AI, Viettel, Zalo TTS, VietOCR, app hiện có (Be My Eyes, Envision, Seeing AI – hỗ trợ tiếng Việt tới đâu) | `notes/10_vietnam_landscape.md` |
| ✅ 1.6 | Bảng so sánh chéo: bài toán / phương pháp / dữ liệu / metric / ưu / nhược / dùng được gì | `notes/20_comparison.md` |
| ✅ 1.7 | Rút ra **khoảng trống nghiên cứu** → câu chuyện cho báo cáo | mục cuối `20_comparison.md` |

**Tiêu chí xong:** mỗi bài có đủ 7 mục, mục "liên hệ với đề tài" viết cụ thể (dùng mô hình nào, dữ liệu nào, ý tưởng UI nào).

---

## Stage 2 — Demo pipeline (20%) · ~1 tuần

**Mục tiêu:** chạy end-to-end ảnh → text → audio trên máy dev, có số liệu.

| Bước | Việc | Công cụ |
|---|---|---|
| 2.1 | Cài môi trường vào `.venv`: paddleocr (CPU), paddlepaddle, pillow, opencv, fastapi, soundfile | `demo/requirements.txt` |
| 2.2 | Tạo tập test 20–30 ảnh trang sách tiếng Việt: chụp điện thoại (thẳng, nghiêng, thiếu sáng) + render từ PDF sách miễn phí | `demo/data/pages/` + `gt/*.txt` ground truth |
| 2.3 | OCR baseline: Tesseract vie vs PaddleOCR det + VietOCR rec vs PaddleOCR det + PP-OCRv5 rec (kiểm tra từ điển PP-OCRv5 có dấu tiếng Việt không); đo CER/WER, thời gian/trang | `demo/ocr_eval.py`, `demo/outputs/ocr_results.csv` |
| 2.4 | Chuẩn hóa văn bản: số, ngày, viết tắt, ngắt câu (VietNormalizer hoặc tự viết rule) | `demo/normalize.py` |
| 2.5 | TTS: (a) VieNeu-TTS chạy CPU, (b) F5-TTS checkpoint tiếng Việt (zalopay/hynt), (c) API FPT.AI; đo RTF, nghe thử 10 câu | `demo/tts_eval.py` |
| 2.6 | Script end-to-end `demo/run_pipeline.py image.jpg → out.wav` | notebook `demo/demo.ipynb` để trình chiếu |

**Tiêu chí xong:** 1 lệnh chạy ra audio; bảng CER/WER + RTF cho ≥2 OCR và ≥2 TTS.

**Rủi ro:** F5-TTS trên CPU có thể >10 s/câu → nếu quá chậm, dùng API làm engine chính của app, F5-TTS chỉ để so sánh.

---

## Stage 3 — Ứng dụng chạy được (30%) · ~2 tuần

**Kiến trúc:** Mobile client (Flutter) ↔ Backend FastAPI (OCR + normalize + TTS) trên máy dev / VPS.

### 3A — Backend (tuần 1)
| Bước | Việc |
|---|---|
| 3.1 | FastAPI: `POST /ocr` (ảnh → text + bbox), `POST /tts` (text → wav/mp3, stream theo câu), `POST /read` (ảnh → audio, gộp) |
| 3.2 | Tiền xử lý ảnh: xoay đúng chiều, khử nghiêng, cắt viền, tăng tương phản |
| 3.3 | Cache audio theo hash câu; chia câu để phát sớm câu đầu trong khi câu sau đang sinh |
| 3.4 | Dockerfile + test bằng curl |

### 3B — Mobile client (tuần 2)
| Bước | Việc |
|---|---|
| 3.5 | Cài Flutter, tạo project `app/mobile/`, test trên Android thật |
| 3.6 | Màn hình chính **tối giản, toàn màn hình là nút lớn**: chạm 1 lần = chụp & đọc; vuốt trái/phải = câu trước/sau; chạm đúp = tạm dừng/tiếp; giữ = đổi tốc độ |
| 3.7 | Phản hồi phi thị giác: rung khi chụp, âm báo khi OCR xong, đọc to trạng thái lỗi |
| 3.8 | Tương thích TalkBack: semantic label cho mọi widget, kiểm tra bằng TalkBack bật |
| 3.9 | Thư viện sách: lưu text + audio đã đọc, mở lại không cần OCR |
| 3.10 | Chế độ đọc tài liệu dài: chụp nhiều trang → ghép → đọc liên tục |

**Tiêu chí xong:** cài APK lên điện thoại, người bịt mắt dùng được luồng chụp → nghe → chuyển câu mà không nhìn màn hình.

**Rủi ro:** chưa có Flutter → dự phòng là PWA (React, dùng được Node 20 sẵn có) chạy trên trình duyệt điện thoại, mất tính năng rung nhưng vẫn demo được.

---

## Stage 4 — Phân tích sâu & cải tiến (20%) · ~1.5 tuần

Chọn **một** trong hai, quyết định sau khi có số liệu Stage 2:

### Lựa chọn A — Cải thiện OCR cho trang sách chụp điện thoại (ưu tiên nếu CER baseline > 5%)
| Bước | Việc |
|---|---|
| 4.1 | Phân tích lỗi: nhóm theo loại (sai dấu thanh, mất dòng, nghiêng, bóng, chữ nhỏ) |
| 4.2 | Cải tiến tiền xử lý: deskew + khử bóng (adaptive threshold) + upscale |
| 4.3 | Hậu xử lý sửa lỗi bằng mô hình ngôn ngữ tiếng Việt nhỏ (ViT5/BARTpho) hoặc từ điển + n-gram |
| 4.4 | Ablation nhỏ: baseline → +tiền xử lý → +hậu xử lý; báo CER/WER từng bước |

### Lựa chọn B — Nâng chất lượng TTS đọc sách (ưu tiên nếu OCR đã tốt)
| Bước | Việc |
|---|---|
| 4.1 | Fine-tune F5-TTS trên PhoAudiobook (subset ~50 h) trên Colab/Kaggle GPU |
| 4.2 | So sánh checkpoint gốc vs fine-tune: MOS (10 người nghe), độ đúng dấu thanh, RTF |
| 4.3 | Chuẩn hóa văn bản chuyên cho sách: số chương, chú thích, hội thoại, ngắt nghỉ |
| 4.4 | Tích hợp bản tốt nhất vào backend |

**Tiêu chí xong:** có bảng số liệu trước/sau, có giải thích vì sao cải tiến hoạt động (hoặc không).

---

## Stage 5 — Báo cáo & trình bày · ~1 tuần

| Bước | Việc | Đầu ra |
|---|---|---|
| 5.1 | Viết báo cáo theo rubric 4 phần + phần giới thiệu/kết luận | `report/report.pdf` (LaTeX hoặc docx) |
| 5.2 | Slide 15–20 trang | `report/slides.pdf` |
| 5.3 | Video demo 2–3 phút quay trên điện thoại thật | `report/demo.mp4` |
| 5.4 | Dọn repo: README hướng dẫn chạy backend + cài app, requirements đầy đủ | README |
| 5.5 | Tập trình bày, chuẩn bị câu hỏi phản biện (vì sao không on-device? độ trễ? quyền riêng tư ảnh?) | `report/qa.md` |

---

## Lịch gợi ý

| Tuần | Stage | Mốc |
|---|---|---|
| 1 | 1.1–1.4 + 2.1–2.3 | Xong 6 tóm tắt nháp, OCR baseline có số |
| 2 | 1.5–1.7 + 2.4–2.6 | Lit review hoàn chỉnh, demo chạy 1 lệnh |
| 3 | 3A | Backend chạy, test bằng curl |
| 4 | 3B | APK cài được, luồng chính dùng được |
| 5 | 3.9–3.10 + chọn hướng Stage 4 | App đủ tính năng; bắt đầu cải tiến |
| 6 | Stage 4 | Có bảng trước/sau |
| 7 | Stage 5 | Báo cáo, slide, video |

## Nguyên tắc làm việc

- Mỗi stage xong → commit, cập nhật checklist trong file này.
- Số liệu luôn lưu dạng CSV trong `demo/outputs/` hoặc `report/tables/` để báo cáo lấy trực tiếp.
- Mọi quyết định thiết kế (chọn OCR nào, TTS nào, vì sao) ghi vào `report/decisions.md` ngay lúc quyết định.
