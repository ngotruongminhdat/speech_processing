# So sánh engine TTS tiếng Việt cho việc tạo sách nói

Đo ngày 05/11/2026 trên máy dev: AMD Ryzen 7 5700G (16 luồng), 62 GB RAM, **không có GPU CUDA**.
Văn bản thử: 20 đoạn đầu của truyện "Lão Hạc" (Nam Cao), 1.333 âm tiết, từ câu thoại 7 ký tự đến đoạn 1.309 ký tự.
Số liệu gốc: `report/tables/tts_piper_speed.csv`, `report/tables/tts_intelligibility.csv`. Mã đo: `demo/tts_bench_piper.py`, `demo/tts_intelligibility.py`.

## 1. Kết quả

| Engine | Chạy ở đâu | Tốc độ tạo | WER ↓ | CER ↓ | Dùng được |
|---|---|---|---|---|---|
| edge-tts, giọng Hoài My | Dịch vụ ngoài của Microsoft | Không ổn định, xem mục 3 | 5,25% | 2,21% | Có, nhưng không tin cậy được |
| Piper `vi_VN-vais1000-medium` | CPU máy dev | **Nhanh gấp 27–40 lần thời gian thực** | 9,98% | 5,00% | Có, giữ làm giọng dự phòng |
| Piper `vi_VN-25hours_single-low` | CPU máy dev | Nhanh gấp khoảng 9 lần khi đo cùng lúc | 38,11% | 21,75% | Không |
| VieNeu-TTS v3 Turbo, giọng Ngọc Linh (nữ) | CPU máy dev | Nhanh gấp 1,1–1,6 lần thời gian thực | 5,10% | 2,19% | **Có, được chọn làm giọng nữ** |
| VieNeu-TTS v3 Turbo, giọng Thiện Minh (nam) | CPU máy dev | Nhanh gấp 1,3–1,6 lần | 5,40% | 2,97% | **Có, được chọn làm giọng nam** |
| VieNeu-TTS v3 Turbo, giọng Quỳnh Anh (nữ) | CPU máy dev | Nhanh gấp 1,2 lần | **4,20%** | **1,79%** | Có |
| VieNeu-TTS v3 Turbo, giọng Ngọc Huyền (nữ) | CPU máy dev | Nhanh gấp 1,2 lần | 4,43% | 2,43% | Có |

**Cách đo độ rõ.** Cho mô hình nhận dạng tiếng nói `faster-whisper large-v3-turbo` nghe lại audio, so văn bản nhận được với văn bản gốc sau khi viết thường và bỏ dấu câu. Sai số của bản thân ASR là như nhau cho mọi engine, nên các con số dùng để **so sánh giữa các engine**, không phải độ rõ tuyệt đối. Đây là cách bài PhoAudiobook (ACL 2025) đánh giá TTS tiếng Việt.

**Cách đo tốc độ.** RTF = thời gian tạo chia cho thời lượng audio. Khi dựng sách thật, không có tiến trình khác tranh CPU, Piper đạt RTF 0,025–0,037. Ví dụ 9 chương đầu của "Tắt đèn": 57,7 phút audio tạo trong 93 giây. VieNeu-TTS đạt RTF 0,80–0,89 khi đọc cả đoạn một lần và 0,62 khi đọc từng câu trong lúc dựng sách thật: 9,1 phút audio của "Gió lạnh đầu mùa" tạo trong 340 giây.

### 1.1. Vì sao chuyển sang VieNeu-TTS (bổ sung 05/11/2026)

Sau khi thư viện được dựng bằng Piper, người nghe thử nhận xét **ngữ điệu không hay bằng giọng Hoài My của bản giữa kỳ**. Phép đo WER ở trên không bắt được điều này vì nó chỉ đo từng từ có nghe ra hay không. Hai phép đo bổ sung trên cùng 20 đoạn:

