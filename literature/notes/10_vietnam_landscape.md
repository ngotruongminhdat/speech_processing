# Giải pháp trong nước và hiện trạng công cụ cho tiếng Việt

Khảo sát ngày 04/11/2026. Mục tiêu: trả lời câu hỏi "trong nước đang giải quyết thế nào" và chốt các công cụ ứng viên cho Stage 2 (demo). Những chỗ đánh dấu ⚠️ là thông tin lấy từ trang nhà cung cấp hoặc blog, chưa kiểm chứng độc lập, cần tự chạy thử trước khi đưa vào báo cáo như một kết luận.

## 1. Nghiên cứu trong nước: VLSP

VLSP (Vietnamese Language and Speech Processing) là chuỗi shared task học thuật chính của Việt Nam về xử lý tiếng nói.

| Năm | Nhiệm vụ TTS | Điểm đáng chú ý |
|---|---|---|
| 2018 | TTS lần 1 | Viettel đứng đầu với MOS 4.66 |
| 2019 | TTS lần 2 | – |
| 2020 | TTS lần 3, 59 đội đăng ký | Trọng tâm: ngắt nghỉ ngữ điệu (prosodic phrasing) cho câu dài và **chuẩn hóa văn bản** (text normalization). Đây chính là hai vấn đề cốt lõi khi đọc sách. |
| 2021 | TTS giọng nói tự nhiên (spontaneous), 43 đội đăng ký, 8 bài nộp | MOS in-domain tốt nhất khoảng 3.73, out-of-domain 3.56 |
| 2022–2024 | Không tìm thấy nhiệm vụ TTS riêng ⚠️ | Cần kiểm tra lại proceedings ACL Anthology |
| 2025 | Voice Conversion (lần đầu) và Speech Quality Assessment | Không có TTS; VC và SQA là hai nhiệm vụ gần TTS nhất |

Nhận xét: nghiên cứu TTS tiếng Việt trong nước đã chuyển từ shared task sang các bài báo quốc tế (PhoAudiobook của VinAI tại ACL 2025 là ví dụ) và sang sản phẩm thương mại. Chưa có shared task nào về **đọc tài liệu dài / sách nói** như một bài toán end-to-end.

