# Zero-Shot Text-to-Speech for Vietnamese (PhoAudiobook)

**Venue:** ACL 2025 (Volume 2: Short Papers, tr. 1042–1049) | **Hạng:** CORE A* | **Năm:** 2025 | **Tác giả/nhóm:** Thi Vu, Linh The Nguyen, Dat Quoc Nguyen – Movian AI, Vietnam (bài ghi Movian AI, không ghi VinAI) | **Link:** dataset https://huggingface.co/datasets/thivux/phoaudiobook ; baseline viXTTS https://huggingface.co/capleaf/viXTTS

**Tóm tắt 3 câu:** Bài giới thiệu PhoAudiobook, bộ dữ liệu TTS tiếng Việt 941 giờ, 735 người nói, xây dựng tự động từ sách nói với các mẫu dài 10–20 giây và transcript đã chuẩn hóa. Nhóm huấn luyện ba mô hình zero-shot TTS (VALL-E, VoiceCraft, XTTS-v2) trên PhoAudiobook và so với baseline viXTTS (XTTS-v2 fine-tune trên viVoice). XTTS-v2 huấn luyện trên PhoAudiobook thắng viXTTS trên mọi metric và test set, còn VALL-E/VoiceCraft bền hơn với câu ngắn (VIVOS).

## 1. Bài toán & động cơ
- Zero-shot TTS (tổng hợp giọng người nói chưa thấy từ vài giây audio tham chiếu) đã tiến xa với các mô hình kiểu language model trên token codec, nhưng với ngôn ngữ ít tài nguyên như tiếng Việt vẫn kém vì thiếu dữ liệu lớn và sạch.
- Các bộ dữ liệu tiếng Việt hiện có (VinBigData, VietnamCeleb, VLSP 2020, BUD500, viVoice) chủ yếu là mẫu ngắn dưới 10 giây, thiếu speaker ID, thiếu chuẩn hóa văn bản hoặc âm lượng không đồng đều.
- Đóng góp: (1) PhoAudiobook 941 giờ dạng long-form, pipeline tái dùng được cho ngôn ngữ khác; (2) benchmark 3 mô hình zero-shot TTS với metric khách quan + chủ quan; (3) công bố dữ liệu cho mục đích phi thương mại.

## 2. Phương pháp
Đây là dataset paper + benchmark, không đề xuất kiến trúc mới. Pipeline tạo dữ liệu (Hình 1):
1. Cào audio sách nói từ sachnoiviet.net: 23K giờ, 2.697 sách, 735 người đọc.
2. Tách giọng khỏi nhạc nền bằng **demucs**.
3. **Whisper-large-v3** sinh transcript + timestamp; ghép các đoạn liên tiếp thành mẫu **10–20 giây**.
4. Chạy lại bằng **PhoWhisper-large**, chỉ giữ mẫu mà hai transcript khớp **chính xác**.
5. Lọc audio nhiều người nói bằng **wav2vec2-bartpho**.
6. Bỏ mẫu có transcript dưới 25 từ, cắt khoảng lặng, chuẩn hóa âm lượng bằng **sox**.
7. **Chuẩn hóa văn bản** (lowercase, thêm dấu câu, số → chữ, "43" → "bốn mươi ba") bằng seq2seq fine-tune từ **mbart-large-50** trên `nguyenvulebinh/spoken_norm_pattern`.

Huấn luyện (Phụ lục A):
- **VALL-E**: phoneme hóa bằng `phonemizer` theo phương ngữ từng người nói (bộ phân loại phương ngữ fine-tune từ wav2vec2-large-vi, chính xác ~95%); 12 lớp Transformer decoder, 1024 hidden, 16 head; batch tối đa 40 s audio, lr 0.05; **8 A100-40GB**; repo `lifeiteng/vall-e`.
- **VoiceCraft**: từ checkpoint `830M_TTSEnhanced`, mở rộng embedding với phoneme tiếng Việt; AdamW lr 1e-5, batch 25.000 token (~8,3 phút audio); **4 A100-40GB**, 16 epoch; repo `jasonppy/VoiceCraft`.
- **XTTS-v2**: fine-tune checkpoint công khai 16 ngôn ngữ theo recipe `coqui-ai/TTS`, dùng token list tiếng Việt của viXTTS, nới giới hạn độ dài lên 20 s; AdamW lr 5e-6, batch 4, **1 A100-40GB**, 18 epoch.
- Chọn checkpoint có loss tốt nhất trên tập validation.