| Giọng | Tổng thời lượng | Tốc độ đọc (âm tiết/phút) | Tốc độ lúc đang phát âm | Phần thời gian là khoảng lặng |
|---|---|---|---|---|
| Hoài My (edge-tts) | 429,9 s | 186 | 286 | 34,8% |
| Piper vais1000 | 290,9 s | 275 | 295 | 6,7% |
| VieNeu Ngọc Linh | 331,4 s | 241 | 284 | 15,1% |
| VieNeu Quỳnh Anh | 353,9 s | 226 | 270 | 16,3% |
| VieNeu Ngọc Huyền | 326,5 s | 245 | 309 | 20,7% |
| VieNeu Thiện Minh | 314,5 s | 254 | 321 | 20,7% |

Khoảng lặng được tính bằng ngưỡng năng lượng đơn giản (khung 20 ms có RMS dưới 1% mức đỉnh), nên chỉ dùng để so tương đối. File của edge-tts có thêm khoảng lặng đệm ở hai đầu mỗi đoạn.

Nhận xét: lúc đang phát âm, mọi giọng nói nhanh gần như nhau. Khác biệt lớn nhất của Piper là **gần như không ngắt nghỉ**: mô hình VITS nhỏ, huấn luyện trên khoảng một nghìn câu đọc rời, không học được chỗ nghỉ ở dấu phẩy và giữa các ý. VieNeu-TTS là mô hình tự hồi quy huấn luyện trên hơn 10.000 giờ, tự ngắt nghỉ trong câu và đạt độ rõ ngang Hoài My.

Trang nghe thử dùng để chọn giọng: `demo/make_listen_page.py`, bản đã deploy ở `/nghe-thu/`. Người nghe chọn Ngọc Linh và Thiện Minh, và yêu cầu ứng dụng cho chọn giữa giọng nữ và giọng nam.

### 1.2. Cái giá của VieNeu-TTS

- **Chậm hơn Piper khoảng 20–40 lần.** Dựng hai giọng cho cả thư viện (khoảng 3,6 giờ audio mỗi giọng) mất nhiều giờ thay vì vài phút. Vì thế việc dựng được xếp hàng theo từng cuốn và deploy dần (`pipeline/scripts/build_voices.py`).
- **Không tăng tốc được bằng cách chạy song song trên máy này.** Một tiến trình: RTF 0,74. Hai tiến trình cùng lúc, mỗi tiến trình 4 luồng: RTF 1,74 mỗi tiến trình, tức tổng thông lượng còn kém hơn chạy một. Ghim một tiến trình vào 4 nhân: RTF 2,04. Mô hình cần trọn 8 nhân.
- **Sinh mẫu ngẫu nhiên, có thể đọc sót.** Trong 20 đoạn thử, giọng Thiện Minh bỏ mất mấy từ ở một câu ("không biết cuối năm nay" trong đoạn 18). Pipeline có hai lớp phòng: (1) lưới an toàn theo nhịp đọc, không tốn thêm thời gian: câu nào có số giây mỗi âm tiết lệch khỏi trung vị quá khoảng 0,65–1,6 lần thì sinh lại (đo trên một truyện thật, mọi câu bình thường nằm trong 0,8–1,3 lần); (2) tùy chọn `--verify` cho ASR nghe lại từng câu, chính xác hơn nhưng làm thời gian dựng tăng gần gấp đôi.
- **Lỗi khi nạp mô hình với onnxruntime mới.** onnxruntime 1.31 từ chối đọc trọng số ngoài qua liên kết tượng trưng trong bộ nhớ đệm Hugging Face. `pipeline/scripts/_vieneu_local.py` tải mô hình thành file thật vào `models/vieneu/`.
- Mô hình 454 MB cộng bộ mã hóa âm thanh 87 MB, so với 63 MB của Piper. Giấy phép Apache 2.0.

## 2. Vì sao giọng `25hours_single-low` không dùng được

Bảng ký hiệu âm vị của mô hình này **không có các ký hiệu thanh điệu**. Bộ chuyển văn bản thành âm vị (espeak-ng) biểu diễn thanh điệu tiếng Việt bằng chữ số đứng sau âm tiết, ví dụ `lˈaː5w hˈaː6c`. Khi đưa vào mô hình, 806 trên 8.068 âm vị của văn bản thử (10,0%) bị bỏ vì không có trong bảng, và toàn bộ số bị bỏ là ký hiệu thanh điệu. Kết quả là giọng đọc mất dấu thanh, WER lên 38%.

