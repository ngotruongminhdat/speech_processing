# MobileSpeech: A Fast and High-Fidelity Framework for Mobile Zero-Shot Text-to-Speech
**Venue:** ACL 2024 (Long Papers, tr. 13588–13600) | **Hạng:** CORE A* | **Năm:** 2024 | **Tác giả/nhóm:** Shengpeng Ji*, Ziyue Jiang*, Hanting Wang, Jialong Zuo, Zhou Zhao — Zhejiang University & Shanghai AI Laboratory | **Link:** https://aclanthology.org/2024.acl-long.733/ (demo: https://mobilespeech.github.io/)
**Tóm tắt 3 câu:** MobileSpeech là hệ TTS zero-shot (nhân bản giọng từ vài giây prompt) đầu tiên nhắm tới triển khai trên di động, xây trên FastSpeech2 + codec rời rạc (Encodec encoder / Vocos decoder), sinh token song song bằng mask thay vì tự hồi quy. Hai đóng góp chính là module SMD (Speech Mask Codec Decoder) khai thác cấu trúc phân cấp của RVQ và module Speaker Prompt trích duration mịn từ prompt speech. Với 207M tham số và 580 giờ LibriTTS, mô hình đạt WER 3.1, SPK 0.688, RTF 0.09 trên A100 (nhanh hơn VALL-E 11 lần); bản tiếng Trung 40.000 giờ vượt MegaTTS2 về CMOS.

## 1. Bài toán & động cơ
Các hệ TTS zero-shot SOTA (VALL-E, NaturalSpeech2, VoiceBox, MegaTTS...) đều chạy trên cloud, bỏ qua tốc độ và kích thước mô hình, trong khi tác giả quan sát RTF trên điện thoại thường gấp 8–10 lần RTF trên A100. Mô hình tự hồi quy (AR) chậm, tốn bộ nhớ, lỗi tích luỹ gây lặp/mất từ; diffusion cần hàng trăm bước; cascade semantic token thêm độ trễ. Bài đặt 5 tiêu chí cho TTS zero-shot di động — **Fast, Lightweight, High similarity & diversity, High quality, Robustness** — và đề xuất MobileSpeech vì không SOTA nào đạt đủ.

## 2. Phương pháp
**Kiến trúc (Hình 1a).** Encoder–Decoder phi tự hồi quy trên nền FastSpeech2: text → phoneme → Text Encoder (FFT blocks); prompt speech → Encodec → ma trận token `C ∈ R^{T×N}` (N = 8 codebook RVQ); **Duration Extractor** trích duration mịn từ token prompt, cùng text đích vào **Duration Predictor** + Length Regulator; **SMD** (ConFormer 16 lớp) sinh token âm học đích; Vocos giải mã ra sóng âm.

**Vì sao nhanh.** (i) Sinh song song kiểu mask-predict (MaskGIT/SoundStorm), không AR, không diffusion. (ii) Chỉ kênh RVQ 1 lặp nhiều vòng (chọn 8); 7 kênh còn lại dự đoán một lượt bằng greedy. (iii) Khi huấn luyện, với xác suất `1−α` (α = 0.6) mask *toàn bộ* kênh 1 để mô hình học sinh thẳng từ text, giúp suy luận cần ít vòng hơn và học từ dễ tới khó. (iv) Mô hình nhỏ 207M.

**Codec & mask (Hình 1b, Phụ lục B).** Vì tầng RVQ càng mịn càng ít ảnh hưởng chất lượng cảm nhận, xác suất đồng thời tách thành kênh 1 (điều kiện trên prompt + text) nhân tích các kênh j = 2..N (điều kiện thêm trên các kênh < j). Mask kênh 1: `M ~ Bernoulli(p)`, `p = cos(u)`, `u ~ U(0, π/2)`. Các kênh còn lại chọn kênh huấn luyện bằng **Prank** (Algorithm 1): lặp kênh `c_i` `w_i` lần với `w_j > w_{j+1}` rồi lấy mẫu, ưu tiên kênh thô. Phụ lục B đối chiếu SpearTTS (trải phẳng, AR), VALL-E (AR kênh 1 + NAR còn lại), UniAudio (attention toàn cục/cục bộ) — đều AR, không hợp di động — với MobileSpeech (mask song song).

**Prompt (Hình 2).** Prompt *text-agnostic*, không cần transcript (khác VALL-E). Khi huấn luyện cắt đoạn đầu dài `k`, `T/3 ≤ k ≤ 2T/3`, làm prompt, phần còn lại là đích; prompt ở Encoder và Decoder là hai đoạn khác nhau. Do bản đầu cho prosody quá đều, nhóm thay prompt thô bằng Duration Extractor dùng Q-K-V attention (text là Query, prompt acoustic/duration là K/V) + Conv1D + residual. Trong SMD, token prompt giữ nguyên không mask, không positional embedding, không qua prompt encoder (theo UniCATS); thêm cross-attention cho text đích hút thông tin từ prompt.

