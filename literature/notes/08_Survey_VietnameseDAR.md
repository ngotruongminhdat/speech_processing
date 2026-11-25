# A Survey on Vietnamese Document Analysis and Recognition: Challenges and Future Directions

**Venue:** arXiv 2025 (chưa phản biện; arXiv:2506.05061v1 [cs.CV], 5/6/2025) | **Vai trò:** tài liệu nền | **Tác giả/nhóm:** Anh Le, Thanh Lam, Dung Nguyen (Đại học Văn Lang tài trợ) | **Link:** https://arxiv.org/abs/2506.05061

**Tóm tắt 3 câu:** Bài tổng quan phân tích và nhận dạng tài liệu tiếng Việt (Document Analysis and Recognition – DAR), đi từ phương pháp truyền thống (SVM, Tesseract) đến học sâu (BLSTM, attention encoder-decoder, pipeline detection + VietOCR/PaddleOCR) và mô hình ngôn ngữ đa phương thức (Vintern-1B). Bài liệt kê các dataset tiếng Việt hiện có, hai cuộc thi chuẩn hóa (VOHTR 2018 trên VNOnDB, MC-OCR 2021 trên hóa đơn chụp điện thoại) và các kỹ thuật hậu xử lý OCR. Kết luận: dấu thanh phức tạp, thiếu dataset lớn, mô hình kém tổng quát và cộng đồng nghiên cứu nhỏ là rào cản chính; lối ra là dữ liệu tổng hợp, fine-tune VLM và hệ thống Document AI đầu-cuối.

## 1. Bức tranh tổng thể OCR / phân tích tài liệu tiếng Việt

- **Bài toán con:** OCR chữ in, nhận dạng chữ viết tay (online/offline), phân tích bố cục (layout analysis), phân loại tài liệu, trích xuất thông tin chính (KIE), đánh giá chất lượng ảnh (IQA), hậu xử lý sửa lỗi OCR, và VQA trên chữ trong ảnh (ViOCRVQA, ViTextVQA).
- **Hai nhóm tài liệu:** *chữ in* (sách, báo, CCCD, hộ chiếu, hồ sơ) – font và bố cục chuẩn nên dễ hơn nhưng vẫn vướng nhiễu, méo, font đa dạng, nền phức tạp; *chữ viết tay* – biến thiên lớn giữa người viết, cần kiến trúc sequence/attention. Nhiều tài liệu thực tế trộn cả hai.
- **Lịch sử:** Truyền thống – Pham et al. (2008) SVM + đặc trưng thống kê cho ký tự viết tay rời, >90% độ chính xác trên 52.485 mẫu; Phan et al. (2017) trích chữ trên bìa sách bằng tiền xử lý + Sobel + Tesseract tiếng Việt + lọc từ điển; Phan et al. (2016) số hóa chữ Nôm. Học sâu – cuộc thi VOHTR tại ICFHR 2018 (Google, IVTOV, MyScript: BLSTM + CTC + n-gram), mô hình AED của Le et al. (2018, 2020); cuộc thi MC-OCR tại RIVF 2021 (YOLOv5/CRAFT/PAN/PaddleOCR → VietOCR → PICK/PhoBERT/luật). LLM/VLM – Vintern-1B (2024); TrOCR, Donut, dictionary-guided STR được nêu là hướng hứa hẹn.
- **Thách thức đặc thù:** dấu phụ dày đặc, nằm cả trên và dưới ký tự; khác dấu là khác nghĩa ("ma / má / mà"); ranh giới từ không trùng khoảng trắng nên khó tách từ; tài liệu lịch sử (Nôm), viết tay, bản quét kém. Bài ghi rõ Tesseract hỗ trợ tiếng Việt nhưng độ chính xác hạn chế vì dấu và nhiễu.

## 2. Danh mục dataset tiếng Việt

