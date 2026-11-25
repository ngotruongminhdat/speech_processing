# Sách Nói: ứng dụng đọc sách tiếng Việt cho người khiếm thị trên thiết bị di động

**Báo cáo đồ án cuối kỳ môn Xử lý tiếng nói**

| | |
|---|---|
| Học viên | (điền họ tên, mã số) |
| Giảng viên | (điền) |
| Hướng thực hiện | Ứng dụng |
| Sản phẩm | https://ngotruongminhdat.github.io/speech_processing/ |
| Mã nguồn | nhánh `final_project` của kho `speech_processing` |
| Ngày viết | 18/11/2026 |

## Tóm tắt

Đồ án giữa kỳ đã tạo một cuốn sách nói theo chuẩn DAISY 3. Đồ án cuối kỳ làm phần còn thiếu để người khiếm thị thật sự nghe được sách trên điện thoại: một dây chuyền biến văn bản thuộc phạm vi công cộng thành sách nói DAISY có mốc thời gian từng câu, và một ứng dụng web tên **Sách Nói** để tìm, nghe và điều hướng trong các cuốn sách đó bằng trình đọc màn hình.

Bốn kết quả chính:

1. **Tổng quan** tám bài báo (sáu bài ở hội nghị hạng A*/A hoặc tạp chí Q1, giai đoạn 2024–2025) và khảo sát giải pháp trong nước, rút ra ba khoảng trống: chưa có số đo tốc độ TTS tiếng Việt trên CPU, chưa có sách nói tiếng Việt điều hướng được ở mức câu cho người khiếm thị, và chưa bài nào đánh giá TTS trong bối cảnh trợ năng.
2. **Demo**: so sánh ba hệ TTS tiếng Việt (Piper, VieNeu-TTS, giọng Hoài My của Microsoft qua edge-tts) với bảy cấu hình giọng trên cùng một văn bản, đo tốc độ tạo trên CPU, tỉ lệ lỗi từ qua nhận dạng tiếng nói, tốc độ đọc và tỉ lệ khoảng lặng.
3. **Ứng dụng**: thư viện 15 đầu sách thuộc 9 thể loại (tính cả cuốn giữa kỳ), đồng bộ văn bản với âm thanh ở mức câu, dùng được hoàn toàn bằng bàn phím và trình đọc màn hình, nghe được khi mất mạng, có chế độ chạm đơn giản gồm năm nút lớn tự đọc lời nhắc, và có 112 kiểm thử tự động trên trình duyệt thật.
4. **Phân tích sâu** bước TTS của dây chuyền: vì sao giọng nhanh nhất không phải giọng tốt nhất cho sách nói, phép đo nào giải thích được nhận xét của người nghe, và ba cải tiến đã cài đặt (lấy mốc câu từ mốc từ của dịch vụ, lưới an toàn bắt câu đọc sót, tăng độ bền khi gọi dịch vụ).

Những việc chưa làm được ghi ở mục 6, quan trọng nhất là chưa thử với người khiếm thị và chưa thử trên điện thoại thật với TalkBack hoặc VoiceOver.

---

## 1. Bài toán và phạm vi

### 1.1. Động cơ

Người khiếm thị đọc sách chủ yếu qua hai kênh: chữ nổi và sách nói. Chuẩn sách nói dành cho họ là DAISY (Digital Accessible Information System): ngoài âm thanh còn có cấu trúc (chương, mục, đoạn) và bảng đồng bộ giữa văn bản với âm thanh, nhờ đó người nghe nhảy được tới đúng chương, đúng đoạn, đúng câu thay vì tua mù như với một file mp3. Ở Việt Nam, sách nói thương mại (Fonos, Voiz FM, Waka) không theo chuẩn này và không thiết kế cho trình đọc màn hình; còn các ứng dụng đọc DAISY quốc tế (BARD Mobile, Legimus, Voice Dream Reader) không có kho sách tiếng Việt.

### 1.2. Quan hệ với đồ án giữa kỳ

```
Giữa kỳ:   EPUB ─► văn bản ─► TTS ─► DAISY 3 (một cuốn, trang web cho từng chương)
Cuối kỳ:   Wikisource ─► văn bản ─► TTS ─► DAISY 3 + mốc từng câu ─► thư viện trên điện thoại
```

| | Giữa kỳ | Cuối kỳ |
|---|---|---|
| Sách | 1 cuốn (Totto-chan bên cửa sổ) | Thư viện 14 cuốn mới, thêm một cuốn bằng hai lệnh |
| Nguồn văn bản | File EPUB | Wikisource tiếng Việt, chỉ tác phẩm thuộc phạm vi công cộng |
| Đồng bộ văn bản với âm thanh | Mức đoạn văn | Mức câu |
| Trình phát | Một trang HTML sinh sẵn cho mỗi chương | Một ứng dụng thiết kế cho điện thoại và trình đọc màn hình |
| Ngoại tuyến | Không | Lưu sách trên máy, cài lên màn hình chính |
| Kiểm thử | Kiểm tra cấu trúc DAISY | Thêm 160 kiểm thử giao diện |

Các script sinh DAISY (`gen_smil.py`, `gen_opf_ncx.py`, `validate_daisy.py`) và ngôn ngữ thiết kế giao diện được kế thừa từ giữa kỳ. Phần còn lại là làm mới.

### 1.3. Thay đổi hướng trong quá trình làm

Kế hoạch đầu tiên (04/11) đặt trọng tâm vào việc chụp trang sách giấy rồi nhận dạng chữ (OCR). Sau khi xem lại đề bài và đồ án giữa kỳ, hướng được đổi (05/11) sang kế thừa giữa kỳ: lõi của đồ án là tiếng nói và trợ năng, OCR chỉ còn là hướng mở rộng. Hệ quả là phần tổng quan có ba bài về OCR tiếng Việt được đọc cho hướng ban đầu; báo cáo giữ lại chúng ở mục 2.3 với vai trò nền cho hướng mở rộng và ghi rõ điều này thay vì giấu đi.

Ràng buộc xuyên suốt: máy phát triển không có GPU (AMD Ryzen 7 5700G, 16 luồng, 62 GB RAM), nên mọi mô hình phải chạy được trên CPU hoặc gọi qua dịch vụ.

---

## 2. Tổng quan tài liệu

### 2.1. Danh sách bài báo

