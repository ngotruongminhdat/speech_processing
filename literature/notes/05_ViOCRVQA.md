# ViOCRVQA: Novel Benchmark Dataset and VisionReader for Visual Question Answering by Understanding Vietnamese Text in Images

**Venue:** Multimedia Systems 2025 (bản arXiv 2024) | **Hạng:** Q1 (SJR) | **Năm:** 2024 (arXiv 2404.18397v1, 29/04/2024), bản tạp chí 2025 | **Tác giả/nhóm:** Huy Quang Pham, Thang Kien-Bao Nguyen, Quan Van Nguyen, Dan Quang Tran, Nghia Hieu Nguyen, Kiet Van Nguyen (liên hệ), Ngan Luu-Thuy Nguyen – ĐH Công nghệ Thông tin (UIT), ĐHQG TP.HCM | **Link:** https://arxiv.org/abs/2404.18397

**Tóm tắt 3 câu:** Bài giới thiệu ViOCRVQA, bộ dữ liệu OCR-VQA tiếng Việt đầu tiên quy mô lớn gồm 28.282 ảnh **bìa sách** và 123.781 cặp hỏi-đáp về tên sách, tác giả, nhà xuất bản, dịch giả, thể loại, xây dựng bán tự động từ metadata của các trang bán sách trực tuyến. Nhóm đề xuất VisionReader, kiến trúc encoder-decoder (ViT5/BARTpho) ghép đặc trưng đối tượng (VinVL), đặc trưng OCR (SwinTextSpotter) và đặc trưng lưới (ViT), đạt EM 41,16% và F1 69,90% trên tập test, vượt LoRRA, BLIP-2, LaTr, PreSTU. Ablation cho thấy OCR là thành phần quyết định (bỏ OCR làm F1 trường tên sách giảm 45 điểm) và tên sách là trường khó nhất do font chữ lạ, bố cục lộn xộn.

## 1. Bài toán & động cơ

OCR-VQA (Optical Character Recognition – Visual Question Answering) là trả lời câu hỏi dựa trên chữ xuất hiện trong ảnh. Tiếng Anh đã có TextVQA, ST-VQA, OCR-VQA-200k (hơn 200.000 ảnh bìa sách), nhưng tiếng Việt – ngôn ngữ ít tài nguyên (low-resource) – chưa có bộ nào; các bộ VQA tiếng Việt trước (ViVQA, OpenViVQA, UIT-EVJVQA, ViCLEVR) không tập trung vào văn bản trong ảnh. Mục tiêu bài: (1) xây dựng bộ OCR-VQA tiếng Việt lớn nhất, (2) đánh giá các phương pháp SOTA tiếng Anh khi chuyển sang tiếng Việt, (3) đề xuất mô hình khai thác quan hệ đối tượng–văn bản, (4) chứng minh vai trò của hệ thống OCR.

## 2. Phương pháp

**Xây dựng dataset (bán tự động, Hình 2):**
- **Nguồn ảnh:** ảnh bìa sách (book covers) crawl từ web bán sách trực tuyến tại Việt Nam, kèm metadata; chỉ giữ ảnh có chữ tiếng Việt, loại ảnh trùng.
- **Làm sạch:** xoá toàn bộ dấu câu và thông tin không in trên bìa ("tặng kèm", "tái bản 2024") vì metadata hay lệch dấu câu so với bìa thật.
- **Mẫu câu hỏi:** 10 người bản ngữ, mỗi người viết ≥30 câu hỏi cho 5 trường (tác giả, tên sách, NXB, dịch giả, thể loại) → hơn 60 câu/trường, tổng 300 mẫu; ghép ngẫu nhiên với metadata để sinh cặp QA.
- **Kiểm chứng nhãn:** 5 người bản ngữ trả lời độc lập 100 cặp QA/loại; so với nhãn tự động đạt EM trung bình 89,93%, F1 92,07% (Bảng 7).

