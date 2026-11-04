# F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching

**Venue:** ACL 2025 (Volume 1: Long Papers, tr. 6255–6271) | **Hạng:** CORE A* | **Năm:** 2025 | **Tác giả/nhóm:** Yushen Chen, Zhikang Niu, Ziyang Ma, Keqi Deng, Chunhui Wang, Jian Zhao, Kai Yu, Xie Chen* — X-LANCE Lab, Shanghai Jiao Tong University; Shanghai Innovation Institute; University of Cambridge; Geely Automobile Research Institute | **Link:** https://SWivid.github.io/F5-TTS/ (trang dự án; mã nguồn và checkpoint được công bố)

**Tóm tắt 3 câu:** F5-TTS là hệ TTS zero-shot hoàn toàn không tự hồi quy (fully non-autoregressive) dựa trên flow matching với backbone Diffusion Transformer (DiT), bỏ hẳn duration model, phoneme alignment và text encoder riêng: văn bản chỉ được tách thành ký tự, đệm filler token cho bằng độ dài mel rồi khử nhiễu. So với E2 TTS (cùng ý tưởng nhưng hội tụ chậm, kém bền), F5-TTS thêm khối ConvNeXt V2 để tinh chỉnh biểu diễn văn bản trước khi ghép với tiếng nói, và đề xuất Sway Sampling — chiến lược lấy mẫu bước flow lúc suy luận, không cần huấn luyện lại. Huấn luyện trên ~100K giờ Emilia (Anh + Trung), mô hình 336M đạt WER 2.42 trên LibriSpeech-PC test-clean (32 NFE) và RTF 0.15 (16 NFE) trên RTX 3090.

## 1. Bài toán & động cơ

Bài toán là zero-shot TTS: cho vài giây audio prompt và transcript của nó, sinh tiếng nói cho văn bản mới với giọng người nói đó. Mô hình tự hồi quy (AR: VALL-E 2, CosyVoice...) có độ trễ cao, exposure bias và phụ thuộc chất lượng speech tokenizer. Mô hình không tự hồi quy (NAR) suy luận song song nên nhanh, nhưng phải giải bài toán căn chỉnh (alignment) văn bản–tiếng nói: Voicebox/NaturalSpeech 3 dùng frame-wise phoneme alignment, Matcha-TTS dùng monotonic alignment search và duration model; các ràng buộc cứng này bị cho là làm giảm độ tự nhiên.

E2 TTS đơn giản hóa triệt để: bỏ phoneme và duration predictor, đưa thẳng chuỗi ký tự đệm filler token vào cùng mel. Tuy nhiên tác giả phát hiện E2 TTS hội tụ chậm và kém bền: trên tiếng Trung nó thất bại cố định ở 7% mẫu test (WER>50%) suốt quá trình huấn luyện, không cứu được bằng re-ranking. Nguyên nhân: ghép trực tiếp chuỗi ký tự (thông tin hữu ích rất ngắn) với chuỗi mel (rất dài) làm đặc trưng ngữ nghĩa và âm học rối sâu vào nhau. F5-TTS muốn giữ pipeline "text in, speech out" nhưng hội tụ nhanh hơn, bền hơn, suy luận nhanh hơn.

## 2. Phương pháp

**Flow matching (FM) và CFM.** FM học một trường vận tốc v_t(x) đưa phân phối đơn giản p_0 (Gaussian) tới phân phối dữ liệu p_1. Vì không biết p_t thật, ta dùng đường xác suất có điều kiện theo từng mẫu x_1 (Conditional Flow Matching), được chứng minh có cùng gradient. Với dạng Optimal Transport, quỹ đạo là đường thẳng ψ_t(x_0) = (1−t)x_0 + t·x_1 và loss là hồi quy: ‖v_t((1−t)x_0 + t·x_1) − (x_1 − x_0)‖². Lúc suy luận, lấy nhiễu x_0 rồi dùng ODE solver (Euler, midpoint, Heun) tích phân từ t=0 đến t=1; số lần chạy mạng là NFE (number of function evaluations): NFE lớn thì chính xác nhưng chậm. Classifier-Free Guidance (CFG) với cường độ α=2 được dùng để tăng độ trung thực; lưu ý CFG làm thời gian suy luận gấp đôi (forward có và không có điều kiện).