**Huấn luyện/suy luận.** `L = L_smd^1 + L_smd^j + L_promptdur + L_dur` (cross-entropy cho SMD, MSE cho duration trong miền log, nhãn từ MFA). Suy luận: kênh 1 confidence-based sampling theo lịch cosine, kênh còn lại greedy.

## 3. Dữ liệu & thiết lập thí nghiệm
- **Tiếng Anh:** LibriTTS 580 giờ, 2.456 người nói; 12 epoch, 4×A100 40G, batch 3.500 khung codec, AdamW (β1 0.9, β2 0.95), warm-up 5k bước, lr đỉnh 5×10⁻⁴; codec pre-trained. Test: LibriSpeech test-clean, mẫu 4–10 s (2,2 giờ), giao thức VALL-E: 3 giây đầu làm prompt, sinh phần tiếp ("Continue").
- **Tiếng Trung:** tập nội bộ 40.000 giờ, 32×A100 40G; codec huấn luyện end-to-end. Test: 200 bản ghi điện thoại thực 3–10 s, sạch lẫn nhiễu; so với API trả phí MegaTTS2 (11/2023).
- **Baseline:** YourTTS (chính thức, ≈640 giờ), VALL-E (tự tái hiện, 60.000 giờ), NaturalSpeech2 và MegaTTS (bản tái hiện).
- **Metric:** WER (HuBERT-Large CTC, không LM), SPK (WavLM-TDNN), RTF = thời gian sinh đặc trưng / độ dài audio, **không tính vocoder, đo trên A100 trống**; MOS-Q/P/S và CMOS, 50 mẫu, ≥20 người nghe mỗi audio.

## 4. Kết quả chính
**Bảng 1 – LibriSpeech test-clean (RTF trên A100, không tính vocoder):**

| Mô hình | Giờ dữ liệu | WER ↓ | SPK ↑ | RTF ↓ | MOS-Q ↑ | MOS-P ↑ | MOS-S ↑ |
|---|---|---|---|---|---|---|---|
| GT Codec | – | 2.4 | 0.871 | – | 4.41 | 4.28 | 4.45 |
| YourTTS | 640 | 7.7 | 0.504 | 0.22 | 3.71 | 3.59 | 3.68 |
| VALL-E | 60000 | 5.9 | 0.751 | 0.94 | 4.22 | 4.09 | 4.16 |
| VALL-E-Continue | 60000 | 3.8 | 0.734 | 0.94 | 4.12 | 4.13 | 4.11 |
| NaturalSpeech2-Continue | 580 | 4.6 | 0.581 | 0.35 | 3.85 | 3.69 | 3.76 |
| MegaTTS-Continue | 580 | 5.8 | 0.615 | 0.39 | 3.93 | 3.85 | 3.89 |
| **MobileSpeech-Continue** | 580 | **3.1** | 0.688 | **0.09** | 4.06 | 4.02 | 4.05 |

**Số tham số:** VALL-E 465M (AR 229M + NAR 235M); NaturalSpeech2 435M; MegaTTS 473M; **MobileSpeech 207M** (Bảng 6: Conformer 67.2M, Text Encoder 42.0M, Prompt Text Encoder 21.0M, Prompt Duration Encoder 21.0M, Duration Extractor 19.2M, Duration Predictor 19.2M, Prompt Encoder 16.2M).

**Bảng 2 – CMOS tiếng Trung** (MobileSpeech = 0.00): GT codec +0.07 / +0.15 / +0.03 (Q/P/S); MegaTTS2 −0.16 / −0.05 / −0.24. Vượt MegaTTS2 cả ba, nhất là tương đồng giọng (+0.24); so với GT codec tốt hơn về SPK, kém về prosody.

**Bảng 3–4 – Ablation:** w/o durprompt: WER 3.6, SPK 0.638, MOS 4.03/3.90/3.97; w/o onechannel (thay SMD bằng chọn ngẫu nhiên một tầng): WER 4.2, SPK 0.614, MOS 3.98/3.95/3.92; đầy đủ: 3.1 / 0.688 / 4.06/4.02/4.05.

**Bảng 5 – số vòng lặp kênh 1 (vòng: RTF / WER / SPK):** 24: 0.20/3.1/0.698; 16: 0.15/3.0/0.696; **8: 0.09/3.1/0.688 (chọn)**; 4: 0.07/4.2/0.615; 1: 0.05/5.7/0.483.

Tác giả kết luận: nhanh hơn VALL-E 11×, nhanh hơn MegaTTS/NaturalSpeech2 ≈4×, sinh 10 s audio trong ~1 s; WER tốt nhất (hơn VALL-E 0.7); SPK kém VALL-E 0.046 do chênh lệch dữ liệu.

