# OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations

**Venue:** CVPR 2025 | **Hạng:** CORE A* | **Năm:** 2025 | **Tác giả/nhóm:** Linke Ouyang, Yuan Qu, Hongbin Zhou, Jiawei Zhu, Rui Zhang, Qunshu Lin, Bin Wang (project lead), ..., Conghui He (corresponding) — Shanghai AI Laboratory (OpenDataLab, nhóm làm MinerU), Abaka AI, 2077AI | **Link:** arXiv 2412.07626v2 (25/03/2025); code & data: https://github.com/opendatalab/OmniDocBench

**Tóm tắt 3 câu:** Bài đề xuất OmniDocBench, benchmark gồm 981 trang PDF thuộc 9 loại tài liệu (có loại sách/book) với hơn 100.000 annotation về layout, nội dung (text/công thức/bảng), thứ tự đọc và 15 nhãn thuộc tính (ngôn ngữ, nền màu, quét mờ, xoay...). Bài xây pipeline đánh giá end-to-end (trích xuất → ghép đoạn → metric) rồi so sánh ba nhóm: pipeline tools (MinerU, Marker, Mathpix), expert VLM (GOT-OCR, Nougat) và general VLM (GPT-4o, Qwen2-VL-72B, InternVL2-76B). Kết luận: pipeline tools mạnh trên tài liệu phổ biến (bài báo, sách, báo cáo), general VLM tổng quát hóa tốt hơn trên trang lạ (notes, slides) và trang quét mờ nhưng kém trên trang dày đặc chữ (báo); hầu hết hệ thống kém trên tiếng Trung hơn tiếng Anh.

## 1. Bài toán & động cơ
Document parsing (trích xuất nội dung có cấu trúc từ trang PDF/ảnh) là đầu vào cho LLM và RAG. Benchmark hiện có bị ba hạn chế: (1) ít đa dạng — chủ yếu bài báo khoa học (Nougat chỉ dùng tài liệu tiếng Anh từ arXiv; benchmark trang của GOT-OCR chỉ 90 trang); (2) metric không phù hợp — dùng Edit Distance/BLEU cho cả bảng và công thức LaTeX/HTML vốn có nhiều cách viết tương đương; (3) thiếu phân tích chi tiết theo loại phần tử hay loại trang. OmniDocBench nhằm so sánh công bằng pipeline và VLM end-to-end ở ba mức: toàn trang, từng tác vụ (layout, OCR, bảng, công thức) và theo thuộc tính.

## 2. Phương pháp
**Thu thập:** >200.000 PDF từ Common Crawl, Google, Baidu và dữ liệu nội bộ → đặc trưng ResNet-50, gom cụm Faiss, lấy 6.000 trang từ 10 tâm cụm → gán thuộc tính thủ công, cân bằng còn **981 trang**.

**9 loại trang:** Book (**104 trang**), Slides (133), Research/Financial Report (81), Colorful Textbook (96), Exam Paper (114), Magazine (97), Academic Literature (129), Notes viết tay (116), Newspaper (111). Có loại "book" riêng.

**Thuộc tính trang (6 nhãn):** loại PDF; layout (Single Column 477, Double 126, Three 45, Mixed 120, Complex 213); ngôn ngữ (English 290, Simplified Chinese 612, Mixed 79); ba "special issue": **Fuzzy Scan (quét mờ, chỉ 28 trang)**, Watermark (65), Colorful Background (246). **Không có thuộc tính "ảnh chụp điện thoại" hay nghiêng góc nhỏ**; xoay chỉ ở mức text block: Normal 22.865, Rotate90 14, Rotate270 58, Horizontal 421 (bảng S4).

**Annotation:** 19 nhóm layout, 15 nhãn thuộc tính (6 trang + 3 text + 6 bảng); text dạng plain text, công thức LaTeX, bảng HTML và LaTeX; có thứ tự đọc và quan hệ caption. Quy trình: tiền gán nhãn tự động (LayoutLMv3, PaddleOCR, UniMERNet, GPT-4o) → annotator sửa từng ký tự → 3 nhà nghiên cứu kiểm tra, dùng render của CDM để bắt phần tử lỗi.