**Nhiệm vụ huấn luyện: text-guided speech infilling.** Đầu vào là mel 100 chiều (24 kHz, hop 256), chuỗi ký tự z đã đệm filler ⟨F⟩ cho bằng số khung mel (công thức 5), nhiễu (1−t)x_0 + t·x_1 và tiếng nói bị che (1−m)⊙x_1 với mặt nạ che ngẫu nhiên 70–100% khung. Mô hình học P(m⊙x_1 | (1−m)⊙x_1, z). Tiếng Anh dùng thẳng chữ cái/ký hiệu; tiếng Trung dùng full pinyin (jieba + pypinyin). Từ vựng 2546 ký tự.

**Bỏ duration model / phoneme alignment.** Lúc suy luận, tổng độ dài mel cần sinh được ước lượng thuần theo tỉ lệ số ký tự giữa văn bản cần sinh và transcript của prompt — không có duration predictor. Mô hình tự phân bổ thời lượng cho từng từ trong tổng độ dài đó, không có ranh giới cứng nên prosody tự nhiên hơn. Sau khi sinh, phần mel của prompt bị bỏ, phần còn lại qua vocoder Vocos (hoặc BigVGAN) ra sóng âm.

**Backbone DiT.** Latent Diffusion Transformer với adaLN-zero; bước flow t đi vào qua adaLN thay vì nối vào chuỗi như Voicebox. Bỏ skip connection kiểu U-Net của Voicebox/E2 TTS. Dùng RoPE cho self-attention, positional embedding tích chập cho chuỗi ghép, sinusoidal cho bước flow và chuỗi ký tự. Base: DiT 22 lớp, 16 head, 1024/2048 chiều; ConvNeXt V2 4 lớp, 512/1024; tổng 335.8M tham số.

**ConvNeXt V2 cho văn bản.** Điểm khác cốt lõi với E2 TTS: trước khi nối theo chiều đặc trưng với mel, chuỗi ký tự đã đệm đi qua 4 khối ConvNeXt V2, tạo "không gian mô hình hóa riêng" để văn bản tự chuẩn bị trước khi in-context learning với tiếng nói. Ablation (mô hình ~155M, tiếng Trung): DiT thuần không ConvNeXt (−Conv2Text) hoàn toàn không học được alignment; thêm ConvNeXt cho cả nhánh audio (+Conv2Audio) làm WER tệ đi +1.61 chỉ đổi lấy +0.01 SIM; thêm long-skip vào DiT hoặc thêm ConvNeXt vào E2 TTS đều làm kết quả tệ đi (E2 TTS+Conv2Text WER 18.10); MMDiT học nhanh nhưng sụp đổ (lặp từ, biến dạng giọng).

