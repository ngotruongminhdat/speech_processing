# So sánh chéo và khoảng trống nghiên cứu

Tổng hợp từ 8 ghi chú `01`–`08` và khảo sát trong nước `10`. Đây là phần dùng trực tiếp cho mục "Tổng quan" của báo cáo.

## 1. Bảng so sánh 7 bài báo

| # | Bài | Venue / hạng | Khối | Bài toán | Phương pháp | Dữ liệu | Kết quả chính | Mã / checkpoint | Tiếng Việt |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PhoAudiobook | ACL 2025 short, A* | TTS-VI | Thiếu dữ liệu TTS tiếng Việt chất lượng cao | Lọc 23K giờ sách nói bằng ASR kép, SI-SNR; huấn luyện VALL-E, VoiceCraft, XTTS-v2 | 941 h, 735 giọng, 16 kHz | XTTS-v2 fine-tune: WER 8,32 vs viXTTS 12,54 trên viVoice; XTTS yếu câu ngắn (WER 37,81) | Dataset có (CC-NC); **không có checkpoint** | Có |
| 2 | F5-TTS | ACL 2025 long, A* | TTS backbone | TTS zero-shot nhanh, không cần aligner/duration | Flow matching + DiT, ký tự thô, Sway Sampling | Emilia 95K h EN+ZH | WER 2,42, SIM 0,66, RTF 0,15 trên RTX 3090; nhanh hơn AR 4–6 lần | Có, 336M | Không; cộng đồng đã fine-tune |
| 3 | MobileSpeech | ACL 2024 long, A* | TTS on-device | TTS zero-shot cho điện thoại | FastSpeech2 + codec RVQ, mask song song (SMD), Prank | LibriTTS 580 h; 40K h ZH nội bộ | WER 3,1, RTF 0,09 trên A100, 207M tham số | **Không có mã, không checkpoint** | Không |
| 4 | ViTextVQA | ESWA 2025, Q1 | OCR-VI | VQA đọc chữ cảnh tiếng Việt | SwinTextSpotter + ViTextBLIP-2 | 16.762 ảnh đường phố, 50.342 QA | F1 53,95; thứ tự đọc TL-BR tăng F1 +2,19; mất dấu làm F1 giảm đơn điệu | Dataset có; không có mã | Có, scene text |
| 5 | ViOCRVQA | Multimedia Systems 2025, Q1 | OCR-VI | VQA đọc chữ bìa sách tiếng Việt | SwinTextSpotter + VisionReader (ViT5) | 28.282 bìa sách, 123.781 QA | EM 41,16, F1 69,90; bỏ OCR giảm F1 tên sách 45 điểm | Dataset theo yêu cầu; không có mã | Có, bìa sách |
| 6 | @BENCH | WACV 2025, A | Trợ năng | Benchmark VLM cho công nghệ hỗ trợ người khiếm thị | Khảo sát 7 PVI + 2 chuyên gia; @MODEL 62M đa nhiệm | VizWiz + 6 bộ OCR tiếng Anh | OCR là nhu cầu số 1 (13,43/15); OCR đa nhiệm 80,1% vs đơn nhiệm 90,0% | Mã hứa công bố | Không |
| 7 | OmniDocBench | CVPR 2025, A* | Document parsing | Benchmark phân tích trang PDF đa dạng | 981 trang, 9 loại, 3 mức đánh giá | EN 290 / ZH 612 | Trên sách: MinerU 0,055 < Marker 0,074 < Qwen2-VL-72B 0,096; Tesseract kém mọi điều kiện; PaddleOCR rớt mạnh khi xoay 270° | Mã + dữ liệu mở | Không |

Bài 8 (survey Vietnamese DAR, arXiv 2025) không xếp vào bảng vì là tổng quan; đóng góp chính là danh mục dataset và pipeline MC-OCR 2021 (PaddleOCR detection + VietOCR recognition, CER tốt nhất 0,22 trên ảnh chụp điện thoại).

## 2. Tổng hợp theo khối

### 2.1 TTS tiếng Việt

