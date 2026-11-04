# ViTextVQA: A Large-Scale Visual Question Answering Dataset and a Novel Multimodal Feature Fusion Method for Vietnamese Text Comprehension in Images

**Venue:** Expert Systems with Applications 2025 (bản arXiv 2024; bản đọc: arXiv:2404.10652v5, 23/02/2026) | **Hạng:** Q1 | **Năm:** 2024–2025 | **Tác giả/nhóm:** Quan Van Nguyen, Dan Quang Tran, Huy Quang Pham, Thang Kien-Bao Nguyen, Nghia Hieu Nguyen, Kiet Van Nguyen (liên hệ), Ngan Luu-Thuy Nguyen – ĐH Công nghệ Thông tin (UIT), ĐHQG TP.HCM | **Link:** https://arxiv.org/abs/2404.10652 ; dataset: https://huggingface.co/datasets/minhquan6203/ViTextVQA

**Tóm tắt 3 câu:** Bài giới thiệu ViTextVQA, bộ dữ liệu VQA dựa trên chữ trong ảnh (text-based VQA) tiếng Việt đầu tiên ở quy mô lớn: 16.762 ảnh, 50.342 cặp hỏi–đáp, câu trả lời bắt buộc là chuỗi chữ có trong ảnh. Nhóm đề xuất ViTextBLIP-2 (chỉ tinh chỉnh Q-Former, ≈5% tham số) kết hợp ViT, OCR SwinTextSpotter, caption Qwen2-VL và LLM ViT5, đạt F1 53,95% / EM 25,48%, vượt các baseline M4C, BLIP-2, LaTr, SaL, PreSTU. Phân tích cho thấy chất lượng OCR, thứ tự token OCR (trên-trái → dưới-phải, TL-BR), dấu thanh và tách từ tiếng Việt đều ảnh hưởng mạnh đến kết quả.

## 1. Bài toán & động cơ
- Bài toán: trả lời câu hỏi tiếng Việt về chữ xuất hiện trong ảnh (scene text VQA); mô hình vừa phải "đọc" chữ (OCR) vừa hiểu ngữ cảnh ảnh để chọn đúng đoạn chữ làm đáp án.
- Động cơ: các bộ VQA tiếng Việt trước đó đều thiếu – ViVQA (15.000 mẫu bán tự động, không có scene text), OpenViVQA (11.199 ảnh, 37.914 QA, chỉ ~một nửa mẫu có chữ, câu trả lời tự do khó chấm), ViOCRVQA (~30.000 ảnh bìa sách, >120.000 QA, không có scene text ngoài đời).
- Đóng góp: dataset gán nhãn thủ công, mô hình ViTextBLIP-2 nhẹ về huấn luyện, và phân tích hệ thống về thứ tự OCR, dấu thanh, tách từ.

## 2. Phương pháp
**Xây dựng dataset:** thu thập >40.000 ảnh từ Google Images, Facebook, Pinterest (crawl bằng Selenium theo từ khóa thành phố như "bảng hiệu ở Thành phố Hồ Chí Minh", "khu du lịch ở Hội An") và chụp tay; lọc bằng SwinTextSpotter giữ >22.000 ảnh giàu chữ tiếng Việt; chọn ~16.000 ảnh để gán nhãn.

**Gán nhãn:** 16 sinh viên, huấn luyện trên 100 ảnh mẫu, mỗi người ≥600 QA/subset, 1 giám sát viên cho 4 người, kéo dài 6 tuần. Quy tắc (Phụ lục A): câu hỏi phải trả lời được bằng chữ trong ảnh; không hỏi yes/no, vị trí, màu, đếm, toán; tối đa 10 QA/ảnh; đáp án chỉ gồm chữ trong ảnh, viết thường, "nếu chữ có xuống dòng thì thay bằng dấu cách", phần bị che chỉ ghi phần nhìn thấy. Độ đồng thuận (IAA) đo bằng F1 token, ngưỡng >70%: trung bình 81,83% → 85,34% (min 73,91 → 83,36). Chia train/dev/test 7:1:2.

**ViTextBLIP-2:** ViT (đóng băng) trích đặc trưng ảnh; SwinTextSpotter cho token và embedding OCR; Qwen2-VL sinh caption; Q-Former khởi tạo từ BLIP-2 (thành phần duy nhất được tinh chỉnh) hợp nhất ảnh + OCR; ViT5 nhận Q, câu hỏi, token OCR và caption để sinh đáp án. Tổng ≈2,5B tham số, tinh chỉnh ≈5%.

**Baseline (Bảng 5):** M4C (VinVL + mBERT-cased), SaL (VinVL + ViT5), BLIP-2, LaTr, PreSTU (ViT + ViT5); tất cả dùng chung OCR SwinTextSpotter. LLM đóng (GPT-4o, Gemini 1.5 Flash, Qwen2-VL-7B) thử 0/1/3/5-shot.