**Kiến trúc VisionReader (Hình 4):** encoder-decoder Transformer dùng ViT5 (nền T5) hoặc BARTpho (nền BART). Đầu vào encoder `Input = Concat(T, V, V_obj, S_ocr)`: *T* – embedding câu hỏi + văn bản OCR qua lớp token embedding của LM; *V* – grid features từ ViT đóng băng; *V_obj* – VinVL trích đặc trưng vùng 2048 chiều cộng bounding box chuẩn hoá; *S_ocr* – SwinTextSpotter cho đặc trưng detection và recognition (256 chiều mỗi loại) cộng bounding box, ghép nối.

**OCR engine:** SwinTextSpotter [58] (scene text spotting end-to-end, CVPR 2022), dùng cho cả văn bản OCR lẫn đặc trưng OCR; bài nói nó "xử lý tốt tiếng Việt" nhưng không nêu phiên bản hay dữ liệu huấn luyện tiếng Việt.

**Baseline:** LoRRA, LaTr, PreSTU, BLIP-2 – gốc tiếng Anh, được thích nghi sang tiếng Việt; LaTr và PreSTU chỉ fine-tune, không pre-train lại.

## 3. Dữ liệu & thiết lập thí nghiệm

**Loại ảnh:** toàn bộ là **ảnh bìa sách tiếng Việt** dạng ảnh sản phẩm trên web – không phải ảnh chụp điện thoại, không phải trang nội dung sách.

| Thống kê | Train | Dev | Test | Tổng |
|---|---|---|---|---|
| Ảnh | 19.798 | 4.243 | 4.241 | 28.282 |
| Câu hỏi = Câu trả lời | 86.592 | 18.587 | 18.601 | 123.781 |

- Theo trường (Bảng 3): Author 27.881; Title 28.283; Publisher 28.283; Translator 11.051; Genre 28.283.
- Độ đa dạng (Bảng 4): 12.371 tác giả, 26.713 tên sách, 176 NXB, 3.713 dịch giả, 32 thể loại; câu hỏi trung bình 9,64 từ, câu trả lời 7,52 từ; 4,37 câu hỏi/ảnh.
- Thể loại (Phụ lục): Thiếu nhi 31,41% (8.882 cuốn), Giáo khoa – Tham khảo 15,29%, Văn học 12,74%, Tâm lý – Kỹ năng sống 10,02%.
- Ngôn ngữ (Bảng 5–6): hơn 90% câu trả lời là cụm từ (96.612 phrase so với 2.884 từ đơn, 5.683 câu); câu trả lời dài tối đa 55 từ.
- Nhóm độ dài câu trả lời trên test (Bảng 13): ≤5 token 12.637; 6–10: 4.392; 11–15: 1.215; >15: 357.

**Huấn luyện:** Adam, lr 3e-05, dropout 0,2, batch 32, dừng sau 5 epoch không tăng EM; GPU A100 80GB, ~10 giờ/mô hình. Độ đo: Exact Match (EM) và F1 mức token (tách theo khoảng trắng). Genre được thí nghiệm riêng vì thường không in trên bìa.

## 4. Kết quả chính

**Bảng 8 – Tập test (4 trường, không tính genre):**

| Mô hình | Kích thước | EM (%) | F1 (%) |
|---|---|---|---|
| LoRRA | 26M | 10,30 | 21,54 |
| BLIP-2 | 1,4B | 21,45 | 55,23 |
| LaTr | 331M | 30,80 | 60,97 |
| PreSTU | 312M | 33,86 | 66,25 |
| VisionReader + BARTpho | 220M | 31,56 | 64,54 |
| **VisionReader + ViT5** | 315M | **41,16** | **69,90** |