## 5. Ưu điểm
- NAR + mask song song: RTF thấp, không lỗi tích luỹ → WER thấp nhất bảng.
- Khai thác phân cấp RVQ (chỉ kênh 1 lặp; Prank ưu tiên kênh thô) — đơn giản, có ablation.
- Prompt không cần transcript; duration mịn từ prompt giảm nói lắp.
- Nhỏ nhất nhóm so sánh (207M), chỉ 580 giờ dữ liệu công khai mà MOS tiệm cận VALL-E 60k giờ.
- Đã triển khai trên điện thoại thực (dự kiến vài trăm nghìn người dùng), test trên bản ghi điện thoại có nhiễu.

## 6. Nhược điểm / hạn chế
*Tác giả nêu (mục 7):* đôi lúc nói lắp, cao độ bất ổn trong kịch bản thực, nghi do prompt nhiễu hoặc mask quá cục bộ; rủi ro lạm dụng giả giọng.

*Tự nhận ra:*
- **Không mã nguồn, không checkpoint**; chỉnh sửa codec và tập 40k giờ là nội bộ → không tái hiện được.
- Dù tên là "Mobile", **mọi RTF đo trên A100 và bỏ qua vocoder**; bài không nêu RTF/độ trễ/bộ nhớ trên điện thoại cụ thể, không nêu runtime hay lượng tử hoá. 207M tham số (~800 MB fp32) vẫn lớn với app di động.
- Chỉ tiếng Anh và Quan Thoại; cần MFA + phoneme set cho ngôn ngữ đích; bài không nêu giá trị trọng số `w_i` của Prank.
- VALL-E/NaturalSpeech2 là bản tái hiện; thiếu baseline NAR nhỏ (VITS/FastSpeech2 đa giọng); CMOS tiếng Trung chỉ 200 mẫu, so với API thương mại đóng.

## 7. Liên hệ với đề tài
- **Tái sử dụng trực tiếp: không.** Không có mã/checkpoint, không hỗ trợ tiếng Việt, huấn luyện cần nhiều A100. App đọc sách cho người khiếm thị cũng không cần nhân bản giọng; một giọng cố định, rõ, ổn định quan trọng hơn.
- **Ý tưởng áp dụng được cho on-device:** (1) ưu tiên kiến trúc NAR (FastSpeech2/VITS/Piper-style) thay vì AR/LLM-TTS để tránh lặp/mất từ khi đọc văn bản dài từ OCR; (2) dùng bộ metric RTF, số tham số, WER qua ASR (Whisper/wav2vec2 tiếng Việt) để đánh giá TTS; (3) nếu dùng codec-TTS, chọn số vòng lặp theo trade-off như Bảng 5; (4) tách duration/prosody để điều chỉnh tốc độ đọc — tính năng trợ năng quan trọng; (5) nhớ hệ số 8–10× giữa điện thoại và A100 khi chọn mô hình CPU.
- **So với gọi API server:** bài cho thấy TTS on-device chất lượng cao là khả thi nhưng cần mô hình riêng và tối ưu không được công bố. Hướng thực tế cho đồ án là lai: TTS tiếng Việt nhẹ chạy CPU/on-device làm chế độ offline, API cloud làm chế độ online; và phải đo RTF/độ trễ trên chính điện thoại thử nghiệm — điều bài này còn thiếu.

## 8. Thuật ngữ & số liệu đáng nhớ
- **SMD:** decoder ConFormer sinh token codec bằng mask song song; kênh RVQ 1 lặp 8 vòng, 7 kênh còn lại greedy.
- **Prank:** lấy mẫu kênh huấn luyện với trọng số giảm dần theo độ sâu RVQ (Algorithm 1).
- **α = 0.6**; lịch mask cosine `p = cos(u), u ~ U(0, π/2)`; prompt dài `T/3 ≤ k ≤ 2T/3`.
- **RTF 0.09** trên A100 (không tính vocoder): nhanh hơn VALL-E (0.94) 11×, NaturalSpeech2 (0.35)/MegaTTS (0.39) ≈4×.
- **WER 3.1 / SPK 0.688 / MOS-Q 4.06** với 580 giờ; VALL-E-Continue 60k giờ: WER 3.8, SPK 0.734.
- **207M tham số** so với VALL-E 465M, NaturalSpeech2 435M, MegaTTS 473M.
- **Codec:** Encodec encoder + Vocos decoder, 8 codebook; duration từ MFA, miền log.
- Tiếng Trung: 40.000 giờ, 32×A100; CMOS-S hơn MegaTTS2 +0.24.
- RTF điện thoại ≈ **8–10×** RTF A100 (quan sát của tác giả, không có số đo cụ thể).