| # | Bài | Nơi công bố | Hạng | Vai trò trong đồ án |
|---|---|---|---|---|
| 1 | Vu, Nguyen, Nguyen. *Zero-Shot Text-to-Speech for Vietnamese* (PhoAudiobook) | ACL 2025, short papers, tr. 1042–1049 | CORE A* | TTS tiếng Việt cho miền sách nói; phương pháp đánh giá |
| 2 | Chen và cộng sự. *F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching* | ACL 2025, long papers, tr. 6255–6271 | CORE A* | Kiến trúc TTS không tự hồi quy |
| 3 | Ji và cộng sự. *MobileSpeech: A Fast and High-Fidelity Framework for Mobile Zero-Shot Text-to-Speech* | ACL 2024, long papers | CORE A* | TTS trên thiết bị di động |
| 4 | Jiang, Zheng và cộng sự. *@BENCH: Benchmarking Vision-Language Models for Human-centered Assistive Technology* | WACV 2025, tr. 3934–3943 | CORE A | Nhu cầu của người khiếm thị |
| 5 | Pham và cộng sự. *ViOCRVQA: Novel Benchmark Dataset and Vision Reader for Visual Question Answering by Understanding Vietnamese Text in Images* | Multimedia Systems, 2025 | Q1 (SJR) | Đọc bìa sách tiếng Việt (hướng mở rộng) |
| 6 | Nguyen và cộng sự. *ViTextVQA: A Large-Scale Visual Question Answering Dataset for Evaluating Vietnamese Text Comprehension in Images* | Expert Systems with Applications, 2025 | Q1 | Lỗi dấu thanh và thứ tự đọc (hướng mở rộng) |
| 7 | Ouyang và cộng sự. *OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations* | CVPR 2025 | CORE A* | So sánh công cụ OCR trang sách (hướng mở rộng) |
| 8 | Le, Lam, Nguyen. *A Survey on Vietnamese Document Analysis and Recognition* | arXiv:2506.05061, 2025 | chưa phản biện | Tài liệu nền, không tính vào số bài đạt chuẩn |

Bảy bài đầu thỏa yêu cầu về nơi công bố và thời gian (2024–2025). Ghi chú chi tiết từng bài theo khung bảy mục nằm ở `literature/notes/`.

### 2.2. Nhóm bài về tổng hợp tiếng nói

**Bài 1. PhoAudiobook (ACL 2025).** Các bộ dữ liệu TTS tiếng Việt trước đó chủ yếu là mẫu ngắn dưới 10 giây, thiếu định danh người nói hoặc chưa chuẩn hóa văn bản. Nhóm tác giả lọc 23 nghìn giờ sách nói bằng hai mô hình nhận dạng tiếng nói kiểm tra chéo và chỉ số SI-SNR, thu được 941 giờ của 735 giọng đọc, mỗi mẫu dài 10–20 giây. Họ huấn luyện ba mô hình zero-shot (VALL-E, VoiceCraft, XTTS-v2) trên bộ này. XTTS-v2 huấn luyện trên PhoAudiobook đạt tỉ lệ lỗi từ (WER) 8,32% trên tập viVoice, so với 12,54% của viXTTS.

- *Ưu điểm:* dữ liệu đúng miền đọc sách, giọng đọc chuyên nghiệp ở tốc độ thong thả (201 từ mỗi phút); đánh giá kỹ với bốn tập thử và cả điểm chấm mù của người bản ngữ; chỉ ra một hiện tượng thực tế là XTTS-v2 lỗi nặng với câu ngắn (WER 37,81%).
- *Nhược điểm:* chỉ công bố dữ liệu, không công bố mô hình đã huấn luyện; giấy phép phi thương mại; không báo cáo tốc độ suy luận, kích thước mô hình hay bộ nhớ; mô hình chuẩn hóa văn bản dùng trong bài không được công bố.
- *Dùng trong đồ án:* (1) cách đánh giá độ rõ bằng cách cho mô hình nhận dạng tiếng nói nghe lại audio tổng hợp rồi tính WER; (2) mốc 201 từ mỗi phút để so tốc độ đọc; (3) cảnh báo về câu ngắn, hiện tượng mà đồ án cũng gặp với câu thoại một từ.

**Bài 2. F5-TTS (ACL 2025).** Hệ TTS zero-shot hoàn toàn không tự hồi quy, dựa trên flow matching với khung Diffusion Transformer. Văn bản chỉ được tách thành ký tự và đệm cho bằng độ dài phổ mel, không cần mô hình độ dài, không cần căn chỉnh âm vị. Bài thêm khối ConvNeXt V2 để tinh chỉnh biểu diễn văn bản và chiến lược lấy mẫu Sway Sampling. Kết quả trên tiếng Anh: WER 2,42%, hệ số thời gian thực (RTF) 0,15 trên RTX 3090, nhanh hơn các mô hình tự hồi quy 4–6 lần.

- *Ưu điểm:* dây chuyền rất đơn giản, đầu vào là ký tự thô nên dễ mở rộng sang ngôn ngữ mới; bền hơn E2 TTS; hội tụ được với dữ liệu nhỏ; công bố mã và mô hình.
- *Nhược điểm:* mọi số đo tốc độ là trên GPU, không có số nào trên CPU hay điện thoại; sinh cả câu một lần nên không phát dần được; không đề cập tiếng Việt; mô hình không tự đọc số, ngày tháng, chữ viết tắt nên bắt buộc có bước chuẩn hóa văn bản; không đánh giá trên văn bản dài kiểu trang sách.
- *Dùng trong đồ án:* là ứng viên chất lượng cao (cộng đồng đã có ít nhất ba bản huấn luyện tiếp cho tiếng Việt), nhưng không chạy thử được vì máy không có GPU. Luận điểm "mô hình không tự hồi quy ít lặp từ, sót từ hơn" của bài là cơ sở để đồ án chú ý tới hiện tượng đọc sót của VieNeu-TTS, một mô hình tự hồi quy.

**Bài 3. MobileSpeech (ACL 2024).** Hệ TTS zero-shot đầu tiên nhắm tới điện thoại, xây trên FastSpeech2 và bộ mã hóa âm thanh rời rạc, sinh mã song song bằng cơ chế che thay vì tự hồi quy. Với 207 triệu tham số và 580 giờ dữ liệu, mô hình đạt WER 3,1% và RTF 0,09 trên GPU A100.

- *Ưu điểm:* nhỏ nhất trong nhóm so sánh; sinh song song nên không tích lũy lỗi; đã triển khai trong sản phẩm thật.
- *Nhược điểm:* không công bố mã lẫn mô hình; dù tên là "Mobile", mọi số đo tốc độ là trên A100 và bỏ qua bộ giải mã âm thanh; chỉ có tiếng Anh và tiếng Trung.
- *Dùng trong đồ án:* không tái sử dụng được gì trực tiếp. Giá trị của bài là bộ tiêu chí (RTF, số tham số, WER qua nhận dạng tiếng nói) và nhận định rằng một ứng dụng đọc sách không cần nhân bản giọng mà cần một giọng cố định, rõ và ổn định.