| Dataset | Loại | Kích thước | Năm | Nguồn (theo bài) | Gần đề tài? |
|---|---|---|---|---|---|
| 4,995 Vietnamese OCR Images (Nexdata) | Scene + ảnh internet + **tài liệu**; bbox dòng/cột + transcript | 4.995 ảnh | bài không nêu | GitHub Nexdata-AI | **Có một phần** |
| Vietnamese OCR Image Corpus (DataoceanAI) | **Chữ in** đời thường, bbox mức dòng | 5.006 ảnh | bài không nêu | dataoceanai.com (thương mại) | **Có** |
| VNDoc | **Tài liệu quét bằng điện thoại/máy quét**: pháp lý, hóa đơn, CV; text detection | 226 tài liệu | 2023 | FDSE 2023 [47] | **Có** |
| MC-OCR 2021 | Hóa đơn chụp điện thoại; nhãn dòng + điểm chất lượng ảnh | >2.000 ảnh | 2021 | RIVF 2021 [15] | Gần (ảnh điện thoại mờ/méo) |
| HANDS-VNOnDB | Viết tay online (đoạn, dòng, nét, ký tự) | 1.146 đoạn | 2018 | TC-11 [2] | Không |
| Cinnamon AI Handwriting | Viết tay, nhãn JSON | 1.838 ảnh | bài không nêu | GitHub TomHuynhSG | Không |
| Vietnamese Handwritten OCR (Kaggle) | Ảnh từ viết tay | >110.000 ảnh | bài không nêu | Kaggle | Không |
| UIT-HWDB | Viết tay tổng hợp | bài không nêu | 2022 | RIVF 2022 [41] | Không |
| ViOCRVQA | VQA trên chữ trong ảnh | >28.000 ảnh, >120.000 QA | 2024 | arXiv 2404.18397 | Gián tiếp |
| ViTextVQA, VinText, VnSceneText | VQA / scene text | bài không nêu | bài không nêu | bài không nêu | Không |
| Bộ bìa sách (Phan et al. 2017), CCCD [1], bệnh án [35] | In-house chuyên biệt | bài không nêu | 2017/2021/2023 | [9], [1], [35] | Bìa sách: gần |

Bài **không nêu dataset nào gồm trang sách nội dung tiếng Việt**; gần nhất là VNDoc, DataoceanAI, Nexdata và bộ bìa sách.

## 3. Danh mục phương pháp / công cụ

| Tên | Loại | Kết quả survey nêu | Mã nguồn mở? |
|---|---|---|---|
| Tesseract | OCR engine truyền thống, có tiếng Việt | Kém về dấu và nhiễu; dùng cho bìa sách [9] | Có (bài gọi là open-source) |
| VietOCR (pbcquoc) | Nhận dạng dòng chữ Transformer | 5/6 đội MC-OCR dùng; CER tốt nhất 0,22 (DataMining_VC: YOLOv5 + VietOCR) | Có (GitHub) |
| PaddleOCR / PP-OCR | Detection + recognition siêu nhẹ | Detection trong pipeline SDSV_AICR (RMSE 0,12 / CER 0,23) | Bài không nêu rõ |
| TransformerOCR (CNN + Transformer) | Nhận dạng | Tung-Nguyen, CER 0,32 | Bài không nêu |
| CRAFT, PAN, YOLOv5, Faster R-CNN; MobileNetV3 | Text detection; sửa xoay | Thành phần pipeline MC-OCR | Bài không nêu |
| EfficientNet / VGG-16 regression | IQA | RMSE thấp nhất 0,10 (UIT_CS_AIClub) | Bài không nêu |
| PICK (GCN), PhoBERT, SVM, luật | KIE | Trích trường trên hóa đơn | Bài không nêu |
| BLSTM + CTC + n-gram (Google, IVTOV, MyScript) | Viết tay online | MyScriptTask2_1: CER 1,02% / WER 2,02% mức dòng | Không (thương mại) |
| AED (CNN/DenseNet + attention LSTM) [13,14] | Viết tay offline, không LM | CER 4,67% / WER 13,33% mức dòng | Bài không nêu |
| Hậu xử lý: SLM n-gram + error model [42]; NMT BLSTM [43]; Hill Climbing [44]; LLM tham chiếu ebook [45]; weighting + contextual corrector [46] | Sửa lỗi sau OCR | SLM 4,17 / 9,82; HC 4,13 / 9,47; NMT WER 11,5 (giảm so với AED gốc) | Bài không nêu |
| Vintern-1B | VLM: Qwen2-0.5B-Instruct + InternViT-300M-448px, fine-tune >3 triệu cặp ảnh-hỏi-đáp | Mạnh trên OpenViVQA, ViTextVQA; "tiết kiệm tài nguyên" | Bài không nêu |
| TrOCR, Donut, Dictionary-guided STR | VLM / OCR-free / STR | Chỉ nêu là hướng hứa hẹn | Bài không nêu |
| VietNamese-OCR-DataGenerator, TextRecognitionDataGenerator | Sinh dữ liệu tổng hợp | Nhiều font, script phi Latin | Có (GitHub) |

Kết quả rời: scene text 81,87% (VinText) / 82,56% (VnSceneText) mức từ; CCCD 96,7% ký tự / 89,7% từ; bệnh án viết tay CER 2% / WER 12%; ViOCRVQA EM 0,4116 / F1 0,6990.

## 4. Những thách thức survey chỉ ra