Giọng `vais1000-medium` có đủ ký hiệu, không bỏ âm vị nào. Dữ liệu huấn luyện của nó (VAIS-1000) có giấy phép CC-BY 4.0.

Bài học: chọn giọng Piper cho tiếng Việt phải kiểm tra bảng ký hiệu của mô hình, không chỉ nhìn tên ngôn ngữ.

## 3. Vì sao bỏ edge-tts dù nó rõ hơn

edge-tts gọi một cổng không chính thức của Microsoft. Trong lần dựng "Lão Hạc":

- Dịch vụ trả về lỗi `NoAudioReceived` hàng loạt cho cả những câu bình thường, rồi một lúc sau lại chạy được. Thử từng câu riêng cho thấy lỗi **không phụ thuộc nội dung**, mà là bị giới hạn tần suất theo kết nối.
- Sau khoảng 40 phút mới xong 25 trên 77 đoạn của một truyện dài 15 phút, thì dừng.
- Đồ án giữa kỳ gặp đúng hiện tượng này: mã nguồn phải thử lại tới 24 lần mỗi đoạn, và cuốn Totto-chan phải dựng qua nhiều đợt.

Với một thư viện nhiều sách, tốc độ và độ tin cậy quan trọng hơn mức chênh 4,7 điểm WER. Piper dựng cùng truyện đó trong 134 giây lúc máy đang bận việc khác, và dựng một truyện dài tương đương trong 26 giây lúc máy rảnh. Không phụ thuộc mạng.

## 4. Lỗi của Piper nằm ở đâu

Phân tích 113 cặp từ bị ASR nghe khác với văn bản gốc trên audio Piper:

- **25 cặp (22%) chỉ khác thanh điệu**, ví dụ "vả" nghe thành "và", "mồi" thành "môi", "châm" thành "chầm". Đây là điểm yếu thật của giọng đọc.
- **Nhầm phụ âm cuối và phụ âm đầu**: "hạc" thành "hạt", "gắp" thành "gắt", "con" thành "co", "rân rấn" thành "dần dấn".
- **8 cặp không phải lỗi phát âm**: ASR viết "ba" thành "3", "năm" thành "5". Các cặp này cũng xuất hiện với edge-tts, nên WER thật của cả hai engine thấp hơn con số trong bảng một chút.
- Một số cặp là đồng âm trong giọng Bắc ("chí" và "trí", "xin" và "sinh"), ASR không phân biệt được và cũng không phải lỗi.

## 5. Điều chưa đo

- **Độ tự nhiên** chưa có điểm nghe chủ quan (MOS). Cần 5–10 người nghe chấm mù.
- **Tốc độ đọc** của Piper là khoảng 245 âm tiết mỗi phút, nhanh hơn mức 201 của bộ sách nói PhoAudiobook. Chưa thử đọc chậm lại.
- **Câu thoại rất ngắn** ("Vâng!", "Này!", "À!") chỉ dài khoảng 0,2 giây, có thể nghe cụt.
- Chưa so với F5-TTS tiếng Việt (cần GPU).
- Chưa đo tỉ lệ câu bị đọc sót của VieNeu-TTS trên cả một cuốn sách bằng ASR.

## 6. Hệ quả cho ứng dụng

- Piper trả audio theo từng câu, nên pipeline ghi được **mốc thời gian mức câu** (`sentences.csv`) mà không cần mô hình căn chỉnh riêng. Bản giữa kỳ chỉ có mốc mức đoạn. Ứng dụng nhờ đó tô sáng và tua theo từng câu.
- Mô hình Piper 63 MB, chạy được trên Android, nên về sau có thể đọc trực tiếp trên điện thoại thay vì tạo audio trước.
- Mỗi giọng đọc là một bản DAISY riêng của cuốn sách. Mốc thời gian của hai giọng khác nhau, nên ứng dụng nhớ vị trí theo **số thứ tự câu** để khi đổi giọng vẫn nghe tiếp đúng câu.