**Tổng hợp nhóm TTS.** Ba bài đồng thuận ở hai điểm: mô hình không tự hồi quy bền hơn về lặp và sót từ, và TTS luôn cần chuẩn hóa văn bản phía trước. Cả ba cùng thiếu một thứ: **không bài nào đo tốc độ trên CPU hoặc trên điện thoại thật**. MobileSpeech chỉ ước lượng điện thoại chậm hơn A100 từ 8 đến 10 lần mà không có số đo. Đây là số liệu đồ án tự đo ở mục 3.

### 2.3. Nhóm bài về trợ năng và đọc chữ

**Bài 4. @BENCH (WACV 2025).** Bài đặt câu hỏi các mô hình thị giác ngôn ngữ đã sẵn sàng cho công nghệ hỗ trợ người khiếm thị chưa. Nhóm tác giả khảo sát 7 người khiếm thị và 2 chuyên gia để xếp hạng nhu cầu, rồi dựng bộ đánh giá năm nhiệm vụ và một mô hình đa nhiệm 62 triệu tham số.

- *Ưu điểm:* là bài duy nhất trong tám bài có người khiếm thị tham gia; cho kết quả định lượng rằng **đọc chữ là nhu cầu số một** (13,43 trên 15 điểm); báo cáo trung thực cả kết quả bất lợi (nhận dạng chữ trong mô hình đa nhiệm đạt 80,1% so với 90,0% của mô hình chuyên biệt).
- *Nhược điểm:* mẫu khảo sát chỉ 7 người, không nêu mức độ khiếm thị; không đo độ trễ hay pin trên thiết bị thật; không đánh giá đầu ra ở góc độ trợ năng (ngắn gọn, cách báo lỗi) và không có thành phần tiếng nói.
- *Dùng trong đồ án:* làm căn cứ cho động cơ của đề tài và cho ba yêu cầu thiết kế: dùng được mà không nhìn màn hình, luôn có phản hồi bằng lời khi thao tác không thành, và cho người dùng xác nhận mình đang ở đâu trước khi nghe dài (nút "Đang ở đâu" ở mục 4).

**Bài 5. ViOCRVQA (Multimedia Systems 2025).** Bộ dữ liệu hỏi đáp trên ảnh gồm 28.282 bìa sách tiếng Việt và 123.781 cặp câu hỏi, câu trả lời về tên sách, tác giả, nhà xuất bản. Mô hình VisionReader đạt F1 69,90%.

- *Ưu điểm:* bộ dữ liệu bìa sách tiếng Việt lớn nhất; cho thấy vai trò quyết định của OCR (bỏ đặc trưng OCR thì F1 của tên sách giảm 45 điểm).
- *Nhược điểm:* ảnh là ảnh sản phẩm trên web, sạch và chính diện, không phải ảnh chụp bằng điện thoại; chỉ dùng một bộ OCR và không báo cáo tỉ lệ lỗi ký tự; cần GPU A100.
- *Dùng trong đồ án:* nền cho hướng mở rộng "chụp bìa để tìm sách trong thư viện", chưa cài đặt.

**Bài 6. ViTextVQA (ESWA 2025)** và **bài 7. OmniDocBench (CVPR 2025)** được đọc cho hướng OCR ban đầu. Hai điều còn giá trị với đồ án hiện tại: ViTextVQA đo được rằng mất dấu thanh làm chất lượng giảm đơn điệu, tức với tiếng Việt lỗi dấu là lỗi nghĩa, phù hợp với kết quả phân tích lỗi của Piper ở mục 5.2 (22% lỗi chỉ khác thanh điệu); OmniDocBench cho thấy dây chuyền gồm các mô hình nhỏ chuyên biệt thắng mô hình ngôn ngữ thị giác lớn trên trang sách sạch, cùng tinh thần với lựa chọn "mô hình nhỏ, chuyên biệt, chạy được trên CPU" của đồ án. Nhược điểm chung: ViTextVQA không có trang sách và có số liệu mâu thuẫn giữa các bảng; OmniDocBench không có tiếng Việt và không có ảnh chụp bằng điện thoại.

### 2.4. Giải pháp trong nước

- **Nghiên cứu:** chuỗi hội thảo VLSP có nhiệm vụ TTS các năm 2018–2021. Năm 2020 đặt trọng tâm vào ngắt nghỉ ngữ điệu cho câu dài và chuẩn hóa văn bản, đúng hai vấn đề của việc đọc sách.
- **Dịch vụ thương mại:** FPT.AI, Viettel AI, Zalo AI, Vbee đều có giọng ba miền, tính phí theo ký tự.
- **Mã nguồn mở:** các bản F5-TTS tiếng Việt của cộng đồng (cần GPU), viXTTS, VietTTS, và VieNeu-TTS (tự nhận chạy thời gian thực trên CPU, đồ án đã kiểm chứng ở mục 3).
- **Ứng dụng cho người khiếm thị:** Envision đọc được chữ tiếng Việt nhưng giao diện tiếng Anh; SgBE nhận diện tiền và vật thể; Blue Eye là thiết bị riêng; Helen là ứng dụng sách nói do học sinh làm. Sách nói thương mại (Fonos, Voiz FM, Waka) có nội dung bản quyền và không theo chuẩn DAISY.

Thông tin trong mục này lấy từ trang giới thiệu và báo chí, chưa được kiểm chứng độc lập (`literature/notes/10_vietnam_landscape.md` đánh dấu từng chỗ).

### 2.5. Khoảng trống và đóng góp của đồ án

| Khoảng trống | Bằng chứng | Đồ án làm gì |
|---|---|---|
| Chưa có số đo tốc độ TTS tiếng Việt trên CPU | Bài 1, 2, 3 chỉ đo trên GPU hoặc không đo | Đo RTF của Piper và VieNeu-TTS trên CPU, cả khi đo riêng lẫn khi dựng sách thật (mục 3) |
| Đánh giá TTS chỉ dừng ở WER và điểm nghe, chưa gắn với việc nghe sách dài | Bài 2 không đánh giá văn bản dài; bài 1 chỉ nêu tốc độ đọc của dữ liệu | Thêm hai phép đo: tốc độ đọc và tỉ lệ khoảng lặng, giải thích được nhận xét của người nghe mà WER không bắt được (mục 5.1) |
| Chưa có ứng dụng sách nói tiếng Việt điều hướng được ở mức câu, dùng với trình đọc màn hình | Khảo sát trong nước; bài 4 không có thành phần tiếng nói | Ứng dụng Sách Nói (mục 4) |
| Mô hình tự hồi quy có thể đọc sót, người khiếm thị không đối chiếu được bằng mắt | Bài 2, 3 nêu nguy cơ, không có cách phát hiện rẻ | Lưới an toàn theo nhịp đọc (mục 5.3) |

---

## 3. Demo: so sánh các hệ TTS tiếng Việt cho sách nói

### 3.1. Thiết lập