1. **Ngôn ngữ:** dấu phụ trên-dưới ký tự dễ nhận sai (nặng nhất ở scene text); tách từ không dựa được vào khoảng trắng; đồng tự khác thanh gây nhập nhằng.
2. **Dữ liệu:** thiếu dataset lớn, chú thích tốt; dataset chủ yếu in-house, thiên về một loại tài liệu; VNDoc chỉ 226 tài liệu; thiếu đa dạng điều kiện chụp.
3. **Mô hình:** kém tổng quát giữa miền (in → viết tay, ánh sáng khác); chưa có LLM chuyên cho tài liệu tiếng Việt; LLM vướng thiếu dữ liệu tiền huấn luyện ảnh tài liệu và chi phí tính toán cao.
4. **Đánh giá:** thiếu metric và benchmark thống nhất nên khó so sánh.
5. **Cộng đồng:** ít nhà nghiên cứu, thiếu kinh phí, nỗ lực phân mảnh.

## 5. Hướng tương lai survey đề xuất

- Dataset chất lượng cao qua crowdsourcing và **sinh dữ liệu tổng hợp**; benchmark đa loại tài liệu; hợp tác học thuật–công nghiệp (ví dụ ViTextVQA).
- **Fine-tune VLM** cho OCR tiếng Việt; self-supervised và few-shot learning để đối phó thiếu nhãn; mô hình nhẹ kiểu Vintern-1B.
- Tích hợp OCR với **phân tích bố cục** (bảng, biểu mẫu); hệ thống **Document AI đầu-cuối** (OCR + layout + extraction).
- Lập cộng đồng/consortium chuẩn hóa dataset và metric.

## 6. Liên hệ với đề tài

- **Chọn OCR engine:** Tổ hợp được kiểm chứng trên ảnh chụp điện thoại (MC-OCR) là *text detection (PaddleOCR / CRAFT / PAN) → sửa xoay → VietOCR*; VietOCR mã nguồn mở và đạt CER tốt nhất cuộc thi. Tesseract chỉ nên là baseline vì bài nói rõ nó yếu về dấu. Máy không GPU thì PP-OCR ("ultra lightweight") + VietOCR hợp lý hơn VLM; Vintern-1B (~1B tham số) là lựa chọn thử nghiệm VLM nhưng bài không cho số liệu tốc độ trên CPU.
- **Dataset đánh giá:** bài không có bộ trang sách. Có thể (a) dùng VNDoc và Nexdata để đánh giá trên tài liệu in chụp điện thoại; (b) dùng MC-OCR để kiểm tra độ bền với ảnh mờ, méo, thiếu sáng; (c) tự sinh ảnh trang sách bằng VietNamese-OCR-DataGenerator với nhiều font sách; (d) đo CER/WER như Bảng 4 của bài.
- **Thách thức app phải xử lý:** sai dấu thanh → TTS đọc sai nghĩa, nên cần tầng **hậu xử lý sửa lỗi OCR** (n-gram âm tiết, từ điển, hoặc LLM nhỏ) trước TTS; ảnh mờ/nghiêng → cần IQA (như Task 1 MC-OCR) để báo người dùng chụp lại và sửa xoay; bố cục trang (2 cột, chú thích, số trang) → cần layout analysis để đọc đúng thứ tự.
- **Khoảng trống đồ án có thể lấp:** bài không có dataset/benchmark trang sách chụp điện thoại, không bàn OCR phục vụ trợ năng/TTS, không đánh giá chi phí trên thiết bị di động hay CPU. Đồ án có thể đóng góp bộ ảnh trang sách nhỏ có nhãn, so sánh Tesseract / PaddleOCR+VietOCR / VLM nhẹ trên CPU theo CER-WER và độ trễ, và đo tác động lỗi OCR lên chất lượng TTS.

## 7. Thuật ngữ & số liệu đáng nhớ

- **DAR** = Document Analysis and Recognition; **KIE** = Key Information Extraction; **IQA** = Image Quality Assessment; **AED** = attention-based encoder-decoder.
- VOHTR 2018 trên HANDS-VNOnDB (1.146 đoạn): MyScript tốt nhất mức dòng CER 1,02% / WER 2,02%.
- MC-OCR 2021: >2.000 hóa đơn chụp điện thoại, >50 tình nguyện viên; RMSE tốt nhất 0,10; CER tốt nhất 0,22; 5/6 đội dùng VietOCR.
- Hậu xử lý giảm lỗi AED từ CER 4,67 / WER 13,33 xuống 4,13 / 9,47 (Hill Climbing không giám sát).
- Vintern-1B = Qwen2-0.5B-Instruct + InternViT-300M-448px, >3 triệu cặp ảnh-hỏi-đáp.
- ViOCRVQA: >28.000 ảnh, >120.000 cặp hỏi-đáp, EM 0,4116 / F1 0,6990.
- VNDoc: 226 tài liệu quét bằng điện thoại và máy quét.
- Ghi chú độ tin cậy: bài trích ViTextVQA là [36] nhưng [36] thực ra là bài Vintern-1B; bảng dataset của bài không ghi năm, năm ở mục 2 suy từ danh mục tham khảo hoặc ghi "bài không nêu".