## 3. Dữ liệu & thiết lập thí nghiệm
- Pipeline cho 1.400 giờ; giới hạn **4 giờ/người** → **941 giờ, 735 người**. Chia theo người nói: train **940 h / 710 người**, validation 0,5 h / 5 người, test "unseen" **0,4 h / 20 người** (ít audio nhất); test "seen" 0,8 h / 20 người lấy từ 559 giờ dư. Hai tập test được soát thủ công, transcript đúng 100%.
- Tăng cường: chạy lại pipeline trên 940 giờ nhưng bỏ bước ghép đoạn và bỏ lọc mẫu ngắn → thêm **554 giờ** clip ngắn, tổng **1.494 giờ** huấn luyện.
- Bảng 1: PhoAudiobook mean 11,66 s (25%: 10,63 s, 75%: 12,18 s), SI-SNR **4,91 dB** (cao nhất), 201 wpm (chậm nhất), 16 kHz. viVoice 1.016 h, mean 4,12 s, SI-SNR 4,81 dB, 243 wpm, 24 kHz, không speaker ID thật, không chuẩn hóa text. Các bộ khác 101–462 h.
- Baseline: **viXTTS** (XTTS-v2 fine-tune trên toàn bộ viVoice).
- Test set: PAB-S, PAB-U, **VIVOS** (0,75 h, 19 người, câu ngắn), **viVoice** (8 người, 0,5 h – nằm trong dữ liệu huấn luyện của viXTTS).
- Metric: WER (ASR PhoWhisper-large), MCD (pymcd), RMSE_F0 (Amphion), MOS, SMOS thang 1–5 bước 0,5; 10 người bản ngữ chấm PAB-S/PAB-U, 20 người chấm VIVOS/viVoice; chấm mù.

## 4. Kết quả chính
Bảng 2 của bài (PAB = huấn luyện trên PhoAudiobook; "Original" là audio gốc):

| Metric | Model | PAB-S | PAB-U | VIVOS | viVoice |
|---|---|---|---|---|---|
| WER ↓ | Original | 0,88 | 0,83 | 5,14 | 4,97 |
| | VALL-E_PAB | 24,96 | 12,90 | 12,63 | 13,58 |
| | VoiceCraft_PAB | 7,53 | 15,14 | 13,53 | 21,70 |
| | XTTS-v2_PAB | **4,16** | **4,31** | 37,81 | **8,32** |
| | viXTTS | 4,23 | 5,17 | 37,81 | 12,54 |
| MCD ↓ | VALL-E_PAB | 7,50 | 8,28 | 10,13 | 8,70 |
| | VoiceCraft_PAB | 6,69 | 7,98 | 10,27 | 9,15 |
| | XTTS-v2_PAB | **6,30** | **7,81** | **9,85** | **8,34** |
| | viXTTS | 7,47 | 8,48 | 10,54 | 8,71 |
| RMSE_F0 ↓ | VALL-E_PAB | 226,55 | 246,88 | 267,80 | **223,56** |
| | VoiceCraft_PAB | **214,66** | 247,54 | **259,46** | 233,68 |
| | XTTS-v2_PAB | 216,44 | **242,51** | 290,77 | 228,81 |
| | viXTTS | 249,54 | 271,70 | 338,59 | 238,05 |
| MOS ↑ | Original | 4,61±0,17 | 4,63±0,16 | 4,41±0,14 | 4,66±0,20 |
| | VALL-E_PAB | 3,96±0,29 | **4,04±0,28** | 3,44±0,21 | 3,75±0,38 |
| | VoiceCraft_PAB | 4,16±0,21 | 3,75±0,29 | **3,85±0,22** | 3,98±0,22 |
| | XTTS-v2_PAB | **4,20±0,20** | 3,89±0,21 | 2,79±0,21 | 3,98±0,29 |
| | viXTTS | 4,05±0,23 | 3,85±0,25 | 2,37±0,24 | 3,48±0,44 |
| SMOS ↑ | Original | 4,23±0,23 | 3,90±0,32 | 3,87±0,24 | 3,34±0,47 |
| | VALL-E_PAB | **3,77±0,24** | 3,46±0,29 | **3,35±0,25** | 3,20±0,38 |
| | VoiceCraft_PAB | 3,64±0,30 | 3,32±0,35 | 3,25±0,25 | **3,41±0,36** |
| | XTTS-v2_PAB | 3,55±0,27 | **3,56±0,29** | 3,03±0,23 | 3,39±0,41 |
| | viXTTS | 2,88±0,28 | 2,63±0,32 | 2,48±0,23 | 3,11±0,43 |