**OCR engine:** SwinTextSpotter (Swin Transformer, phát hiện + nhận dạng end-to-end), checkpoint công khai **không fine-tune thêm**, chỉ cấu hình decoder với bộ ký tự tiếng Việt và "diacritic-aware settings" (Phụ lục B).

## 3. Dữ liệu & thiết lập thí nghiệm
- 16.762 ảnh, 50.342 QA (so sánh: TextVQA 28.408 ảnh/45.336 câu; DocVQA 12.767/50.000; OpenViVQA 11.199/21.271).
- Câu hỏi 3–31 token, trung bình 9,59; đáp án 1–52 token, trung bình 4,18.
- Loại ảnh: cảnh đời thường Việt Nam – bảng hiệu, menu, nhãn sản phẩm, đường phố. Đối tượng (VinVL): "person" >47.000, "sign" 43.000, "letter" 36.000, "motorbike" ~9.000 (gấp 3 "car"). **Ảnh trang sách/tài liệu quét: bài không nêu**; dataset thuần scene text.
- Tập test (Bảng 9): 7.853 đáp án ≤5 token, 1.541 từ 6–10, 421 từ 11–15, 213 >15.
- Thiết lập: RTX 4090 24GB, Adam, 10 epoch, lr 3×10⁻⁵, dropout 0,2, batch 16, weight decay 10⁻⁴; 6–7 h (base), 9–10 h (large). Metric: Exact Match (EM) và F1 token.

## 4. Kết quả chính
**Bảng 6 – tập test ViTextVQA:**

| Mô hình | Phiên bản | Kích thước | % tinh chỉnh | F1 (%) | EM (%) |
|---|---|---|---|---|---|
| M4C | base | ≈140M | ≈100 | 25,46 | 10,26 |
| BLIP-2 | base / large | ≈450M / 1,4B | ≈25 / ≈8 | 36,87 / 38,47 | 13,59 / 15,58 |
| LaTr | base / large | ≈330M / 900M | ≈100 | 40,41 / 42,34 | 17,85 / 20,94 |
| SaL | base / large | ≈270M / 780M | ≈100 | 43,49 / 43,39 | 20,11 / 21,48 |
| PreSTU | base / large | ≈315M / 860M | ≈100 | 43,81 / 44,93 | 20,85 / 22,64 |
| **ViTextBLIP-2** | base | ≈2,5B | ≈5 | **53,95** | **25,48** |

**Bảng 7 (100 mẫu):** GPT-4o 3-shot F1 76,67 / EM 56,00; Gemini-1.5-flash 5-shot 64,40 / 39,00; Qwen2-VL-7B ≈54–55 F1; ViTextBLIP-2 56,43 / 26,00; **con người 96,42 / 88,00**. **Bảng 8 (OpenViVQA):** CIDEr 3,2129 / BLEU 0,4717 (M4C 1,5073 / 0,2941).

**Phân tích liên quan OCR và tiếng Việt:**
- Độ phủ token OCR (<25, 25–50, 50–75, 75–100, 100%): F1 tăng theo độ phủ, nhưng **ngay cả khi OCR phủ 100% token đáp án, F1 tốt nhất vẫn <60 và EM <35**. Bài **không báo cáo CER/WER hay độ chính xác trực tiếp của SwinTextSpotter**; tỉ lệ từng nhóm chỉ ở Hình 12 (bài không nêu số).
- Kích thước chữ: F1 tăng đều từ chữ nhỏ (<1% diện tích ảnh) → vừa (1–5%) → lớn (>5%).
- **Thứ tự OCR (Bảng 10, 13):** trung bình 10 mô hình – gốc F1 40,62 / EM 18,45; sắp theo độ tin cậy 39,04 / 17,30 (giảm); **TL-BR 42,81 / 19,83**. M4C hưởng lợi nhất (+4,58 F1). Số từ ghép tách được bằng VnCoreNLP tăng 0,56 → 1,06 từ/mẫu với TL-BR.
- **Dấu thanh (mục 7.1, Hình 18):** xóa dấu 0/25/50/75/100% làm F1 giảm đơn điệu ở mọi mô hình; EM sụt mạnh nhất ở mức 50%; LaTr và SaL nhạy nhất ngay từ 0→25%. Bài chỉ cho đồ thị, **không nêu con số**.
- **Ablation (Bảng 12):** đủ 3 thành phần 52,51 / 24,83; bỏ caption −13,37 F1; bỏ OCR −12,98 F1; chỉ Image Encoder 14,17 / 4,69.

## 5. Ưu điểm
- Dataset lớn, gán nhãn thủ công có kiểm soát (IAA >80%), công khai trên HuggingFace; đáp án là chữ trong ảnh nên chấm bằng EM/F1 khách quan.
- Mọi mô hình dùng cùng một OCR → so sánh công bằng.
- Phân tích đặc thù tiếng Việt (độ phủ OCR, cỡ chữ, thứ tự OCR, dấu thanh, tách từ) rất hữu ích cho người xây pipeline OCR tiếng Việt.
- ViTextBLIP-2 chỉ tinh chỉnh ≈5% tham số, chi phí huấn luyện thấp.