**Hiện trạng.** Ba bài cho ba mảnh ghép: PhoAudiobook cung cấp dữ liệu đúng miền sách nói nhưng không có mô hình; F5-TTS cung cấp kiến trúc nhanh, dễ fine-tune sang ngôn ngữ mới vì nhận ký tự thô; MobileSpeech chứng minh TTS zero-shot trên điện thoại khả thi nhưng không công bố gì để tái dụng. Cộng đồng đã ghép hai mảnh đầu: có ít nhất 3 checkpoint F5-TTS tiếng Việt (hynt ViVoice 1000 h, zalopay CC-BY-4.0, namprice227 huấn luyện trên chính PhoAudiobook).

**Điểm đồng thuận.**
- Mô hình non-autoregressive (F5-TTS, MobileSpeech) bền hơn autoregressive về lặp từ và mất từ. Với sách dài, đây là yếu tố an toàn vì người khiếm thị không đối chiếu được bằng mắt.
- Mọi bài đều cần bước chuẩn hóa văn bản trước TTS: PhoAudiobook chuẩn hóa transcript trước khi huấn luyện, F5-TTS nhận ký tự thô nên không tự đọc số. VLSP 2020 đã xem chuẩn hóa là bài toán riêng.
- Độ dài câu đầu vào ảnh hưởng mạnh: XTTS-v2 lỗi nặng với câu ngắn, F5-TTS test trên câu 4–10 giây. Hệ quả cho app: gộp câu ngắn thành đoạn 10–20 giây trước khi TTS.

**Điểm mâu thuẫn hoặc thiếu.**
- Không bài nào đo RTF trên CPU hay điện thoại thật. MobileSpeech tự nhận hệ số 8–10 lần giữa điện thoại và A100 nhưng không có số đo. Đây là số liệu đồ án phải tự đo.
- Giấy phép: PhoAudiobook và đa số checkpoint cộng đồng là phi thương mại; chỉ zalopay là CC-BY-4.0. Với đồ án học thuật thì không vướng, nhưng cần ghi rõ trong báo cáo.

### 2.2 OCR tiếng Việt cho trang sách

**Hiện trạng.** Hai bài UIT (ViTextVQA, ViOCRVQA) là dữ liệu tiếng Việt lớn nhất nhưng đều là VQA, dùng duy nhất SwinTextSpotter và **không báo cáo CER/WER của OCR**. OmniDocBench cho so sánh engine kỹ lưỡng nhất nhưng không có tiếng Việt và không có ảnh chụp điện thoại. Survey xác nhận không có bộ dữ liệu trang sách tiếng Việt nào, gần nhất là VNDoc 226 tài liệu.

**Điểm đồng thuận.**
- Tesseract chỉ nên làm baseline: OmniDocBench đo kém mọi điều kiện, survey nói yếu về dấu tiếng Việt.
- Pipeline detection + recognition nhẹ thắng VLM lớn trên trang sách sạch (OmniDocBench: MinerU 0,055 vs GPT-4o 0,157), và @BENCH cho thấy OCR trong mô hình đa nhiệm tụt 10 điểm. Kết luận: giữ OCR chuyên biệt, VLM chỉ làm fallback cho ảnh xấu hoặc tính năng hỏi đáp.
- Thứ tự đọc và dấu thanh là hai lỗi đặc thù tiếng Việt: ViTextVQA đo được TL-BR tăng F1 và mất dấu làm giảm đơn điệu; survey tổng hợp 5 hướng sửa lỗi dấu sau OCR.
- Xoay và nghiêng phá hỏng OCR: PaddleOCR rớt từ 0,015 xuống 0,285 khi xoay 270°; MC-OCR 2021 có bước sửa xoay riêng.

**Điểm mâu thuẫn cần giải quyết bằng thực nghiệm.**
- OmniDocBench xếp PaddleOCR tốt nhất, survey cho thấy 5/6 đội MC-OCR dùng VietOCR, còn một nguồn cộng đồng (xem `10_vietnam_landscape.md`) cho rằng từ điển của PP-OCRv5 bản latin **không có dải ký tự dấu thanh tiếng Việt**. Ba nguồn này không mâu thuẫn nếu hiểu đúng: PaddleOCR mạnh ở **phát hiện dòng**, còn **nhận dạng** tiếng Việt cần VietOCR hoặc model PaddleOCR có từ điển tiếng Việt. Stage 2 phải kiểm tra trực tiếp từ điển của PP-OCRv5 và so CER của ba cấu hình: Tesseract vie, PaddleOCR det + VietOCR rec, PaddleOCR det + PP-OCRv5 rec.