**Theo trường (Bảng 10, VisionReader + ViT5, EM/F1 %):** Title 13,42/64,34; Author 44,19/64,29; Publisher 65,73/85,71; Translator 41,58/58,09. Tên sách khó nhất về EM ở mọi mô hình (LoRRA 3,58; BLIP-2 3,49; LaTr 4,90; PreSTU 9,58) do font lạ, bố cục lộn xộn; NXB dễ nhất vì chỉ 176 giá trị và in rõ ở cuối bìa; tác giả tốt hơn dịch giả vì in chữ lớn hơn.

**Genre (Bảng 9):** VR-ViT5 EM 57,24 / F1 64,41; PreSTU 51,17 / 61,96.

**Ảnh hưởng chất lượng OCR (Mục 7.2, Hình 8):** chia test theo tỷ lệ token đáp án được SwinTextSpotter nhận ra (25/50/75/100%). Hiệu năng tăng theo tỷ lệ này, nhảy vọt ở 100%; **nhưng ngay cả khi OCR nhận đúng 100% token đáp án, EM vẫn dưới 55% và F1 dưới 80%**. Bài không công bố CER/WER độc lập của SwinTextSpotter trên tiếng Việt.

**Bỏ OCR (Bảng 12, ViT5):** Title EM 0,70 (↓12,72), F1 19,29 (↓45,05); Publisher EM 38,20 (↓27,53); Translator F1 15,24 (↓42,85). Kết luận: "cải thiện OCR là cách tốt nhất để tăng hiệu năng".

**Bỏ đối tượng (Bảng 11, ViT5):** Title EM ↓6,61 / F1 ↓15,71; Author EM ↓12,76; Translator EM ↓15,41; riêng Publisher tăng nhẹ (+2,55 EM).

**Độ dài (Mục 7.5):** EM giảm nhanh khi câu trả lời dài lên; F1 ổn định ở nhóm ngắn–dài nhưng kém ở nhóm rất dài (>15 token). Câu hỏi quá ngắn hoặc quá dài đều kém hơn câu hỏi trung bình–dài.

**Kích thước dữ liệu (Mục 7.6):** tăng mạnh 25%→50%, tăng ít 50%→75%, gần bão hoà 75%→100%.

**Dấu thanh:** bài **không nêu** phân tích riêng; chỉ thấy qua ví dụ định tính ở phụ lục ("nhật ký cá sấu" → "nhật ký ca sâu sấu", "sâu sấu tán ca").

## 5. Ưu điểm

- Bộ OCR-VQA tiếng Việt đầu tiên và lớn nhất (28.282 ảnh, 123.781 QA), toàn bộ là bìa sách tiếng Việt.
- Gán nhãn bán tự động nhưng được người kiểm chứng (EM ~90%, F1 ~92%); 300 mẫu câu hỏi bản ngữ đa dạng.
- So sánh 4 baseline SOTA; ablation rõ ràng về OCR, đối tượng, độ dài, kích thước dữ liệu.
- VisionReader 220–315M tham số vượt BLIP-2 1,4B – gợi ý mô hình nhẹ cho tiếng Việt.
- Phân tích theo trường (tên sách/tác giả/NXB/dịch giả) sát nhu cầu "đọc thông tin bìa sách".

## 6. Nhược điểm / hạn chế

- Chỉ có ảnh bìa dạng ảnh sản phẩm web (sạch, chính diện); không có ảnh chụp điện thoại thực tế (nghiêng, mờ, bóng) và không có trang nội dung sách.
- Nhãn từ metadata đã bỏ dấu câu, viết thường (GT "nhà xuất bản kim đồng") nên không phản ánh chính xác chữ in trên bìa.
- Chỉ một OCR engine (SwinTextSpotter), không báo cáo CER/WER hay so với engine khác (FOTS, Mask TextSpotter chỉ nêu ở hướng tương lai).
- Không phân tích lỗi theo dấu thanh/ký tự đặc thù tiếng Việt.
- Cần A100 80GB, ~10 giờ/mô hình; không bàn triển khai trên di động hay CPU.
- Dữ liệu "available on reasonable request"; bài không nêu link GitHub.
- Lỗi trình bày: Bảng 12 ghi nhãn cột Author là F1 hai lần; văn bản ghi nhầm "OCR-ViVQA".