**Sway Sampling.** Huấn luyện vẫn lấy t ~ U[0,1], nhưng lúc suy luận lấy u ~ U[0,1] rồi biến đổi t = f_sway(u; s) = u + s·(cos(πu/2) − 1 + u), s ∈ [−1, 2/(π−2)]. s<0 dồn các bước về phía t nhỏ (gần nhiễu), s=0 là đều. Trực giác: giai đoạn đầu (t→0) mô hình phác thảo đường nét và quyết định alignment văn bản–tiếng nói, giai đoạn sau chỉ tô chi tiết; cho ODE solver nhiều bước ở đầu giúp tích phân chính xác hơn. Mặc định s=−1. Thí nghiệm "leak and override" (thay x_0 bằng nhiễu trộn 10% mel của prompt, t'=0.1) cho thấy chỉ khi có Sway Sampling mô hình mới ghi đè được nội dung rò rỉ và đọc đúng văn bản mới. Kỹ thuật này áp dụng được cho mọi mô hình CFM có sẵn mà không cần huấn luyện lại (đã kiểm chứng trên E2 TTS).

## 3. Dữ liệu & thiết lập thí nghiệm

- **Huấn luyện base:** Emilia (in-the-wild, đa ngữ) sau lọc còn ~95K giờ tiếng Anh + Trung; 1.2M bước, batch 307,200 khung audio (0.91 giờ), hơn một tuần trên 8× NVIDIA A100 80G; AdamW, LR đỉnh 7.5e-5, warm-up 20K bước, grad-clip 1; dropout 0.1; CFG drop rate 0.3 (masked speech) rồi 0.2 (masked speech + text); suy luận bằng trọng số EMA.
- **Ablation:** mô hình nhỏ ~155M, 800K bước, WenetSpeech4TTS Premium (945 giờ tiếng Quan Thoại), batch bằng nửa base.
- **Test set:** LibriSpeech-PC test-clean (tác giả xây và công bố tập con 1127 mẫu, 4–10 giây, ~2 giờ), Seed-TTS test-en (1088 mẫu Common Voice), Seed-TTS test-zh (2020 mẫu DiDiSpeech), ELLA-V hard sentences (100 mẫu).
- **Metric:** WER (Whisper-large-v3 cho Anh, Paraformer-zh cho Trung), SIM-o (cosine embedding WavLM-large giữa audio sinh và audio gốc), RTF (thời gian suy luận cho 10 giây tiếng nói trên RTX 3090), UTMOS (độ tự nhiên khách quan), CMOS/SMOS chủ quan (20 người bản ngữ mỗi ngôn ngữ, 30 vòng). Mọi số là trung bình 3 seed.
- **Baseline:** AR: VALL-E 2, MELLE, FireRedTTS, CosyVoice; NAR: Voicebox, NaturalSpeech 3, DiTTo-TTS, MaskGCT, Seed-TTS_DiT, và E2 TTS do tác giả tái tạo (333.2M, cùng dữ liệu Emilia).

## 4. Kết quả chính

**Bảng 1 – LibriSpeech(-PC) test-clean** (RTF cho 10 s tiếng nói trên RTX 3090; Vocos; CFG=2; s=−1):

| Mô hình | #Param | #Data | WER(%)↓ | SIM-o↑ | RTF↓ |
|---|---|---|---|---|---|
| *LibriSpeech test-clean (các tập con khác nhau)* | | | | | |
| Ground Truth (2.2 h subset) | – | – | 2.2 | 0.754 | – |
| VALL-E 2 | – | 50K EN | 2.44 | 0.643 | 0.732 |
| MELLE | – | 50K EN | 2.10 | 0.625 | 0.549 |
| MELLE-R2 | – | 50K EN | 2.14 | 0.608 | 0.276 |
| Voicebox | 330M | 60K EN | 1.9 | 0.662 | 0.64 |
| DiTTo-TTS | 740M | 55K EN | 2.56 | 0.627 | 0.162 |
| NaturalSpeech 3 (40 samples) | 500M | 60K EN | 1.94 | 0.67 | 0.296 |
| MaskGCT | 1048M | 100K Multi. | 2.634 | 0.687 | – |
| *LibriSpeech-PC test-clean (1127 mẫu, 2 h)* | | | | | |
| Ground Truth | – | – | 2.23 | 0.69 | – |
| Vocoder Resynthesized | – | – | 2.32 | 0.66 | – |
| CosyVoice | ~300M | 170K Multi. | 3.59 | 0.66 | 0.92 |
| FireRedTTS | ~580M | 248K Multi. | 2.69 | 0.47 | 0.84 |
| E2 TTS (32 NFE) | 333M | 100K Multi. | 2.95 | 0.69 | 0.68 |
| **F5-TTS (16 NFE)** | 336M | 100K Multi. | 2.53 | 0.66 | **0.15** |
| **F5-TTS (32 NFE)** | 336M | 100K Multi. | **2.42** | 0.66 | 0.31 |

**Bảng 2 – Seed-TTS test-en / test-zh** (* = số báo cáo trong bài gốc của baseline):

| Mô hình | en WER↓ | en SIM-o↑ | en CMOS↑ | en SMOS↑ | zh WER↓ | zh SIM-o↑ | zh CMOS↑ | zh SMOS↑ |
|---|---|---|---|---|---|---|---|---|
| Ground Truth | 2.06 | 0.73 | 0.00 | 3.91 | 1.26 | 0.76 | 0.00 | 3.72 |
| CosyVoice | 3.39 | 0.64 | 0.02 | 3.64 | 3.10 | 0.75 | −0.06 | 3.54 |
| FireRedTTS | 3.82 | 0.46 | −1.46 | 2.94 | 1.51 | 0.63 | −0.49 | 3.28 |
| MaskGCT | 2.623* | 0.717* | – | – | 2.273* | 0.774* | – | – |
| Seed-TTS_DiT | 1.733* | 0.790* | – | – | 1.178* | 0.809* | – | – |
| E2 TTS (32 NFE) | 2.19 | 0.71 | 0.06 | 3.81 | 1.97 | 0.73 | −0.04 | 3.44 |
| F5-TTS (16 NFE) | 1.89 | 0.67 | 0.16 | 3.79 | 1.74 | 0.75 | 0.02 | 3.72 |
| F5-TTS (32 NFE) | 1.83 | 0.67 | 0.31 | 3.89 | 1.56 | 0.76 | 0.21 | 3.83 |

**Ablation Sway Sampling (Bảng 5, base, midpoint solver):** trên LibriSpeech-PC, F5-TTS 32 NFE WER 2.84 → 2.41, SIM 0.62 → 0.66, UTMOS 3.70 → 3.89 khi bật SS; E2 TTS 32 NFE WER 2.95 → 2.84, SIM 0.69 → 0.72. Với SS, 16 NFE (2.43) gần bằng 32 NFE (2.41) nhưng RTF giảm nửa (0.26 so với 0.53).

**ODE solver (Bảng 6):** Euler 16 NFE, s=−1 cho RTF 0.15 (WER 2.53); midpoint 16 NFE RTF 0.26; Euler 32 NFE RTF 0.31. s=−0.8 kém hơn s=−1.

**Mô hình nhỏ (Hình 2, Bảng 4):** trên Seed-TTS test-zh, F5-TTS 155M đạt WER 4.17 / SIM 0.54 sau 800K bước; E2 TTS cùng cỡ 9.63 / 0.53.

**Câu khó ELLA-V (Bảng 7):** F5-TTS WER 4.40 (Sub 1.81, Del 2.40, Ins 0.18) so với E2 TTS 8.58, CosyVoice 8.30*, StyleTTS 2 4.83*, E1 TTS_DMD 4.29*. Insertion thấp → không lặp vô tận; Deletion cao → bỏ từ khi gặp chuỗi từ lặp.

**Vocoder (Bảng 8):** BigVGAN tốt hơn Vocos: 32 NFE WER 2.11 so với 2.42 (LibriSpeech-PC).

**Quy mô dữ liệu nhỏ (Bảng 9):** mô hình 158M huấn luyện trên LibriTTS 585 giờ đạt WER 2.20 / SIM 0.60 ở 500K bước (ground truth 2.23 / 0.69); trên LJSpeech 24 giờ đơn giọng, WER tốt nhất 2.93 ở 200K bước rồi tăng dần (5.25 ở 600K) — dấu hiệu overfit. Mỗi 100K bước ≈ 8 giờ trên 8× H100.

## 5. Ưu điểm

- Pipeline cực đơn giản: không G2P, không duration predictor, không text encoder riêng, không codec ngữ nghĩa; đầu vào ký tự thô → dễ mở rộng sang ngôn ngữ mới.
- Nhanh: RTF 0.15 (16 NFE, Euler, RTX 3090), nhanh hơn 4–6 lần các baseline AR (CosyVoice 0.92, FireRedTTS 0.84, VALL-E 2 0.732) và E2 TTS (0.68).
- Bền hơn E2 TTS rõ rệt (WER 2.42 so với 2.95; mô hình nhỏ 4.17 so với 9.63), không có kiểu thất bại hệ thống không cứu được bằng re-ranking.
- Sway Sampling là cải tiến "miễn phí" lúc suy luận: tăng đồng thời WER, SIM, UTMOS và cho phép giảm NFE còn một nửa; dùng được cho mọi mô hình CFM.
- Hội tụ ổn định với dữ liệu nhỏ (585 giờ, thậm chí 24 giờ) — quan trọng cho ngôn ngữ ít tài nguyên.
- Mã nguồn, checkpoint, tập test 1127 mẫu được công bố; đánh giá chủ quan minh bạch (20 người/ngôn ngữ); CMOS vượt ground truth (+0.31 en, +0.21 zh).

## 6. Nhược điểm / hạn chế

**Tác giả tự nêu:** (1) chuỗi mel vẫn dài hơn nhiều so với văn bản → tốn tính toán; (2) thiếu điều khiển chi tiết cận ngôn ngữ (cảm xúc). Ngoài ra từ kết quả: ước lượng độ dài theo tỉ lệ ký tự khá thô; bỏ từ khi gặp cụm lặp (Del 2.40% trên ELLA-V); phát âm sai từ hiếm (yogis→yojus); SIM-o thấp hơn E2 TTS (0.66 so với 0.69–0.71).

**Khi đặt vào app đọc sách cho người khiếm thị trên di động:**
- *Độ trễ/tài nguyên:* RTF 0.15 đo trên RTX 3090, với CFG (2 forward mỗi bước) và 16 bước; bài không nêu số đo nào trên CPU hay thiết bị di động. Mô hình 336M + vocoder, 16–32 lần forward DiT 22 lớp trên toàn chuỗi mel → trên CPU laptop/điện thoại gần như chắc chắn RTF > 1; thực tế cần server GPU/API hoặc sinh trước theo lô rồi phát.
- *Không streaming:* NAR sinh cả câu một lần; sách dài phải chia câu/đoạn, cần buffer.
- *Yêu cầu prompt:* cần audio prompt + transcript đúng của prompt; app phải đóng gói sẵn giọng mẫu.
- *Tiếng Việt:* bài hoàn toàn không đề cập tiếng Việt; từ vựng 2546 ký tự xây từ Emilia (Anh/Trung), chữ cái có dấu thanh tiếng Việt chưa chắc có → phải mở rộng từ vựng và fine-tune. Bài không nêu kết quả cross-lingual sang ngôn ngữ chưa thấy.
- *Chuẩn hóa văn bản:* mô hình nhận ký tự thô, không đọc số/ngày/viết tắt → bước text normalization của ta là bắt buộc.
- *Chi phí huấn luyện:* base cần 8× A100 hơn một tuần; mô hình nhỏ 100K bước ≈ 8 giờ trên 8× H100 — vượt xa Colab; chỉ khả thi fine-tune nhẹ từ checkpoint.
- *Giấy phép:* bài không nêu giấy phép mã nguồn/checkpoint.
- *Đánh giá:* không có số liệu trên văn bản dài kiểu trang sách hay độ ổn định giọng giữa nhiều câu liên tiếp.

## 7. Liên hệ với đề tài

- **Vị trí trong pipeline:** khối TTS (bước 4), sau OCR và chuẩn hóa văn bản. F5-TTS là ứng viên backbone TTS chất lượng cao chạy phía server/API; không phải ứng viên chạy trực tiếp trên điện thoại (đối chiếu bài MobileSpeech).
- **Mô hình/checkpoint:** bài công bố mã và checkpoint F5-TTS Base (336M, Emilia ~100K giờ EN+ZH) và E2 TTS tái tạo tại https://SWivid.github.io/F5-TTS/; vocoder Vocos hoặc BigVGAN pretrained. Link GitHub/HuggingFace cụ thể: bài không nêu ngoài trang dự án (theo hiểu biết ngoài bài, repo là github.com/SWivid/F5-TTS và checkpoint HuggingFace SWivid/F5-TTS — cần tự xác minh cùng giấy phép).
- **Khả năng fine-tune tiếng Việt:** thiết kế ký tự thô + không G2P là lợi thế lớn: chỉ cần (a) mở rộng từ vựng với chữ cái có dấu tiếng Việt, (b) fine-tune từ checkpoint Base trên dữ liệu tiếng Việt có transcript (ví dụ PhoAudiobook từ bài 01). Bằng chứng gián tiếp: mô hình nhỏ học alignment ổn định với 585 giờ (WER 2.20) và chạy được với 24 giờ (WER 2.93 ở 200K bước) — nhưng phải canh overfit (LJSpeech tăng WER sau 200K bước). Chi phí trong bài là train-from-scratch nhiều GPU; fine-tune trên Colab T4/A100 đơn với batch nhỏ là kịch bản bài chưa kiểm chứng.
- **Ý tưởng áp dụng:** (1) cấu hình mặc định Sway Sampling s=−1 + Euler + 16 NFE để giảm độ trễ nửa mà gần như không mất chất lượng; (2) chỉnh tỉ lệ ước lượng độ dài để làm speed control cho người dùng (bài nêu khả năng này); (3) đóng gói một audio prompt chuẩn 3–5 giây kèm transcript để cố định giọng đọc; (4) chia văn bản OCR thành câu 4–10 giây tương tự điều kiện test; (5) thử BigVGAN thay Vocos nếu chấp nhận thêm chi phí.
- **Rủi ro:** độ trễ CPU không có số liệu; bỏ từ khi gặp cụm lặp và phát âm sai từ hiếm là nguy hiểm với sách (người khiếm thị không đối chiếu được bằng mắt); phụ thuộc chất lượng chuẩn hóa văn bản; giấy phép chưa rõ; đánh giá tiếng Việt phải tự xây (WER bằng ASR tiếng Việt, SIM bằng WavLM) vì bài không có.

## 8. Thuật ngữ & số liệu đáng nhớ

- **CFM / OT-CFM:** hồi quy trường vận tốc trên đường thẳng (1−t)x_0 + t·x_1; suy luận bằng ODE solver, chi phí tính theo NFE; CFG strength 2 (gấp đôi thời gian).
- **Sway Sampling:** t = u + s·(cos(πu/2) − 1 + u), s ∈ [−1, 2/(π−2)], mặc định s=−1 (dồn bước về gần nhiễu); không cần huấn luyện lại; áp dụng cho mọi mô hình CFM.
- **Filler token ⟨F⟩:** đệm chuỗi ký tự cho bằng số khung mel → không cần duration model/phoneme alignment; độ dài suy luận ước lượng theo tỉ lệ ký tự.
- **ConvNeXt V2 text refinement:** 4 lớp, 512/1024; bỏ đi thì DiT không học được alignment.
- **Kiến trúc Base:** DiT 22 lớp, 16 head, 1024/2048; adaLN-zero; RoPE; 335.8M tham số; mel 100 chiều, 24 kHz, hop 256; từ vựng 2546 ký tự.
- **Huấn luyện:** Emilia ~95K giờ EN+ZH, 1.2M bước, batch 0.91 giờ audio, >1 tuần trên 8× A100 80G.
- **Kết quả then chốt:** WER 2.42 / SIM-o 0.66 (LibriSpeech-PC, 32 NFE); RTF 0.15 (16 NFE, Euler, RTX 3090); Seed-TTS test-en WER 1.83, test-zh 1.56; CMOS +0.31/+0.21 so với ground truth.
- **So với E2 TTS:** WER 2.95 → 2.42, RTF 0.68 → 0.15–0.31; mô hình nhỏ tiếng Trung WER 9.63 → 4.17; E2 TTS thất bại cố định 7% mẫu.
- **Hiệu quả SS trên base:** WER 2.84 → 2.41, SIM 0.62 → 0.66, UTMOS 3.70 → 3.89 (32 NFE, midpoint).
- **Hạn chế tự nêu:** mel vẫn quá dài so với text; không điều khiển được cảm xúc/paralinguistic.