- **Văn bản thử:** 20 đoạn đầu của truyện "Lão Hạc" (Nam Cao), 1.333 âm tiết, gồm cả câu thoại 7 ký tự lẫn đoạn văn 1.309 ký tự.
- **Ba hệ, bảy cấu hình giọng:** Piper (kiến trúc VITS, hai giọng), VieNeu-TTS v3 Turbo (tự hồi quy, bốn giọng), và giọng Hoài My của Microsoft gọi qua thư viện edge-tts.
- **Độ rõ:** cho mô hình nhận dạng tiếng nói `faster-whisper large-v3-turbo` nghe lại audio, so với văn bản gốc sau khi viết thường và bỏ dấu câu, tính WER và CER. Đây là cách bài PhoAudiobook đánh giá. Sai số của bản thân mô hình nhận dạng là như nhau cho mọi giọng nên con số chỉ dùng để so sánh giữa các giọng, không phải độ rõ tuyệt đối.
- **Tốc độ tạo:** RTF bằng thời gian tạo chia cho thời lượng audio.
- **Mã và số liệu gốc:** `demo/tts_bench_piper.py`, `demo/tts_bench_vieneu.py`, `demo/tts_intelligibility.py`, `report/tables/`.

### 3.2. Kết quả

| Hệ TTS | Chạy ở đâu | Tốc độ tạo | WER | CER |
|---|---|---|---|---|
| edge-tts, giọng Hoài My | Dịch vụ của Microsoft | Phụ thuộc dịch vụ, xem mục 5.4 | 5,25% | 2,21% |
| Piper `vais1000-medium` | CPU | Nhanh gấp 27–40 lần thời gian thực | 9,98% | 5,00% |
| Piper `25hours_single-low` | CPU | Nhanh gấp khoảng 9 lần | 38,11% | 21,75% |
| VieNeu-TTS, Ngọc Linh (nữ) | CPU | Nhanh gấp 1,1–1,6 lần | 5,10% | 2,19% |
| VieNeu-TTS, Thiện Minh (nam) | CPU | Nhanh gấp 1,3–1,6 lần | 5,40% | 2,97% |
| VieNeu-TTS, Quỳnh Anh (nữ) | CPU | Nhanh gấp 1,2 lần | 4,20% | 1,79% |
| VieNeu-TTS, Ngọc Huyền (nữ) | CPU | Nhanh gấp 1,2 lần | 4,43% | 2,43% |

Khi dựng sách thật, không có tiến trình khác tranh CPU, Piper đạt RTF 0,025–0,037 (57,7 phút audio của chín chương đầu "Tắt đèn" tạo trong 93 giây). VieNeu-TTS đạt RTF 0,62 khi đọc từng câu (9,1 phút audio của "Gió lạnh đầu mùa" tạo trong 340 giây).

### 3.3. Ba phát hiện

1. **Một giọng Piper tiếng Việt không có thanh điệu.** Bảng ký hiệu âm vị của giọng `25hours_single-low` thiếu các ký hiệu thanh điệu: 806 trên 8.068 âm vị của văn bản thử (10,0%) bị bỏ khi đưa vào mô hình, và toàn bộ số bị bỏ là ký hiệu thanh. WER lên 38%. Bài học: chọn giọng cho tiếng Việt phải kiểm tra bảng ký hiệu của mô hình, không chỉ nhìn tên ngôn ngữ.
2. **VieNeu-TTS chạy được trên CPU nhanh hơn thời gian thực**, đúng như dự án tự nhận, với độ rõ ngang giọng thương mại của Microsoft. Nhưng nó không tăng tốc được bằng cách chạy song song trên máy này: một tiến trình đạt RTF 0,74, hai tiến trình cùng lúc đạt RTF 1,74 mỗi tiến trình.
3. **WER không phản ánh hết chất lượng nghe.** Piper có WER gấp đôi nhưng lý do người nghe thử chê nó là ngữ điệu, điều WER không đo. Mục 5.1 phân tích tiếp.

### 3.4. Trang nghe thử

Để chọn giọng bằng tai chứ không chỉ bằng số, đồ án dựng một trang nghe thử phát cùng các đoạn văn bằng từng giọng (`demo/make_listen_page.py`, đã đưa lên ở đường dẫn `/nghe-thu/` của trang sản phẩm). Người nghe ở đây là chính học viên, không phải một nhóm chấm điểm mù.

---

## 4. Ứng dụng Sách Nói

### 4.1. Kiến trúc

```
Wikisource (phạm vi công cộng)
   │  import_wikisource.py     lấy văn bản, tách đoạn, gán id; kiểm tra nhãn phạm vi công cộng
   ▼
books/<slug>/build/chapter_NN/segments.json + dtbook.xml
   │  tts_chapter_edge.py      đọc từng đoạn văn, lấy mốc từng câu
   │  gen_smil.py, gen_opf_ncx.py, validate_daisy.py     bộ file DAISY 3 và kiểm tra chéo
   ▼
books/<slug>/voices/<giọng>/   mỗi giọng đọc là một bản DAISY đầy đủ
   │  build_site.py            danh mục + dữ liệu cho ứng dụng
   ▼
site/ ─► deploy_site.py ─► GitHub Pages
```

Ứng dụng là trang web tĩnh viết bằng HTML, CSS và JavaScript thuần (không dùng khung giao diện), cài được lên màn hình chính như một ứng dụng (PWA). Lý do chọn web thay cho ứng dụng gốc: chạy ngay trên mọi điện thoại không cần cài qua kho ứng dụng, triển khai bằng GitHub Pages không tốn chi phí máy chủ, và trình đọc màn hình của cả Android lẫn iOS đều hỗ trợ tốt nội dung web có đánh dấu ngữ nghĩa. Cái giá là không dùng được một số khả năng của hệ điều hành (ví dụ phím âm lượng làm cử chỉ).

**Cài lên điện thoại.** Có ba cách, đều ghi trong mục Cài ứng dụng của trang Hướng dẫn. Trên Android, người dùng tải file `SachNoi.apk` ngay từ trang; đây là bản đóng gói Trusted Web Activity dựng bằng Bubblewrap (`app/android`), nặng chưa tới 1 MB vì nó chỉ mở trang web trong Chrome ở chế độ toàn màn hình, nhờ vậy mọi cập nhật của trang có ngay trong ứng dụng mà không phải dựng lại APK. Cũng trên Android có thể chọn Thêm vào màn hình chính trong Chrome. Trên iPhone và iPad, người dùng mở trang bằng Safari rồi chọn Thêm vào Màn hình chính; đồ án không có bản cài riêng cho iOS vì việc đó cần máy Mac và tài khoản Apple Developer. Hai giới hạn: APK còn hiện một thanh địa chỉ mỏng do chưa đặt được file `assetlinks.json` ở gốc tên miền, và cả ba cách cài chưa được thử trên điện thoại thật.