- XTTS-v2_PAB thắng viXTTS trên **mọi metric và test set**; trên viVoice WER 8,32 so với 12,54 dù viXTTS được test trên chính dữ liệu huấn luyện của nó. SMOS cải thiện rõ nhất (PAB-U 3,56 vs 2,63).
- Trên PAB-S, PAB-U, viVoice: VALL-E/VoiceCraft kém XTTS-v2_PAB về WER nhưng tương đương ở MCD, RMSE_F0, MOS, SMOS.
- Trên VIVOS (câu ngắn): hai mô hình XTTS (WER 37,81; MOS 2,79/2,37) kém hẳn VALL-E/VoiceCraft (WER 12,63/13,53). Soát thủ công thấy XTTS-v2 hay **sinh đoạn thừa, lảm nhảm ở cuối** với input ngắn; tác giả quy cho kiến trúc XTTS-v2 chứ không phải dữ liệu, vì cả viVoice lẫn tập augment đều có mẫu ngắn.

## 5. Ưu điểm
- Bộ dữ liệu TTS tiếng Việt lớn, sạch (SI-SNR cao nhất), có speaker ID thật, transcript đã chuẩn hóa, mẫu 10–20 s – đúng miền "đọc sách" với giọng đọc chuyên nghiệp, tốc độ 201 wpm thong thả.
- Pipeline toàn công cụ mở, có kiểm tra chéo hai ASR nên transcript tin cậy; dễ tái dụng.
- Đánh giá toàn diện: 3 mô hình, 4 test set in-/out-of-distribution, 5 metric gồm chấm mù bởi người bản ngữ; tập test soát tay có thể làm benchmark chuẩn.
- Phát hiện thực tế: XTTS-v2 yếu với câu ngắn, các mô hình codec-LM bền hơn về độ dài đầu vào.

## 6. Nhược điểm / hạn chế
Tác giả tự nêu: chưa đánh giá code-switching Việt–Anh.

Nhận xét thêm trong bối cảnh app đọc sách cho người khiếm thị trên di động:
- **Không công bố checkpoint mô hình**, chỉ công bố dataset; muốn có XTTS-v2_PAB phải tự fine-tune trên A100-40GB với 1.494 giờ (VoiceCraft/VALL-E cần 4–8 GPU) – quá sức Colab miễn phí.
- **Giấy phép phi thương mại** cho PhoAudiobook; XTTS-v2 gốc cũng theo giấy phép phi thương mại của Coqui.
- Bài **không báo cáo độ trễ, RTF, kích thước mô hình, bộ nhớ** suy luận; cả ba đều là mô hình autoregressive nặng (VoiceCraft 830M tham số), chạy CPU/điện thoại khó đạt thời gian thực.
- WER còn xa audio gốc (XTTS-v2_PAB 4,16–8,32 vs 0,83–0,88); **XTTS-v2 lỗi nặng với câu ngắn** (WER 37,81) trong khi sách có nhiều tiêu đề chương, câu thoại ngắn.
- Dữ liệu 16 kHz, chỉ miền sách nói, transcript đã chuẩn hóa nên mô hình cần bước chuẩn hóa văn bản trước TTS – mô hình chuẩn hóa đó không được công bố.
- Test set viVoice trùng dữ liệu huấn luyện của viXTTS; bản quyền tác phẩm gốc trên sachnoiviet.net bài không bàn.