**Pipeline đánh giá (Hình 4):** tiền xử lý Markdown; trích xuất theo thứ tự bảng LaTeX → bảng HTML → công thức display → bảng Markdown → code; phần còn lại là pure text (công thức inline chuyển sang Unicode gộp vào text); **Adjacency Search Match** — tính ma trận Normalized Edit Distance giữa GT và dự đoán, ghép cặp vượt ngưỡng, phần còn lại fuzzy-match và gộp đoạn kề nhau tới khi edit distance không giảm nữa; **ignore logic** — header, footer, số trang, footnote, caption tham gia ghép nhưng không tính điểm.

**Metric:** Text — Normalized Edit Distance (↓); Bảng — TEDS (chuyển về HTML) và Edit Distance; Công thức — CDM, Edit Distance, BLEU; Thứ tự đọc — Normalized Edit Distance trên thành phần text; Layout — mAP.

## 3. Dữ liệu & thiết lập thí nghiệm
981 trang; >20.000 annotation block-level thuộc 15 nhóm (15.979 text paragraph, 989 figure, 428 table), >70.000 span-level (4.009 công thức inline, 357 footnote mark), >16.000 annotation thứ tự đọc; >2.000 block text nền phức tạp, 493 block text xoay; bảng có 150 merged cell, 142 nền màu, 81 chứa công thức, 7 xoay.

Hệ thống (cài đặt mặc định): **Pipeline** MinerU v0.9.3, Marker v1.2.3, Mathpix (thương mại); **Expert VLM** GOT-OCR2.0 (chế độ format), Nougat 0.1.0-base (350M); **General VLM** GPT-4o (2024-08-06), Qwen2-VL-72B (max token 32000), InternVL2-Llama3-76B (max token 4096), do_sample=False. Đơn tác vụ thêm: layout (DiT-L, LayoutLMv3, DocLayout-YOLO...), OCR (PaddleOCR, Tesseract 5, Surya...), bảng (PaddleOCR, RapidTable, StructEqTable...), công thức (UniMERNet-B, Pix2Tex...).

## 4. Kết quả chính
**Bảng 2 — End-to-end (Edit↓, TEDS↑):**

| Nhóm | Phương pháp | Text EN | Text ZH | Table TEDS EN/ZH | Overall EN | Overall ZH |
|---|---|---|---|---|---|---|
| Pipeline | MinerU | **0.061** | **0.215** | 78.6 / 62.1 | **0.150** | 0.357 |
| Pipeline | Marker | 0.080 | 0.315 | 67.6 / 49.2 | 0.336 | 0.556 |
| Pipeline | Mathpix | 0.105 | 0.384 | 77.0 / 67.1 | 0.191 | 0.365 |
| Expert VLM | GOT-OCR | 0.189 | 0.315 | 53.2 / 47.2 | 0.287 | 0.411 |
| Expert VLM | Nougat | 0.365 | 0.998 | 39.9 / 0.0 | 0.452 | 0.973 |
| General VLM | GPT-4o | 0.144 | 0.409 | 72.0 / 62.9 | 0.233 | 0.399 |
| General VLM | Qwen2-VL-72B | 0.096 | 0.218 | 76.8 / 76.4 | 0.252 | **0.327** |
| General VLM | InternVL2-76B | 0.353 | 0.290 | 63.0 / 60.2 | 0.440 | 0.443 |

**Bảng 3 — Text Edit↓ theo loại trang:**

| Phương pháp | **Book** | Textbook | Magazine | Academic | Notes | Newspaper | Overall |
|---|---|---|---|---|---|---|---|
| MinerU | **0.055** | 0.102 | 0.072 | 0.025 | 0.984 | 0.171 | 0.206 |
| Marker | 0.074 | 0.319 | 0.153 | 0.059 | 0.651 | 0.192 | 0.274 |
| Mathpix | 0.131 | 0.216 | 0.147 | 0.091 | 0.634 | 0.690 | 0.300 |
| GOT-OCR | 0.111 | 0.132 | 0.198 | 0.179 | 0.388 | 0.771 | 0.267 |
| Nougat | 0.734 | 0.820 | 0.830 | 0.214 | 0.991 | 0.871 | 0.806 |
| GPT-4o | 0.157 | 0.187 | 0.173 | 0.146 | 0.607 | 0.751 | 0.316 |
| Qwen2-VL-72B | 0.096 | 0.149 | 0.071 | 0.085 | **0.168** | 0.676 | **0.179** |
| InternVL2-76B | 0.216 | 0.184 | 0.150 | 0.419 | 0.226 | 0.903 | 0.300 |