### 2.3 Trợ năng và thiết kế cho người khiếm thị

Chỉ có @BENCH là bài có người khiếm thị tham gia, và nó khẳng định đọc chữ là nhu cầu số một. Ba yêu cầu rút ra: dùng được mà không nhìn màn hình, phản hồi khi khung hình lệch hoặc thiếu sáng, và xác nhận đã nhận đúng đối tượng trước khi đọc dài. Không bài nào trong 7 bài đo độ trễ từ lúc chụp tới lúc nghe được audio, cũng không bài nào đánh giá TTS trong bối cảnh trợ năng. Khảo sát trong nước cho thấy chưa có app Việt nào kết hợp OCR sách giấy với TTS tiếng Việt và giao diện cho người mù; Envision làm được OCR tiếng Việt nhưng giao diện tiếng Anh.

## 3. Khoảng trống nghiên cứu và đóng góp dự kiến của đồ án

| Khoảng trống | Bằng chứng từ tài liệu | Đóng góp của đồ án |
|---|---|---|
| Chưa có benchmark OCR tiếng Việt trên **trang sách chụp điện thoại** | Survey: không có dataset trang sách; ViTextVQA/ViOCRVQA là scene text và bìa web; OmniDocBench không có tiếng Việt | Bộ test nhỏ 20–30 trang tự chụp có ground truth, gán thuộc tính (nghiêng, sáng, cột); so 3 cấu hình OCR theo CER/WER và thời gian trên CPU, mượn metric Normalized Edit Distance và ignore header/footer của OmniDocBench |
| Chưa có số đo **RTF của TTS tiếng Việt trên CPU** | F5-TTS, MobileSpeech, PhoAudiobook đều không đo CPU | Đo RTF và MOS nhỏ cho F5-TTS tiếng Việt, VieNeu-TTS và một API thương mại trên cùng 10 câu |
| Chưa có **pipeline end-to-end** OCR trang sách → chuẩn hóa → TTS được đánh giá như một hệ thống | Mỗi bài chỉ giải một khối; không bài nào đo độ trễ chụp-tới-nghe | App chạy được với độ trễ đo trên điện thoại thật; đánh giá dùng được không cần nhìn |
| **Chuẩn hóa văn bản sách** (số chương, chú thích, hội thoại, nối dòng) chưa có công cụ mở | VLSP 2020 nêu vấn đề; PhoAudiobook không công bố mô hình chuẩn hóa; ViTextVQA chỉ ra lỗi nối dòng và thứ tự đọc | Mô-đun chuẩn hóa dựa trên luật, kiểm tra bằng số lỗi đọc sai của TTS trước và sau |
| Lỗi **dấu thanh từ OCR truyền sang TTS** chưa được định lượng | ViTextVQA đo trên VQA, survey tổng hợp phương pháp sửa nhưng không gắn với TTS | Nếu chọn hướng cải tiến OCR ở Stage 4: hậu xử lý sửa dấu bằng mô hình ngôn ngữ tiếng Việt, đo CER trước và sau |

## 4. Quyết định rút ra cho Stage 2

1. OCR: so ba cấu hình Tesseract vie, PaddleOCR det + VietOCR rec, PaddleOCR det + PP-OCRv5 rec. Kiểm tra từ điển PP-OCRv5 trước khi chạy. Có bước xoay tự động và deskew.
2. TTS: so VieNeu-TTS (CPU), F5-TTS checkpoint zalopay hoặc hynt, và FPT.AI API. Gộp câu ngắn thành đoạn 10–20 giây. Đo RTF trên CPU máy dev.
3. Đánh giá: CER/WER bằng Normalized Edit Distance mức ký tự, bỏ header/footer; báo cáo theo thuộc tính ảnh; WER của TTS đo bằng PhoWhisper như PhoAudiobook.
4. Thiết kế app: theo ba yêu cầu của @BENCH, cộng thêm đọc tiêu đề hoặc câu đầu để người dùng xác nhận trước khi đọc cả trang.
