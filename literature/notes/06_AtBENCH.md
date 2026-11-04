# @BENCH: Benchmarking Vision-Language Models for Human-centered Assistive Technology

**Venue:** WACV 2025 | **Hạng:** CORE A | **Năm:** 2025 | **Tác giả/nhóm:** Xin Jiang*, Junwei Zheng*, Ruiping Liu, Jiahang Li, Jiaming Zhang (liên hệ), Sven Matthiesen, Rainer Stiefelhagen – Karlsruhe Institute of Technology (KIT) & Li Auto Inc. | **Link:** CVF Open Access, WACV 2025, tr. 3934–3943; mã nguồn "sẽ công bố tại ATBench" (bài không nêu URL cụ thể)

**Tóm tắt 3 câu:** Bài đặt câu hỏi "VLM đã sẵn sàng cho công nghệ hỗ trợ (Assistive Technology, AT) người khiếm thị chưa?" và trả lời bằng benchmark @BENCH gồm 5 nhiệm vụ do chính người khiếm thị (People with Visual Impairments, PVIs) xếp hạng qua khảo sát human-in-the-loop. Nhóm đề xuất @MODEL – mô hình generalist 62M tham số dựa trên X-Decoder, dùng task-specific prompt để làm cả 5 nhiệm vụ với một bộ trọng số. Kết quả: nhận dạng chữ (OCR) là nhu cầu số một của PVIs, @MODEL cạnh tranh với mô hình chuyên biệt không pre-train, nhưng OCR giảm rõ khi huấn luyện đa nhiệm.

## 1. Bài toán & động cơ

Các hệ thống AT trước đây chỉ làm một vài chức năng riêng lẻ (dẫn đường, tránh vật cản, mô tả ảnh) và khó xử lý đồng thời nhiều nhiệm vụ. VLM generalist (OFA, Unified-IO, X-Decoder) hứa hẹn khắc phục, nhưng benchmark LLM/LVLM hiện có (MMBench, AGIEval) (1) hiếm khi đánh giá nhiệm vụ thuần thị giác (segmentation, depth) vốn quan trọng với người khiếm thị và (2) ưu tiên tính tổng quát thay vì nhu cầu đặc thù của PVIs.

Người khiếm thị tham gia trực tiếp vào thiết kế: nhóm làm pre-study với 2 chuyên gia trợ năng để soạn bảng hỏi, rồi khảo sát 7 người mù hoặc thị lực kém. Mỗi người chấm 8 chức năng theo 3 tiêu chí (mức quan tâm, tần suất dùng, tầm quan trọng) thang 1–5; điểm trung bình 3 tiêu chí cộng lại để xếp hạng (Bảng 1):

| Chức năng | Nhiệm vụ tương ứng | Quan tâm | Tần suất | Quan trọng | Tổng |
|---|---|---|---|---|---|
| Nhận dạng chữ (Text Recognition) | OCR | 4.57 | 4.43 | 4.43 | **13.43** |
| Nhận dạng vật thể | Panoptic Seg. | 3.86 | 3.71 | 4.00 | 11.57 |
| Hỏi đáp thị giác | VQA | 3.57 | 3.43 | 3.43 | 10.43 |
| Định vị vật thể | Panoptic Seg. | 3.29 | 3.14 | 3.29 | 9.72 |
| Hiểu môi trường xung quanh | Image Captioning | 3.43 | 2.86 | 2.71 | 9.00 |
| Tránh vật cản | Panoptic Seg. | 3.00 | 2.71 | 2.43 | 8.14 |
| Ước lượng khoảng cách trong nhà | Depth Estimation | 3.14 | 2.43 | 2.43 | 8.00 |
| Nhận dạng cảnh (Scene Recognition) | – | 2.14 | 1.71 | 1.86 | 5.71 (loại) |

Nhận dạng chữ dẫn đầu cả 3 tiêu chí với khoảng cách lớn; nhận dạng cảnh bị loại vì điểm thấp vượt trội.

## 2. Phương pháp