Trên **trang sách**, MinerU tốt nhất (0.055), rồi Marker (0.074) và Qwen2-VL-72B (0.096). MinerU hỏng với notes viết tay (0.984, nhận cả trang thành hình); các VLM hỏng trên báo (Qwen 0.676, GPT-4o 0.751) do giới hạn độ phân giải và token.

**Bảng 4 — Text Edit↓ theo suy giảm thị giác (mean):** Fuzzy scan: Qwen2-VL-72B **0.082**, InternVL2 0.120, MinerU 0.15, GOT-OCR 0.175, GPT-4o 0.263, Mathpix 0.294, Marker 0.333, Nougat 0.934. Watermark: MinerU 0.151, Qwen 0.172, Marker 0.484. Nền màu: Qwen 0.104, MinerU 0.107, Marker 0.319. Trang bình thường (None): Marker 0.062, MinerU 0.079, Qwen 0.084. Marker rớt từ 0.062 xuống 0.333 khi trang mờ; Qwen2-VL gần như không đổi.

**Bảng 8 — OCR subset (Edit↓ theo thuộc tính text):** PaddleOCR tốt nhất tổng thể: EN 0.071, ZH 0.055, Mixed 0.118, Rotate90 0.015, **Rotate270 0.285**, Horizontal 0.021. Tesseract 5 rất kém: EN 0.179, ZH 0.553, Rotate270 0.979. Surya EN 0.057/ZH 0.123; GOT-OCR EN 0.041/ZH 0.112; GPT-4o EN **0.020**/ZH 0.224; Qwen2-VL-72B EN 0.072/ZH 0.274. VLM khó với text xoay và trộn ngôn ngữ. Bảng S2 (end-to-end theo block): MinerU EN 0.124, ZH 0.234, Mixed 0.742 — vì module OCR của MinerU là PaddleOCR, kém khi trộn ngôn ngữ.

**Khác:** thứ tự đọc giảm từ single → multi-column → complex (MinerU 0.101 double, 0.385 complex). Layout: DocLayout-YOLO (19.6M tham số) mAP 47.38, vượt LayoutLMv3 (28.84); trên Book 43.71. Bảng: RapidTable 82.5 TEDS; bảng xoay làm sập hầu hết mô hình (PaddleOCR 23.3, GOT-OCR 8.5). Công thức: GPT-4o 86.8 CDM, Mathpix 86.6, UniMERNet-B 85.0.

## 5. Ưu điểm
- Đa dạng loại trang thực tế (sách, sách giáo khoa, báo, notes) thay vì chỉ arXiv; annotation sửa từng ký tự và có chuyên gia duyệt.
- Ba mức đánh giá chỉ ra điểm yếu cụ thể từng hệ thống (MinerU với notes, VLM với báo).
- Pipeline đánh giá xử lý công bằng khác biệt định dạng đầu ra (ghép đoạn kề, ignore header/footer, chuẩn hóa bảng/công thức).
- Metric chuyên biệt theo loại nội dung (TEDS, CDM); mã nguồn và dữ liệu mở.

## 6. Nhược điểm / hạn chế
- **Không có tiếng Việt**: chỉ English, Simplified Chinese và trộn Anh-Trung; kết luận về tiếng Việt phải ngoại suy (bài không nêu).
- **Không có ảnh chụp điện thoại**: nguồn là trang PDF/scan; gần nhất là "fuzzy scan" (28 trang) và nền màu. Không có nghiêng góc nhỏ, cong trang, bóng, lóa; "rotate" chỉ là 90°/270° với 14 và 58 block — quá ít mẫu.
- Mất cân bằng ngôn ngữ (612 trang Trung / 290 Anh) nên điểm Overall nghiêng về tiếng Trung.
- **Chi phí tính toán**: bài không đo tốc độ, bộ nhớ hay giá; VLM được đánh giá là 72B/76B tham số hoặc API thương mại, không chạy được trên máy không GPU hay điện thoại. Bài chỉ nhận xét định tính rằng pipeline tools nhanh nhờ mô hình nhẹ và song song hóa.
- Nhóm tác giả cũng phát triển MinerU và DocLayout-YOLO nên có thể thiên lệch (bài không bàn).