Mỗi cuốn sách vẫn là một bộ DAISY 3 hợp lệ (DTBook, SMIL, OPF, NCX), mở được bằng phần mềm đọc DAISY khác. Ứng dụng đọc một bản rút gọn dạng JSON sinh từ chính bộ DAISY đó để tải nhanh trên điện thoại.

### 4.2. Thư viện

Thư viện gồm 15 đầu sách. Mười bốn cuốn dựng trong đồ án này có 115 phần, tổng cộng 974 phút âm thanh (khoảng 16 giờ), tất cả đã nghe được trên trang sản phẩm:

| Thể loại | Sách |
|---|---|
| Truyện ngắn | Lão Hạc, Chí Phèo (Nam Cao); Hai đứa trẻ, Gió lạnh đầu mùa, Cô hàng xén, Dưới bóng hoàng lan (Thạch Lam) |
| Tiểu thuyết | Tắt đèn (Ngô Tất Tố), 27 chương |
| Tùy bút | Hà Nội băm sáu phố phường (Thạch Lam), 21 bài |
| Thơ | Truyện Kiều (Nguyễn Du), 13 phần; Thơ Hàn Mặc Tử, 4 phần |
| Ngâm khúc | Chinh phụ ngâm (Đặng Trần Côn, bản diễn Nôm tương truyền của Đoàn Thị Điểm), 4 phần |
| Truyện truyền kỳ | Truyền kỳ mạn lục (Nguyễn Dữ, Ngô Văn Triện dịch), 20 truyện |
| Lịch sử | Việt Nam sử lược (Trần Trọng Kim), lời tựa và hai phần đầu, 12 mục |
| Khảo cứu | Việt Nam phong tục (Phan Kế Bính), 8 mục đầu |
| Thiếu nhi | Totto-chan bên cửa sổ, cuốn của đồ án giữa kỳ, mở bằng trình phát cũ |

**Bản quyền.** Mười bốn cuốn mới đều lấy từ Wikisource tiếng Việt và thuộc phạm vi công cộng theo Luật Sở hữu trí tuệ (suốt đời tác giả cộng 50 năm). Bộ nhập sách từ chối trang không có nhãn phạm vi công cộng. Các tựa trong danh sách tài liệu của lớp còn bản quyền (Dế Mèn phiêu lưu ký, Vang bóng một thời...) và các truyện cổ tích không rõ nguồn bản kể không được đưa vào; căn cứ từng cuốn ghi ở `books/README.md`. Totto-chan còn bản quyền, chỉ được giữ dưới dạng liên kết tới trang giữa kỳ đã nộp. Bìa sách dựng từ ảnh thuộc phạm vi công cộng hoặc giấy phép mở trên Wikimedia Commons, có ghi nguồn trong ứng dụng.

**Giới hạn dung lượng.** GitHub Pages giới hạn 1 GB; trang giữa kỳ đã chiếm 410 MB và bản hiện tại dùng 986 MB. Vì vậy Việt Nam sử lược và Việt Nam phong tục chỉ có phần đầu, và các sách dài thêm sau không kèm file zip DAISY tải về.

### 4.3. Tính năng

**Nghe và điều hướng**
- Văn bản hiện cùng âm thanh, câu đang đọc được tô sáng; chạm vào một câu để nghe từ câu đó.
- Một cặp nút lùi và tới với **bước nhảy chọn được**: câu, đoạn, 30 giây, phần, dấu trang. Đây là cách các máy đọc sách cho người mù (Victor Reader Stream) tổ chức điều hướng.
- Tốc độ từ 0,5 đến 3 lần, nhớ riêng cho từng cuốn. Người dùng trình đọc màn hình lâu năm thường nghe ở tốc độ rất cao.
- Nhớ vị trí từng cuốn, mục "Nghe tiếp" ở đầu thư viện; tự chuyển sang phần sau khi hết phần.
- Đánh dấu trang, có thể kèm ghi chú bằng giọng nói của người dùng.
- Nút **Quay lại** để hủy cú nhảy vừa rồi, kể cả khi đã nhảy sang phần khác.
- Hẹn giờ tắt theo phút hoặc khi hết phần.
- **Lùi về đầu câu khi nghe tiếp:** sau khi dừng hơn 20 giây hoặc khi mở lại sách, ứng dụng phát lại từ đầu câu đang nghe dở (câu mới nghe chưa tới 2 giây thì lùi thêm một câu) để người nghe bắt lại mạch. Nhờ có mốc thời gian từng câu nên lùi theo câu, không lùi theo số giây cố định như BARD Mobile. Tắt được trong Cài đặt.
- **Tìm trong sách:** ở trang bìa, gõ một từ hoặc một câu, không cần gõ dấu; ứng dụng tìm trong văn bản của mọi phần, báo số câu tìm thấy bằng lời và mở đúng câu được chọn.

**Dùng không cần nhìn**
- **Chế độ chạm đơn giản:** trình đọc màn hình bắt người dùng vuốt qua từng phần tử rồi nhấp đôi, nên một trang nhiều nút rất tốn thao tác. Chế độ này thay cả màn hình bằng năm hoặc sáu nút rất lớn ở vị trí cố định (nhắc lại và hướng dẫn, lùi, tới, nghe hoặc tạm dừng, đổi sách), chạm một lần là chạy, không cuộn, không vuốt. Khi đang nghe có thêm một nút đổi chức năng của hai nút lùi và tới giữa năm mức: 30 giây, chọn phần, đổi tốc độ, dấu trang (đánh dấu và đi tới dấu trang), hẹn giờ tắt; đây là cách máy đọc sách Victor Reader giữ ít phím mà đủ việc. Ứng dụng tự đọc lời nhắc và hướng dẫn bằng chính giọng đọc sách (Hoài My) và vặn nhỏ tiếng sách trong lúc đọc, nên dùng được cả khi không bật trình đọc màn hình. Bản đầu dùng giọng tiếng Việt của máy (Web Speech API), nhưng máy không cài giọng tiếng Việt thì trình duyệt đọc chữ Việt bằng giọng tiếng Anh. Vì vậy mọi lời nhắc được viết lại thành các câu ngắn lấy giá trị từ tập đếm được (tên sách, tên phần, số phút, tốc độ), khoảng 1.200 câu, thu sẵn bằng edge-tts (`pipeline/scripts/build_prompts.py`) và phát nối nhau; câu nào không có bản thu thì mới dùng giọng của máy, và máy không có giọng tiếng Việt thì hiện bằng chữ. Lựa chọn được ghi nhớ cho lần mở sau.
- Mọi nút có nhãn bằng lời; mọi thay đổi trạng thái (đổi bước nhảy, tới đầu hoặc cuối sách, đã đánh dấu) được báo qua vùng thông báo cho trình đọc màn hình, kèm tiếng báo hiệu ngắn có thể tắt.
- Nút **Đang ở đâu** đọc tên sách, tên phần, thời điểm, thời gian còn lại và tốc độ.
- Thứ tự đọc của trang đặt nút điều khiển trước nội dung sách, để người dùng trình đọc màn hình không phải vuốt qua cả chương mới tới nút phát.
- Đang tạm dừng mà nhảy câu thì ứng dụng đọc câu đó lên, cho phép dò từng câu.
- Phím tắt cho mọi thao tác và một trang hướng dẫn trong ứng dụng.
- Tìm sách bằng cách gõ tên, tác giả, thể loại, hoặc bằng giọng nói (nếu trình duyệt hỗ trợ nhận dạng tiếng nói); chọn thể loại từ danh sách.
- **Điều khiển bằng giọng nói:** bấm nút micro một lần, nghe tiếng báo rồi nói một lệnh tiếng Việt: phát, tạm dừng, lùi hoặc tới kèm số giây hay số phút, câu trước, câu sau, phần trước, phần sau, phần số mấy, nhanh hơn, chậm hơn, đánh dấu, tới dấu trang, hẹn giờ kèm số phút, đang ở đâu, thư viện, mở kèm tên sách hoặc tên tác giả. Ứng dụng dùng nhận dạng tiếng nói của trình duyệt (Web Speech API, `vi-VN`) rồi tự hiểu lệnh bằng luật: so khớp từ khoá trên câu đã bỏ dấu để chịu được lỗi dấu, nhưng đọc số trên câu còn dấu để phân biệt "phần sáu" với "phần sau". Chọn cách bấm rồi nói thay vì luôn lắng nghe vì micro sẽ thu lẫn tiếng sách; trong lúc nghe lệnh sách tạm dừng rồi tự phát tiếp. Nút có ở giao diện đầy đủ và ở hàng dưới cùng của chế độ chạm đơn giản, nơi câu trả lời phát bằng bản thu sẵn giọng Hoài My. Tính năng cần mạng và chỉ hiện khi trình duyệt hỗ trợ.