**Benchmark @BENCH – 5 nhiệm vụ:** Panoptic Segmentation (PS), Depth Estimation (DE), OCR, Image Captioning (IC) và Visual Question Answering (VQA). OCR là chuyển ảnh chữ in/viết tay thành văn bản; vì là chức năng quan trọng nhất nên nhóm đưa vào nhiều bộ OCR phủ nhiều bối cảnh chữ (đa số generalist bỏ qua OCR). VQA và IC dùng VizWiz vì ảnh do chính người khiếm thị chụp. Benchmark còn xét trade-off hiệu quả–hiệu năng, đo bằng số tham số (nhóm nêu FLOPs và thời gian suy luận là lựa chọn khác nhưng chọn #params để so sánh với công trình trước).

**@MODEL:** xây trên X-Decoder, gồm image encoder, hai text encoder chia sẻ tham số, và transformer decoder với latent queries + textual queries. Hai kiểu đầu ra: pixel-level (PS, DE) và token-level (OCR, IC, VQA). Thay vì thêm một output head cho mỗi nhiệm vụ (multi-head, ~0.2M tham số/head), nhóm dùng **task-specific prompt** thống nhất đầu vào thành "ảnh + prompt" (~10K tham số/prompt); với VQA, câu hỏi chính là prompt. Lợi ích: thống nhất dạng đầu vào, giúp mô hình phân biệt nhiệm vụ sớm, và giảm tham số.

**Tokenizer riêng cho OCR:** mặc định là CLIP subword tokenizer (~50.000 subword). Nhóm quan sát các bộ OCR tiếng Anh: mỗi ảnh thường chỉ một từ, dùng 26 chữ cái + 10 chữ số, dài dưới 15 ký tự, nên chuyển sang **character-based tokenizer với vocabulary giới hạn**.

**Cách đánh giá:** (a) multi-task training (một bộ trọng số, không pre-train, không fine-tune riêng) so với generalist khác; (b) single-task training so với SoTA chuyên biệt; (c) ablation prompt vs multi-head và tokenizer.

## 3. Dữ liệu & thiết lập thí nghiệm

| Nhiệm vụ | Dataset | #Train | #Val | #Test | Metric |
|---|---|---|---|---|---|
| PS | ADE20K (150 lớp, >27K ảnh, 365 cảnh) | 25,574 | 2,000 | 2,000 | PQ |
| DE | NYU v2 (trong nhà) | 24,230 | 654 | 654 | RMSE |
| OCR | MJSynth + SynthText (train); IC13, IC15, IIIT5K, SVT, SVTP, CUTE (eval) | 15,895,356 | 7,507 | 7,507 | Accuracy |
| IC | VizWiz Cap | 23,431 | 7,750 | 8,000 | BLEU-1 / CIDEr |
| VQA | VizWiz VQA | 20,523 | 4,319 | 8,000 | Accuracy |
| Tổng | @BENCH | 15,989,114 | 22,230 | 26,161 | |

Chọn NYU v2 vì PVIs dành phần lớn thời gian trong nhà. Dữ liệu OCR toàn bộ là tổng hợp (synthetic) và tiếng Anh. Chi tiết cài đặt (optimizer, epoch, phần cứng) nằm ở supplementary – bài chính không nêu; phụ lục không có trong file text.

## 4. Kết quả chính

**Multi-task @MODEL so với generalist khác (Bảng 3, không pre-train/fine-tune):**

| Mô hình | PQ ↑ | RMSE ↓ | OCR avg (%) | B@1 | CIDEr | VQA (%) | #Params |
|---|---|---|---|---|---|---|---|
| Unified-IO (S)† | – | 0.649 | – | ⋆ | ⋆ | 42.4 | 71M |
| Unified-IO (B)† | – | 0.469 | – | ⋆ | ⋆ | 45.8 | 241M |
| Unified-IO (L)† | – | 0.402 | – | ⋆ | ⋆ | 47.7 | 776M |
| X-Decoder (T)† | 41.6 | – | – | ⋆ | ⋆ | – | 164M |
| GIT† | – | – | – | ⋆ | 113.1 | 68.0 | 0.7B |
| PaLI† | – | – | – | ⋆ | 117.2 | 67.5 | 3.0B |
| **@MODEL** | 38.5 | 0.425 | **80.1** | 61.0 | 52.5 | 53.7 | **62M** |

(† dùng trọng số pre-train.) @MODEL là generalist duy nhất có OCR; vượt Unified-IO (S) 0.224 RMSE và 11.3% VQA với số tham số tương đương, vượt cả Unified-IO (B); vẫn kém xa GIT/PaLI (lớn hơn 10–50 lần, có pre-train) về caption/VQA.

**Single-task so với SoTA chuyên biệt (Bảng 4), riêng OCR:**

| Mô hình | IC13 | IC15 | SVT | IIIT5K | SVTP | CUTE | Avg |
|---|---|---|---|---|---|---|---|
| ASTER | 91.8 | 76.1 | 89.5 | 93.4 | 78.5 | 79.5 | 86.7 |
| SEED | 92.8 | 80.0 | 89.6 | 93.8 | 81.4 | 83.6 | 88.3 |
| MaskOCR† (97M) | 98.1 | 87.3 | 94.7 | 95.8 | 89.9 | 89.2 | 93.1 |
| **@MODEL (62M)** | 97.1 | 84.4 | 92.6 | 90.3 | 88.7 | 93.1 | **90.0** |

@MODEL vượt ASTER +3.3% và SEED +1.7% (không pre-train), thua MaskOCR có pre-train. Nhiệm vụ khác (single-task): PQ 39.2 (MaskFormer 34.7, Mask2Former 39.7, kMaX-DeepLab 41.5), RMSE 0.386 (GLP 0.344, DPT 0.357, BTS 0.392), IC B@1 60.0 / CIDEr 45.1 (AoANet 65.9/59.7), VQA 49.1 (CS-VQA 53.2).

**Multi-task vs single-task:** OCR tụt từ 90.0% xuống 80.1% khi huấn luyện chung – nhóm cho rằng bộ OCR quá lớn (gần 16 triệu mẫu) gây mất cân bằng; PS, DE cũng giảm nhẹ. Ngược lại IC và VQA tăng (CIDEr 45.1 → 52.5; VQA 49.1 → 53.7) vì cùng liên quan hiểu cảnh.

**Ablation:** task-prompt tốt hơn multi-head trên mọi nhiệm vụ (OCR 80.1 vs 79.4; CIDEr 52.5 vs 50.0) với 62M vs 63M tham số. Với OCR, character tokenizer +4.3% (82.4 → 86.7), giới hạn vocabulary thêm +3.3% (→ 90.0).

**Nhận xét từ người dùng khiếm thị (Discussion):** về OCR, người dùng nói "khả năng dùng được bởi người mù hoàn toàn là rất quan trọng", "các hệ thống hiện tại gặp khó khi chọn đúng mục tiêu"; đọc văn bản trên giấy hay bao bì cầm tay bằng smartphone là khả thi, nhưng đọc được biển cửa, poster, biển đường ngoài tầm với mới "cực kỳ hữu ích". Về nhận dạng vật thể: cần độ tin cậy cao và cách để người mù xác nhận đúng vật đã được nhận ra. Thứ tự ưu tiên rõ ràng: chữ > vật thể > VQA. Về **độ ngắn gọn câu trả lời và tốc độ suy luận (latency): bài không nêu**; "hiệu quả" chỉ đo bằng số tham số.

## 5. Ưu điểm

- Benchmark xuất phát từ người dùng thật (2 chuyên gia + 7 PVIs), có điểm định lượng và trích dẫn định tính; là bằng chứng công bố (CORE A) rằng OCR là nhu cầu số một.
- Bao phủ cả nhiệm vụ thuần thị giác lẫn cross-modal, dùng dữ liệu VizWiz do người khiếm thị chụp.
- @MODEL nhỏ (62M), một bộ trọng số cho 5 nhiệm vụ, hướng tới thiết bị di động; task-prompt gần như không thêm tham số.
- Phân tích tokenizer cho OCR có giá trị thực tiễn: vocabulary nhỏ, theo ký tự tốt hơn subword.
- Báo cáo trung thực mặt tiêu cực (OCR giảm khi đa nhiệm).

## 6. Nhược điểm / hạn chế

- Mẫu khảo sát rất nhỏ (7 người); bài không nêu độ tuổi, mức độ khiếm thị, quốc gia hay phân tích thống kê.
- OCR chỉ ở mức từ đơn (word-level) trên ảnh crop sẵn, huấn luyện hoàn toàn bằng dữ liệu tổng hợp tiếng Anh; không có OCR tài liệu/trang sách, không tiếng Việt hay chữ có dấu, không có text detection.
- Không đo latency, FLOPs, pin trên thiết bị thật dù mục tiêu là "portable device"; không thử nghiệm sản phẩm với người dùng cuối.
- Không đánh giá đầu ra ở góc độ trợ năng (độ ngắn gọn, độ tin cậy, cách báo lỗi); không có TTS hay giao diện giọng nói.
- Khoảng cách còn lớn với LVLM lớn ở caption/VQA; chưa pre-train.
- Phụ lục (chi tiết cài đặt, thêm phân tích) không có trong file đọc được.

## 7. Liên hệ với đề tài

- **Xác nhận hướng đề tài:** đọc chữ là chức năng người khiếm thị quan tâm, dùng thường xuyên và coi là quan trọng nhất (13.43/15) – trích dẫn mạnh cho phần động cơ của app đọc sách.
- **Bài học về nhu cầu thật:** (a) phải dùng được bởi người mù hoàn toàn – giao diện không phụ thuộc thị giác, hướng dẫn canh khung bằng giọng nói/rung; (b) khó "chọn đúng mục tiêu" – app cần phản hồi khi trang bị lệch, thiếu sáng, mất góc; (c) muốn xác nhận đã nhận đúng đối tượng – nên đọc tiêu đề/đoạn đầu để người dùng xác nhận trước khi đọc cả trang.
- **Có nên dùng VLM thay OCR truyền thống?** Theo bài, chưa nên với pipeline đọc sách: generalist đa nhiệm làm OCR tụt 10 điểm, VLM lớn (GIT 0.7B, PaLI 3.0B) không khả thi trên máy không GPU, và benchmark chỉ đo chữ cảnh (scene text) tiếng Anh. Với trang sách tiếng Việt, engine OCR chuyên biệt (mô hình nhẹ, vocabulary ký tự tiếng Việt) hợp lý hơn; VLM để dành cho tính năng mở rộng (hỏi đáp về trang/ảnh minh họa).
- **Gợi ý kỹ thuật:** tokenizer theo ký tự với vocabulary giới hạn cho OCR tiếng Việt (bài cho +7.6% tổng cộng trên tiếng Anh); lưu ý mất cân bằng dữ liệu nếu huấn luyện chung nhiều nhiệm vụ.
- **Tiêu chí đánh giá nên đưa vào đồ án:** (1) độ chính xác OCR theo ký tự/từ (CER/WER) trên ảnh chụp điện thoại thật; (2) tài nguyên: số tham số, thời gian xử lý mỗi trang trên CPU, dung lượng mô hình – bổ sung latency mà bài chưa đo; (3) khảo sát người dùng theo đúng 3 tiêu chí của bài (quan tâm, tần suất, quan trọng) thang 1–5 cho từng tính năng; (4) khả năng dùng không cần nhìn (số thao tác, thời gian tới khi nghe được audio).

## 8. Thuật ngữ & số liệu đáng nhớ

- **PVIs** (People with Visual Impairments), **AT** (Assistive Technology), **human-in-the-loop user study**: 2 chuyên gia + 7 người khiếm thị, 8 chức năng, 3 tiêu chí thang 1–5.
- Text Recognition/OCR tổng 13.43 – cao nhất; Object Recognition 11.57; VQA 10.43; Scene Recognition 5.71 bị loại.
- @BENCH: 5 nhiệm vụ PS/DE/OCR/IC/VQA; 15,989,114 ảnh train, trong đó OCR 15,895,356 (MJSynth + SynthText).
- 6 bộ OCR đánh giá: IC13, IC15, IIIT5K, SVT, SVTP, CUTE (7,507 ảnh).
- @MODEL: 62M tham số, dựa trên X-Decoder, task-specific prompt (~10K tham số/prompt so với ~0.2M/head).
- OCR avg: 90.0% single-task vs 80.1% multi-task; vượt ASTER +3.3%, SEED +1.7%; MaskOCR (pre-train, 97M) 93.1%.
- Character tokenizer +4.3%, limited vocabulary +3.3% (82.4 → 86.7 → 90.0).
- Vượt Unified-IO (S) 0.224 RMSE và 11.3% VQA với số tham số tương đương (62M vs 71M).
- Efficiency chỉ đo bằng #params; latency/FLOPs/độ ngắn gọn câu trả lời: bài không nêu.