## 7. Liên hệ với đề tài

- **Đánh giá OCR bìa sách cho app:** dùng được như bộ test gián tiếp cho tính năng "đọc tên sách từ bìa": lấy ảnh bìa + đáp án Title/Author/Publisher làm ground truth, chạy OCR của app trên CPU (VietOCR/PaddleOCR/Tesseract) rồi đo token recall / F1 mức token như bài định nghĩa; phải bỏ dấu câu và viết thường trước khi so sánh. Không dùng được cho OCR trang nội dung hay ảnh chụp điện thoại – cần tự chụp bổ sung.
- **OCR engine trong bài:** SwinTextSpotter; kết quả OCR độc lập bài không nêu, nhưng thông điệp cốt lõi là OCR quyết định hiệu năng (bỏ OCR giảm F1 tên sách 45 điểm), và kể cả OCR đúng 100% token thì EM vẫn <55% – nên bước chuẩn hoá văn bản và ghép dòng trong pipeline của đề tài rất quan trọng.
- **Tính năng "đọc tên sách từ bìa":** chụp bìa → OCR → tách tên sách/tác giả/NXB → TTS đọc "Sách ..., tác giả ..., NXB ...". Bài gợi ý: (1) NXB dễ nhất (F1 85,71%) vì vị trí cố định cuối bìa và tập đóng 176 giá trị → dùng từ điển NXB để sửa lỗi OCR; (2) tên sách khó nhất do font nghệ thuật → ưu tiên vùng chữ lớn nhất và cho người dùng xác nhận bằng giọng nói; (3) tên tác giả in lớn hơn dịch giả → heuristic theo kích thước font; (4) toạ độ bounding box hữu ích → nên dùng OCR trả về toạ độ.
- **Mô hình:** VisionReader cần VinVL + SwinTextSpotter + ViT5, quá nặng cho máy không GPU; nên coi bài là nguồn dữ liệu và insight thiết kế. Biến thể rẻ hơn: fine-tune ViT5/BARTpho chỉ với đầu vào văn bản OCR để trích trường tên sách/tác giả.
- **Link GitHub:** bài không nêu (abstract chỉ ghi "link"); liên hệ kietnv@uit.edu.vn.

## 8. Thuật ngữ & số liệu đáng nhớ

- **OCR-VQA**: VQA cần đọc chữ trong ảnh; độ đo **EM** (Exact Match) và **F1 mức token**.
- ViOCRVQA: **28.282 ảnh bìa sách tiếng Việt**, **123.781 cặp QA**, 5 trường; train/dev/test = 19.798/4.243/4.241 ảnh.
- Chất lượng nhãn tự động so với người: EM 89,93%, F1 92,07%.
- VisionReader + ViT5 (315M): **EM 41,16%, F1 69,90%**; PreSTU 33,86/66,25; BLIP-2 (1,4B) 21,45/55,23.
- Theo trường (ViT5): Publisher EM 65,73 / F1 85,71 (dễ nhất); Title EM 13,42 / F1 64,34 (khó nhất).
- Bỏ OCR: F1 Title giảm 45,05 điểm còn 19,29; EM còn 0,70%.
- OCR đúng 100% token đáp án vẫn chỉ cho EM <55%, F1 <80%.
- Thành phần: VinVL (object), SwinTextSpotter (OCR), ViT (grid), ViT5/BARTpho (encoder-decoder).
- >90% câu trả lời là cụm từ, trung bình 7,52 từ; 176 NXB, 32 thể loại, Thiếu nhi 31,41%.
- Huấn luyện: A100 80GB, ~10 giờ/mô hình, lr 3e-05, batch 32.