## 7. Liên hệ với đề tài
- **Bước TTS**: với máy không GPU, lựa chọn thực tế là **viXTTS** (`capleaf/viXTTS`, checkpoint công khai, chạy CPU được dù chậm) hoặc XTTS-v2 fine-tune nhẹ trên Colab với tập con PhoAudiobook (vài chục giờ). Bài là luận cứ rằng fine-tune trên dữ liệu audiobook cải thiện WER và độ giống giọng so với viVoice.
- **Dữ liệu** `thivux/phoaudiobook`: (a) fine-tune/đánh giá TTS; (b) chọn **giọng tham chiếu** (reference prompt) chất lượng đọc sách cho zero-shot TTS; (c) dùng PAB-S/PAB-U làm benchmark nội bộ.
- **Bước chuẩn hóa văn bản** (sau OCR, trước TTS): bài xác nhận TTS cần số → chữ, dấu câu, lowercase; có thể tái dụng ý tưởng seq2seq với `nguyenvulebinh/spoken_norm_pattern` hoặc rule-based nhẹ trên điện thoại.
- **Đánh giá**: đo WER tự động bằng PhoWhisper-large trên audio tổng hợp; MOS/SMOS thang 1–5 bước 0,5 với người bản ngữ.
- **Thiết kế app**: vì XTTS-v2 sinh đoạn thừa với câu ngắn, nên **gộp câu ngắn thành đoạn 10–20 s** (đúng phân phối huấn luyện) trước khi TTS, và cắt audio thừa cuối bằng VAD.
- **Rủi ro**: độ trễ CPU/di động cao → cần TTS phía server hoặc tiền tổng hợp theo trang; giấy phép phi thương mại; không có checkpoint chính thức; chưa rõ hành vi với tiếng Anh xen kẽ (tên riêng, thuật ngữ).

## 8. Thuật ngữ & số liệu đáng nhớ
- **PhoAudiobook**: 941 giờ, 735 người nói, mẫu 10–20 s (mean 11,66 s), SI-SNR 4,91 dB, 201 wpm, 16 kHz; lọc từ 23K giờ thô, cap 4 giờ/người.
- Train 940 h + 554 h augment ngắn = **1.494 h**; val 0,5 h; test seen 0,8 h/20 người, unseen 0,4 h/20 người.
- **Zero-shot TTS**: tổng hợp giọng chưa thấy từ vài giây audio prompt; VALL-E/VoiceCraft = neural codec language model; XTTS-v2 = kế thừa Tortoise, đa ngôn ngữ, BPE.
- XTTS-v2_PAB vs viXTTS trên viVoice: WER **8,32 vs 12,54**; PAB-U: WER 4,31 vs 5,17, SMOS 3,56 vs 2,63.
- VIVOS (câu ngắn): XTTS WER **37,81** vs VALL-E 12,63, VoiceCraft 13,53; MOS XTTS-v2_PAB 2,79 vs VoiceCraft 3,85.
- Metric: WER (PhoWhisper-large), MCD (pymcd), RMSE_F0 (Amphion), MOS, SMOS (1–5, bước 0,5; 10/20 người chấm).
- Tài nguyên: XTTS-v2 1×A100-40GB/18 epoch; VoiceCraft 4×A100/16 epoch (830M params); VALL-E 8×A100.
- Hạn chế tự nêu: chưa test code-switching. Bài không nêu: độ trễ, RTF, kích thước mô hình, checkpoint phát hành.