**Dùng với thị lực kém**
- Ba nền (giấy, tối, tương phản cao), bốn cỡ chữ, một kiểu chữ dễ đọc; câu đang đọc được tô bằng một trong ba màu, gạch chân, hoặc không tô.
- Vùng chạm tối thiểu 44 điểm ảnh, bố cục đã kiểm tra tới màn hình rộng 320 điểm ảnh.

**Di động**
- Điều khiển phát từ màn hình khóa và tai nghe (Media Session), có ảnh bìa.
- Lưu từng cuốn để nghe khi mất mạng (âm thanh lưu trong IndexedDB); cài lên màn hình chính.

Danh sách tính năng điều hướng được lập bằng cách đối chiếu với BARD Mobile, Legimus, Voice Dream Reader, Victor Reader Stream và các tiêu chí của DAISY Consortium, rồi bổ sung những gì còn thiếu (17/11). Lần đối chiếu thứ hai (20/11, thêm Dolphin EasyReader) bổ sung bước nhảy theo dấu trang, tốc độ 0,5 lần, lùi về đầu câu khi nghe tiếp, tìm trong sách, và đưa dấu trang cùng hẹn giờ tắt vào chế độ chạm đơn giản. Những gì các ứng dụng đó có mà Sách Nói chưa có: chỉnh âm sắc, ra lệnh bằng giọng nói khi đang nghe, mở sách của riêng người dùng.

### 4.4. Kiểm thử

- **Cấu trúc DAISY:** `validate_daisy.py` kiểm tra chéo cho từng phần của từng cuốn: mọi đoạn trong DTBook có mốc trong SMIL, mốc thời gian tăng dần và nằm trong thời lượng file âm thanh, OPF và NCX khớp nhau. Mọi phần đã dựng đều qua.
- **Giao diện:** 160 kiểm thử đầu-cuối chạy trên Chromium qua Playwright ở kích thước màn hình điện thoại (`app/tests/e2e.py`). Chúng kiểm tra hành vi thật chứ không chỉ sự tồn tại của nút: ví dụ nhảy 30 giây thì thời điểm phát tăng trong khoảng 29,5 đến 32 giây; chọn thể loại "Thơ" thì thư viện chỉ còn đúng các tập thơ; ghi âm ghi chú bằng micro giả rồi kiểm tra dữ liệu âm thanh đã nằm trong bộ nhớ của máy.
- **Giới hạn của kiểm thử tự động:** nó xác nhận nhãn, vai trò, thứ tự và thông báo có mặt trong trang, không xác nhận TalkBack hay VoiceOver đọc chúng ra sao. Việc này chưa được làm (mục 6).

---

## 5. Phân tích sâu: chọn và cải tiến bước TTS cho sách nói tiếng Việt

Bước được chọn để phân tích là tổng hợp tiếng nói, vì nó quyết định cả chất lượng nghe lẫn khả năng mở rộng thư viện. Trong hai tuần, giọng đọc của thư viện đã đổi ba lần; mỗi lần đổi đều có số liệu và lý do.

### 5.1. Vì sao giọng nhanh nhất không dùng được: phép đo mà WER bỏ sót

Lựa chọn đầu tiên là Piper: chạy trên CPU nhanh gấp 27–40 lần thời gian thực, không phụ thuộc mạng, WER 10%. Cả thư viện dựng xong trong vài phút. Nhưng nghe thử thì ngữ điệu kém giọng Hoài My của bản giữa kỳ rõ rệt, điều mà WER (chỉ đo từng từ có nghe ra hay không) không thể hiện.

Hai phép đo bổ sung trên cùng 20 đoạn:

| Giọng | Tốc độ đọc (âm tiết/phút) | Tốc độ lúc đang phát âm | Phần thời gian là khoảng lặng |
|---|---|---|---|
| Hoài My (edge-tts) | 186 | 286 | 34,8% |
| Piper vais1000 | 275 | 295 | 6,7% |
| VieNeu Ngọc Linh | 241 | 284 | 15,1% |
| VieNeu Thiện Minh | 254 | 321 | 20,7% |

Lúc đang phát âm, các giọng nói nhanh gần như nhau (284–321 âm tiết mỗi phút). Khác biệt nằm ở khoảng lặng: Piper **gần như không ngắt nghỉ** (6,7% thời gian), còn Hoài My dành hơn một phần ba thời gian cho chỗ nghỉ. Giải thích hợp lý là mô hình VITS nhỏ, huấn luyện trên khoảng một nghìn câu đọc rời, không học được chỗ nghỉ ở dấu phẩy và giữa các ý. Với sách nói, chỗ nghỉ là lúc người nghe kịp hiểu; tốc độ đọc của Piper cũng cao hơn nhiều so với mốc 201 của bộ sách nói PhoAudiobook.