Nguồn: [VLSP 2020 TTS overview](https://aclanthology.org/2020.vlsp-1.7.pdf), [VLSP 2021 TTS](https://jcsce.vnu.edu.vn/index.php/jcsce/article/view/358), [VLSP 2025 VC](https://aclanthology.org/2025.vlsp-1.13.pdf), [VLSP 2025 SQA](https://aclanthology.org/2025.vlsp-1.7.pdf), [Bảng tiến độ TTS tiếng Việt](https://github.com/undertheseanlp/NLP-Vietnamese-progress/blob/master/tasks/text_to_speech.md).

## 2. TTS tiếng Việt thương mại (API)

| Nhà cung cấp | Giọng | Giá ⚠️ | Ghi chú |
|---|---|---|---|
| FPT.AI | ~7 giọng, 3 miền Bắc/Trung/Nam | Miễn phí 100.000 ký tự/tháng; gói 500.000đ cho 1,5 triệu ký tự; lớn nhất 5 triệu đồng cho 27 triệu ký tự | Có tài liệu API rõ ràng, phù hợp làm baseline thương mại cho demo |
| Viettel AI | 9 giọng, 3 miền | Không tìm thấy giá công khai | Đứng đầu VLSP 2018 |
| Zalo AI | 4–6 giọng Bắc/Nam | Tải audio cần gói trả phí | Số giọng không thống nhất giữa các nguồn |
| Vbee | Nhiều giọng | Một bài báo cũ nêu 500đ/1.000 ký tự, miễn phí 10.000 ký tự | Được thiết bị Blue Eye dùng |
| VinBase (VinBigData) | – | Không tìm thấy thông tin công khai | – |

Nhận xét cho đề tài: một cuốn sách 300 trang khoảng 400.000 đến 600.000 ký tự, tức là gói miễn phí của FPT.AI chỉ đọc được một phần cuốn sách mỗi tháng. Chi phí API là lý do chính đáng để app cần cache audio theo câu và cân nhắc TTS offline.

Nguồn: [FPT.AI TTS pricing](https://docs.fpt.ai/docs/en/speech/documentation/tts-pricing/), [FPT.AI TTS overview](https://docs.fpt.ai/docs/en/speech/documentation/text-to-speech/), [Viettel AI](https://viettelai.vn/en/tin-tuc/top-5-phan-mem-doc-van-ban-thanh-giong-noi-mien-phi), [So sánh Vbee](https://tryaivoices.com/blog/vbee-ai-voice).

## 3. TTS tiếng Việt mã nguồn mở

| Dự án | Nền tảng | Dữ liệu huấn luyện | Giấy phép | Ghi chú |
|---|---|---|---|---|
| hynt/F5-TTS-Vietnamese-ViVoice | F5-TTS | ~1000 giờ (ViVoice, VLSP 2021–2023) | CC-BY-NC-SA-4.0 | Checkpoint F5 tiếng Việt được nhắc tới nhiều nhất |
| zalopay/vietnamese-tts | F5-TTS | – | CC-BY-4.0 | Giấy phép thoáng nhất trong nhóm F5 |
| namprice227/F5-TTS-Vietnamese1000h-Pretrain | F5-TTS | PhoAudiobook | – | Huấn luyện đúng trên dữ liệu **sách nói**, rất hợp đề tài; đánh dấu "experimental" |
| toandev / yukiakai / danhtran2mind / ticchien | F5-TTS | viet-tts dataset và khác | CC-BY-NC | Chất lượng không đồng đều, có bản tự nhận "khá tệ" |
| VietTTS (dangvansam) | Toolkit riêng | – | Apache 2.0 | Có trên PyPI (04/2025) |
| **VieNeu-TTS (pnnbao97)** | Mô hình riêng | – | – | Quảng cáo chạy **real-time trên CPU, on-device, 48 kHz, clone giọng tức thì** ⚠️. Nếu đúng, đây là ứng viên số một cho TTS offline trên máy không GPU |
| viXTTS | XTTS-v2 | – | Coqui (non-commercial) | Được PhoAudiobook dùng làm baseline XTTS |

Kết luận cho Stage 2: thử ba engine theo thứ tự ưu tiên: (1) VieNeu-TTS vì chạy CPU, (2) F5-TTS checkpoint hynt hoặc zalopay, (3) FPT.AI API làm mốc thương mại. Đo RTF trên CPU máy dev và nghe thử cùng 10 câu.

Nguồn: [hynt/F5-TTS-Vietnamese-ViVoice](https://huggingface.co/hynt/F5-TTS-Vietnamese-ViVoice/blob/main/README.md), [zalopay/vietnamese-tts](https://huggingface.co/zalopay/vietnamese-tts), [namprice227](https://huggingface.co/namprice227/F5-TTS-Vietnamese1000h-Pretrain), [VietTTS](https://huggingface.co/dangvansam/viet-tts), [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS), [F5-TTS-Vietnamese GitHub](https://github.com/nguyenthienhy/F5-TTS-Vietnamese).

## 4. OCR tiếng Việt: công cụ và cảnh báo

| Công cụ | Loại | Tiếng Việt | Bằng chứng ⚠️ |
|---|---|---|---|
| Tesseract (`vie`) | OCR cổ điển, CPU | Có, đầy đủ dấu | Tài liệu VietOCR cũ nêu >97% trên bản quét tốt; một PR trên GitHub đo 2,3% lỗi trên trang in sinh tự động. Yếu với chữ nhỏ, ảnh chụp nghiêng, bóng. |
| VietOCR (pbcquoc) | Transformer/Attention, chỉ nhận dạng dòng | Có | Giảm CER từ 69,3% xuống 31,8% so với Tesseract trên **chữ viết tay**; cần ghép với mô-đun phát hiện dòng (thường là PaddleOCR det hoặc CRAFT) |
| PaddleOCR PP-OCRv5 | Det + Rec, có bản mobile | **Nghi vấn** | Một nguồn nêu từ điển của `latin_PP-OCRv5_mobile_rec` **không chứa dải U+1EA0–U+1EF9**, tức không xuất được dấu thanh tiếng Việt; cùng nguồn đo 21,6% lỗi so với 2,3% của Tesseract trên trang in. Phải tự kiểm tra ở Stage 2 trước khi loại. |
| PP-OCRv6 fine-tune (OcrDoc) | Fine-tune cộng đồng | Có | Tự báo 78,95% trên VinText so với 59,19% của VietOCR |
| VLM (Qwen2.5-VL, GPT-4o) | Đa năng | Có | Mạnh với bố cục phức tạp nhưng cần GPU hoặc API, độ trễ cao |

Nhận xét: trái với giả định ban đầu, **PP-OCRv5 có thể không phải lựa chọn an toàn cho tiếng Việt**. Thiết kế thí nghiệm Stage 2 cần so ít nhất Tesseract, VietOCR (với PaddleOCR detection) và một VLM nhỏ, trên cùng tập ảnh trang sách có ground truth.

Nguồn: [Nôm benchmark OCR](https://nom-vn.nrl.ai/tasks/ocr), [PR uniwork-office về Tesseract vie](https://github.com/UNIAI-TEAM/uniwork-office/pull/11), [OcrDoc](https://huggingface.co/truonggiabao7/ocrdoc-models), [VietOCR usage](https://vietocr.sourceforge.net/usage.html).

## 5. Ứng dụng hiện có cho người khiếm thị

### Quốc tế

| App | Tiếng Việt | Ghi chú |
|---|---|---|
| Envision AI | Có OCR tiếng Việt (nằm trong hơn 60 ngôn ngữ đọc được) | Gần nhất với đề tài; giao diện app không có tiếng Việt |
| Seeing AI (Microsoft) | Không xác nhận được | Một blog nhận xét chỉ tốt cho đoạn ngắn tiếng Anh ⚠️ |
| Be My Eyes / Be My AI | Không xác nhận được | Dựa trên GPT-4, có thể đọc được tiếng Việt nhưng không có tài liệu chính thức |
| Google Lookout, TalkBack | Có OCR cơ bản | Không tối ưu cho đọc sách dài |

### Trong nước

| Sản phẩm | Loại | Ghi chú |
|---|---|---|
| SgBE (TP.HCM, 2025) | App AI nhận diện tiền, vật thể, màu, phản hồi bằng giọng tiếng Việt | Không tập trung vào đọc sách |
| Blue Eye | Thiết bị Android + camera, đọc chữ bằng Vbee TTS | Thiết bị riêng, không phải app điện thoại |
| Mắt kính AI (sinh viên TP.HCM) | Thiết bị đeo, OCR + Google TTS | Tự báo độ chính xác 90%, thử với 10 người |
| Helen | App sách nói Android do học sinh làm | Sách nói có sẵn, không OCR |
| Waka, Voiz FM, Fonos | Nền tảng sách nói thương mại | Nội dung có bản quyền, không đọc sách giấy |
| "Đọc Văn Bản Bằng Giọng Nói" (App Store) | App OCR + TTS, tự nhận xử lý AI cục bộ | Thông tin từ mô tả store ⚠️ |

Nguồn: [AI cho người khiếm thị (VJST)](https://vjst.vn/tri-tue-nhan-tao-mo-them-doi-mat-so-cho-nguoi-khiem-thi-87164.html), [Blue Eye](https://vusta.vn/blue-eye-ho-tro-doc-van-ban-cho-nguoi-khiem-thi-p87415.html), [Mắt kính AI](https://vnexpress.net/sinh-vien-lam-mat-kinh-ho-tro-doc-sach-cho-nguoi-mu-4554242.html), [Envision App Store](https://apps.apple.com/us/app/envision-ai/id1268632314), [Văn hóa đọc cho người khiếm thị](https://thoibaonganhang.vn/anh-sang-van-hoa-doc-cho-nguoi-khiem-thi-117832.html).

## 6. Khoảng trống rút ra

1. **Không có app Việt nào** kết hợp OCR trang sách giấy + TTS tiếng Việt + giao diện thiết kế riêng cho người không nhìn màn hình. Envision làm được OCR tiếng Việt nhưng giao diện tiếng Anh và không tối ưu cho sách dài.
2. **OCR tiếng Việt trên ảnh chụp điện thoại chưa có benchmark công khai đáng tin**; các con số hiện có mâu thuẫn và đo trên dữ liệu khác nhau. Đồ án có thể đóng góp một tập test nhỏ và so sánh công bằng.
3. **TTS offline trên CPU** cho tiếng Việt mới xuất hiện (VieNeu-TTS) và chưa được đánh giá độc lập. Đo RTF và MOS của nó là đóng góp có giá trị.
4. **Chuẩn hóa văn bản sách** (số chương, chú thích, hội thoại, viết tắt) là vấn đề VLSP 2020 đã nêu nhưng chưa có công cụ mở nào xử lý tốt cho văn bản sách.