## 7. Liên hệ với đề tài
- **Chọn OCR engine cho trang sách chụp điện thoại:** kết quả ủng hộ hướng pipeline nhẹ. MinerU đạt Text Edit 0.055 trên Book (tốt nhất) và vẫn ổn khi trang mờ (0.15); ở mức OCR thuần, PaddleOCR tốt nhất (EN 0.071, ZH 0.055), bền với xoay 90° và nền màu, và chính là module OCR bên trong MinerU. Tesseract rất kém mọi điều kiện (EN 0.179, mờ/xoay gần 1.0) nên không dùng làm engine chính dù nhẹ. Với máy không GPU, lựa chọn hợp lý là **PaddleOCR (PP-OCR, có model tiếng Việt) + layout detector nhẹ DocLayout-YOLO (19.6M)** để tách cột và bỏ header/footer; MinerU nếu xử lý phía server. VLM lớn bền hơn với trang mờ nhưng không khả thi về tài nguyên và còn hallucinate trên trang khó (Hình S30); chỉ nên làm fallback qua API khi ảnh quá xấu.
- **Lưu ý thiết kế app:** text xoay 270° làm PaddleOCR rớt từ 0.015 xuống 0.285 → cần tự động xoay/deskew trước OCR; nền màu và watermark hại pipeline nhiều hơn VLM → cần tiền xử lý ảnh (tăng tương phản, nhị phân hóa); sách hai cột hoặc layout phức tạp làm mọi hệ thống giảm mạnh → cần phát hiện cột.
- **Metric nên mượn:** (1) **Normalized Edit Distance** mức trang/đoạn cho text (tính ở mức ký tự, tương đương CER, phù hợp tiếng Việt có dấu); (2) **Adjacency Search Match** + **ignore header/footer/số trang** để so GT–dự đoán không bị phạt vì ngắt đoạn khác nhau — phù hợp vì đầu ra TTS không cần header/footer; (3) báo cáo **theo thuộc tính** (góc nghiêng, độ mờ, ánh sáng, số cột) thay vì một điểm trung bình. Đồ án có thể tự xây một bộ nhỏ kiểu OmniDocBench cho sách tiếng Việt chụp điện thoại.
- **Công cụ:** repo https://github.com/opendatalab/OmniDocBench có code extract/match/metric, chạy được trên Markdown đầu ra của PaddleOCR/MinerU và GT tự gán nhãn.

## 8. Thuật ngữ & số liệu đáng nhớ
- **981 trang, 9 loại, 104 trang Book; >100.000 annotation; 19 nhóm layout, 15 nhãn thuộc tính.**
- Ngôn ngữ: EN 290 / ZH 612 / Mixed 79 — **không có tiếng Việt**; Fuzzy scan chỉ 28 trang.
- Text Edit trên Book: MinerU 0.055 < Marker 0.074 < Qwen2-VL-72B 0.096 < GOT-OCR 0.111 < GPT-4o 0.157.
- Fuzzy scan: Qwen2-VL-72B 0.082, MinerU 0.15, Marker 0.333, Nougat 0.934.
- OCR subset: PaddleOCR EN 0.071 / ZH 0.055; Tesseract EN 0.179 / ZH 0.553; PaddleOCR Rotate270 0.285 (Rotate90 0.015).
- Overall Edit: MinerU 0.150 EN tốt nhất; Qwen2-VL-72B 0.327 ZH tốt nhất.
- DocLayout-YOLO 47.38 mAP / 19.6M tham số; RapidTable 82.5 TEDS; GPT-4o 86.8 CDM.
- Thuật ngữ: Normalized Edit Distance, TEDS, CDM (Character Detection Matching), Adjacency Search Match, ignore handling, pipeline tools / expert VLM / general VLM.
- Nguyên nhân lỗi: VLM — bỏ sót nội dung trang dày, hallucination; pipeline — kém bền với watermark, yếu với notes viết tay.