Khoảng lặng được tính bằng ngưỡng năng lượng đơn giản (khung 20 ms có RMS dưới 1% mức đỉnh) nên chỉ dùng để so tương đối; file của edge-tts còn có khoảng lặng đệm ở hai đầu mỗi đoạn.

### 5.2. Lỗi của Piper nằm ở đâu

Phân tích 113 cặp từ mà mô hình nhận dạng nghe khác văn bản gốc trên audio của Piper:

- 25 cặp (22%) **chỉ khác thanh điệu**: "vả" thành "và", "mồi" thành "môi". Đây là điểm yếu thật của giọng đọc và là loại lỗi làm sai nghĩa trong tiếng Việt.
- Nhầm phụ âm cuối và phụ âm đầu: "hạc" thành "hạt", "gắp" thành "gắt".
- 8 cặp không phải lỗi phát âm mà là mô hình nhận dạng viết "ba" thành "3"; các cặp này cũng xuất hiện với Hoài My, nên WER thật của mọi giọng thấp hơn bảng một chút.

### 5.3. Cải tiến thứ nhất: VieNeu-TTS và lưới an toàn bắt câu đọc sót

VieNeu-TTS giải quyết được vấn đề ngữ điệu (khoảng lặng 15–21%, WER 4,2–5,4%) mà vẫn chạy trên CPU. Cái giá:

- Chậm hơn Piper 20–40 lần: dựng hai giọng cho thư viện khi đó (khoảng 3,6 giờ audio mỗi giọng) mất nhiều giờ. Việc dựng được chuyển thành hàng đợi chạy tiếp được sau khi ngắt và đưa lên trang dần theo từng phần (`build_voices.py`).
- **Có thể đọc sót.** Là mô hình tự hồi quy sinh mẫu ngẫu nhiên, nó đôi khi bỏ mất vài từ; trong 20 đoạn thử, giọng Thiện Minh bỏ một cụm ở một câu. Với người nghe khiếm thị, đây là lỗi nghiêm trọng vì họ không đối chiếu được bằng mắt.

Cách phát hiện chuẩn là cho mô hình nhận dạng nghe lại từng câu, nhưng việc đó làm thời gian dựng tăng gần gấp đôi. Đồ án đề xuất và cài đặt một **lưới an toàn theo nhịp đọc**, không tốn thêm thời gian: tính số giây mỗi âm tiết của từng câu; câu nào lệch khỏi trung vị của chương quá khoảng 0,65 đến 1,6 lần thì sinh lại. Đo trên một truyện thật, mọi câu bình thường nằm trong khoảng 0,8 đến 1,3 lần, nên ngưỡng này không bắt nhầm. Phương án kiểm tra bằng nhận dạng tiếng nói vẫn có sẵn qua tùy chọn `--verify`.

**Giới hạn:** tỉ lệ đọc sót trước và sau khi có lưới an toàn chưa được đo trên cả một cuốn sách, nên hiệu quả của lưới mới được kiểm trên các trường hợp đã biết.

### 5.4. Cải tiến thứ hai: giọng dịch vụ với mốc câu lấy từ mốc từ

Sau khi nghe cả thư viện bằng hai giọng VieNeu, lựa chọn cuối cùng (16/11) vẫn là giọng Hoài My vì ngữ điệu. Số liệu không phản bác lựa chọn này: Hoài My có WER ngang VieNeu và là giọng ngắt nghỉ nhiều nhất. Trở ngại trước đó của edge-tts là độ tin cậy và việc mất đồng bộ mức câu, không phải chất lượng. Đồ án giải quyết hai trở ngại đó như sau.

**Giữ đồng bộ mức câu mà không cần mô hình căn chỉnh.** Bản giữa kỳ gửi cả đoạn văn cho dịch vụ và chỉ có mốc mức đoạn. Cách dễ nhất để có mốc câu là gửi từng câu, nhưng như vậy số yêu cầu tăng khoảng 5 lần và ngữ điệu liên câu bị mất. Cách đã cài đặt (`tts_chapter_edge.py`): vẫn gửi cả đoạn, yêu cầu dịch vụ trả về sự kiện mốc từng từ (WordBoundary), rồi gán lần lượt các từ vào các câu theo số từ của mỗi câu để ra mốc đầu và mốc cuối của câu. Hai cách tách từ (của dịch vụ và của dây chuyền) được so khớp; nếu không khớp thì đoạn đó lùi về chia thời lượng theo số ký tự. Trong lần dựng Chí Phèo, 5 trên 150 đoạn phải lùi về cách này.

Cùng cơ chế đếm từ đó phát hiện được **audio bị cụt**: dịch vụ đôi khi trả về âm thanh thiếu vài từ cuối. Nếu số từ nhận về ít hơn số từ gửi đi thì đoạn được tải lại.

**Tăng độ bền khi gọi dịch vụ.** Đo ngày 18/11: mỗi lần gọi hỏng với xác suất khoảng ba phần tư, bất kể đã chờ bao lâu giữa hai lần gọi. Vì vậy chiến lược chờ lâu dần của bản trước chỉ làm chậm. Ba thay đổi:

| Thay đổi | Kết quả đo |
|---|---|
| Thử lại sau 0,5 giây thay cho chờ lâu dần; tải nhiều đoạn cùng lúc | Từ 1,4 lên khoảng 12 đoạn mỗi phút khi tải 4 đoạn cùng lúc, 18 đoạn mỗi phút khi tải 8 |
| Giới hạn thời gian cho mỗi yêu cầu | Hết hiện tượng một kết nối treo im lặng hàng chục phút |
| Đoạn hỏng 10 lần liên tiếp thì chia đôi theo ranh giới câu, tải từng nửa rồi ghép, cộng dồn mốc thời gian | Một đoạn 2.365 ký tự của Chí Phèo bị từ chối suốt hơn một giờ đã dựng được; mốc câu qua chỗ ghép vẫn liền mạch |

**Cái giá còn lại:** bước dựng phụ thuộc một dịch vụ không chính thức, không có cam kết. Người nghe không bị ảnh hưởng vì âm thanh được dựng sẵn; hai bản VieNeu được giữ làm đường lùi, và ứng dụng tự phát giọng dự phòng (kèm lời báo) cho phần chưa có giọng chính.

### 5.5. So sánh ba phương án

| Tiêu chí | Piper | VieNeu-TTS | Hoài My (edge-tts) |
|---|---|---|---|
| WER trên văn bản thử | 9,98% | 4,2–5,4% | 5,25% |
| Khoảng lặng | 6,7% | 15–21% | 34,8% |
| Tốc độ dựng | Gấp 27–40 lần thời gian thực | Gấp 1,1–1,6 lần | Phụ thuộc dịch vụ |
| Cần mạng khi dựng | Không | Không | Có |
| Nguy cơ sai nội dung | Sai thanh điệu | Đọc sót từ | Audio cụt (đã có kiểm tra) |
| Kích thước mô hình | 63 MB | 541 MB | Không áp dụng |
| Vai trò hiện tại | Giọng dự phòng | Giọng dự phòng, đối chứng | Giọng của thư viện |