## 6. Nhược điểm / hạn chế
- Không đánh giá độc lập chất lượng OCR (không CER/WER, không so với VietOCR/PaddleOCR/Tesseract); OCR không fine-tune tiếng Việt.
- Chỉ scene text, không có trang sách/tài liệu; chữ in dày đặc nhiều dòng gần như vắng mặt.
- Số liệu dấu thanh chỉ ở dạng đồ thị; mục 7.1 viết "5 dấu thanh" trong khi tiếng Việt có 6 thanh (kể cả thanh ngang).
- Mâu thuẫn nội bộ: Bảng 6 ghi 53,95/25,48 nhưng Bảng 10 đặt con số này ở cột "OCR Confidence", còn TL-BR (đánh dấu là cấu hình gốc) chỉ 52,51/24,83 – trùng ablation. Kết luận viết "vượt baseline với biên 53,95% F1" là nhầm giá trị tuyệt đối với mức chênh.
- Bảng 7 chỉ 100 mẫu, phương sai lớn. ViTextBLIP-2 cần Qwen2-VL sinh caption → nặng, không chạy nổi trên CPU/di động. Không có link GitHub mã nguồn; "Data Availability" ghi "on request" dù có link HuggingFace.

## 7. Liên hệ với đề tài
- **Dùng để đánh giá OCR cho app?** Chỉ một phần. Ảnh là cảnh đường phố, không phải trang sách; đáp án là đoạn chữ ngắn (TB 4,18 token), không có transcript toàn ảnh nên không tính được CER/WER. Có thể dùng làm "stress test" phụ cho OCR trên ảnh chụp điện thoại thực tế (font lạ, nghiêng, mờ) bằng cách đo tỉ lệ token đáp án xuất hiện trong đầu ra OCR, như mục 6.1. Đánh giá OCR trang sách cần bộ khác (ảnh sách tự chụp + transcript).
- **OCR engine của bài:** SwinTextSpotter, checkpoint công khai, decoder cấu hình bộ ký tự tiếng Việt. Bài không công bố độ chính xác OCR, chỉ cho thấy F1 VQA tăng theo độ phủ OCR. Với máy không có GPU CUDA, SwinTextSpotter không phù hợp để triển khai; nên coi bài là bằng chứng về tầm quan trọng của OCR hơn là gợi ý engine.
- **Bài học về dấu thanh:** mất dấu làm F1 giảm đơn điệu → lỗi dấu từ OCR (ví dụ "má"/"mà") sẽ truyền thẳng sang TTS và đọc sai nghĩa. Bước chuẩn hóa văn bản cần: chuẩn hóa Unicode NFC, kiểm tra/khôi phục dấu, tuyệt đối không bỏ dấu khi tiền xử lý.
- **Bài học về khoảng trắng và thứ tự đọc:** khoảng trắng tiếng Việt tách âm tiết, không tách từ; sắp token OCR theo thứ tự đọc tự nhiên (TL-BR) tăng từ ghép tách được 0,56 → 1,06 và F1 trung bình +2,19 điểm, còn sắp theo độ tin cậy làm giảm. App phải nhóm box OCR thành dòng/đoạn theo thứ tự đọc (kể cả 2 cột, chú thích) trước khi đưa vào TTS. Quy tắc "xuống dòng thay bằng dấu cách" cũng gợi ý cách nối dòng khi chuẩn hóa.
- **Link:** dataset https://huggingface.co/datasets/minhquan6203/ViTextVQA ; GitHub: bài không nêu.

## 8. Thuật ngữ & số liệu đáng nhớ
- **ViTextVQA:** 16.762 ảnh, 50.342 QA, chia 7:1:2, 16 người gán nhãn/6 tuần, IAA F1 TB 85,34%.
- **Text-based VQA:** đáp án bắt buộc là chữ trong ảnh; metric EM và F1 token.
- **SwinTextSpotter:** OCR end-to-end dùng chung cho mọi mô hình; không fine-tune, chỉ cấu hình bộ ký tự tiếng Việt.
- **ViTextBLIP-2:** ViT + SwinTextSpotter + Qwen2-VL caption + Q-Former + ViT5; ≈2,5B tham số, tinh chỉnh ≈5%; F1 53,95 / EM 25,48.
- **TL-BR ordering:** F1 TB 40,62 → 42,81; sắp theo confidence giảm còn 39,04.
- **OCR token coverage:** OCR phủ 100% đáp án vẫn chỉ F1 <60, EM <35.
- **Diacritics:** xóa dấu 25–100% làm F1 giảm đơn điệu; LaTr, SaL nhạy nhất.
- **Word segmentation (VnCoreNLP):** 0,56 → 1,06 từ ghép/mẫu với TL-BR.
- **Người vs LLM (100 mẫu):** người 96,42 F1 / 88,00 EM; GPT-4o 3-shot 76,67 / 56,00.