Kết luận của phần phân tích: với sách nói, tiêu chí xếp hạng các hệ TTS không phải chỉ là WER và tốc độ như trong các bài báo đã đọc. Ngắt nghỉ và độ an toàn nội dung (không sót, không cụt) quan trọng ngang độ rõ, và cả hai đo được bằng công cụ rẻ: tỉ lệ khoảng lặng, nhịp đọc theo âm tiết, và phép đếm từ.

### 5.6. Đề xuất cải tiến chưa thực hiện

1. **Chuẩn hóa văn bản trước TTS.** Số La Mã, ngày tháng, chữ viết tắt và lối viết gạch nối kiểu cũ ("Hồng-bàng") hiện được đọc nguyên trạng. Cần một bộ luật chuẩn hóa và phép đo WER trước, sau trên các câu có số.
2. **Thơ.** Thơ lục bát và song thất lục bát hiện được ghép bốn câu thành một đoạn và hiển thị liền dòng như văn xuôi. Nên giữ xuống dòng theo câu thơ và thử thêm chỗ nghỉ ở cuối mỗi câu.
3. **Điểm nghe chủ quan.** Chưa có phép chấm mù (MOS) với nhiều người nghe; lựa chọn giọng hiện dựa trên số đo khách quan và tai của một người.
4. **Câu thoại rất ngắn** ("Vâng!", "Này!") chỉ dài khoảng 0,2 giây với Piper, nghe cụt; hiện tượng cùng loại với lỗi câu ngắn mà PhoAudiobook báo cáo ở XTTS-v2.
5. **F5-TTS tiếng Việt** chưa được so sánh vì cần GPU.

---

## 6. Hạn chế

- **Chưa thử với người khiếm thị**, và chưa thử trên điện thoại thật với TalkBack hoặc VoiceOver. Mọi kiểm tra trợ năng đến nay là kiểm thử tự động trên Chromium ở kích thước màn hình điện thoại. Đây là hạn chế lớn nhất của đồ án.
- Micro thật và nhận dạng tiếng nói thật (cho tìm kiếm, ra lệnh và ghi chú bằng giọng nói) chưa được thử; kiểm thử dùng thiết bị giả và đưa thẳng câu chữ vào bộ hiểu lệnh. Vì vậy chưa biết tỉ lệ nhận đúng lệnh khi người thật nói, nhất là trong môi trường ồn hoặc với giọng địa phương.
- Giọng Hoài My chưa được nghe kiểm tra trên các thể loại mới thêm (thơ, văn bản có nhiều từ Hán Việt gạch nối).
- Phép đo TTS chỉ trên một văn bản (20 đoạn của một truyện), một lần chạy cho mỗi giọng.
- Chữ Hán, chữ Nôm và chú thích trong Truyền kỳ mạn lục, Việt Nam sử lược bị lược bỏ khi nhập; vài chỗ còn lỗi chính tả của bản số hóa trên Wikisource.
- Thư viện bị chặn bởi giới hạn 1 GB của nơi lưu trữ.

## 7. Kết luận

Đồ án nối tiếp đồ án giữa kỳ thành một dây chuyền hoàn chỉnh từ văn bản thuộc phạm vi công cộng tới sách nói DAISY nghe được trên điện thoại, và cho thấy bằng số liệu rằng việc chọn hệ TTS cho sách nói cần những phép đo ngoài WER. Ứng dụng đã chạy công khai với 15 đầu sách và đã có bộ kiểm thử tự động; bước còn thiếu để gọi nó là dùng được cho người khiếm thị là thử nghiệm với chính họ.

## Tài liệu tham khảo

1. Thi Vu, Linh The Nguyen, Dat Quoc Nguyen. Zero-Shot Text-to-Speech for Vietnamese. ACL 2025 (Short Papers), tr. 1042–1049.
2. Yushen Chen, Zhikang Niu, Ziyang Ma, Keqi Deng, Chunhui Wang, Jian Zhao, Kai Yu, Xie Chen. F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching. ACL 2025 (Long Papers), tr. 6255–6271.
3. Shengpeng Ji và cộng sự. MobileSpeech: A Fast and High-Fidelity Framework for Mobile Zero-Shot Text-to-Speech. ACL 2024 (Long Papers).
4. Xin Jiang, Junwei Zheng, Ruiping Liu, Jiahang Li, Jiaming Zhang, Sven Matthiesen, Rainer Stiefelhagen. @BENCH: Benchmarking Vision-Language Models for Human-centered Assistive Technology. WACV 2025, tr. 3934–3943.
5. Huy Quang Pham, Thang Kien-Bao Nguyen, Quan Van Nguyen, Dan Quang Tran, Nghia Hieu Nguyen, Kiet Van Nguyen, Ngan Luu-Thuy Nguyen. ViOCRVQA: Novel Benchmark Dataset and Vision Reader for Visual Question Answering by Understanding Vietnamese Text in Images. Multimedia Systems, 2025.
6. Quan Van Nguyen, Dan Quang Tran, Huy Quang Pham, Thang Kien-Bao Nguyen, Nghia Hieu Nguyen, Kiet Van Nguyen, Ngan Luu-Thuy Nguyen. ViTextVQA: A Large-Scale Visual Question Answering Dataset for Evaluating Vietnamese Text Comprehension in Images. Expert Systems with Applications, 2025.
7. Linke Ouyang và cộng sự. OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations. CVPR 2025.
8. Anh Le, Thanh Lam, Dung Nguyen. A Survey on Vietnamese Document Analysis and Recognition. arXiv:2506.05061, 2025.
9. DAISY Consortium. ANSI/NISO Z39.86-2005 (R2012), Specifications for the Digital Talking Book.

## Phụ lục: chạy lại

```bash
python3 -m venv .venv
.venv/bin/pip install piper-tts vieneu lameenc numpy mutagen edge-tts playwright faster-whisper jiwer pillow

# thêm một cuốn sách thuộc phạm vi công cộng rồi dựng giọng đọc
python3 pipeline/scripts/import_wikisource.py --slug lao-hac --author "Nam Cao" --year 1943 "Lão Hạc"
.venv/bin/python pipeline/scripts/build_voices.py lao-hac

# lắp trang, chạy thử và kiểm thử trên máy
python3 pipeline/scripts/build_site.py
python3 app/tests/serve.py 8931 &
.venv/bin/python app/tests/e2e.py http://127.0.0.1:8931/
```

Nhật ký quyết định thiết kế đầy đủ: `report/decisions.md`. Số liệu so sánh TTS: `report/tts_comparison.md` và `report/tables/`.
