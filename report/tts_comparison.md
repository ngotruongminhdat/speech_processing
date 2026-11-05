# So sánh engine TTS tiếng Việt cho việc tạo sách nói

Đo ngày 05/11/2026 trên máy dev: AMD Ryzen 7 5700G (16 luồng), 62 GB RAM, **không có GPU CUDA**.
Văn bản thử: 20 đoạn đầu của truyện "Lão Hạc" (Nam Cao), 1.333 âm tiết, từ câu thoại 7 ký tự đến đoạn 1.309 ký tự.
Số liệu gốc: `report/tables/tts_piper_speed.csv`, `report/tables/tts_intelligibility.csv`. Mã đo: `demo/tts_bench_piper.py`, `demo/tts_intelligibility.py`.

## 1. Kết quả

| Engine | Chạy ở đâu | Tốc độ tạo | WER ↓ | CER ↓ | Dùng được |
|---|---|---|---|---|---|
| edge-tts, giọng Hoài My | Dịch vụ ngoài của Microsoft | Không ổn định, xem mục 3 | **5,25%** | **2,21%** | Có, nhưng không tin cậy được |
| Piper `vi_VN-vais1000-medium` | CPU máy dev | **Nhanh gấp 27–40 lần thời gian thực** | 9,98% | 5,00% | **Có, được chọn** |
| Piper `vi_VN-25hours_single-low` | CPU máy dev | Nhanh gấp khoảng 9 lần khi đo cùng lúc | 38,11% | 21,75% | Không |

**Cách đo độ rõ.** Cho mô hình nhận dạng tiếng nói `faster-whisper large-v3-turbo` nghe lại audio, so văn bản nhận được với văn bản gốc sau khi viết thường và bỏ dấu câu. Sai số của bản thân ASR là như nhau cho mọi engine, nên các con số dùng để **so sánh giữa các engine**, không phải độ rõ tuyệt đối. Đây là cách bài PhoAudiobook (ACL 2025) đánh giá TTS tiếng Việt.

**Cách đo tốc độ.** RTF = thời gian tạo chia cho thời lượng audio. Khi dựng sách thật, không có tiến trình khác tranh CPU, Piper đạt RTF 0,025–0,037. Ví dụ 9 chương đầu của "Tắt đèn": 57,7 phút audio tạo trong 93 giây.

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
- Chưa so với VieNeu-TTS và F5-TTS tiếng Việt.

## 6. Hệ quả cho ứng dụng

- Piper trả audio theo từng câu, nên pipeline ghi được **mốc thời gian mức câu** (`sentences.csv`) mà không cần mô hình căn chỉnh riêng. Bản giữa kỳ chỉ có mốc mức đoạn. Ứng dụng nhờ đó tô sáng và tua theo từng câu.
- Mô hình 63 MB, chạy được trên Android, nên về sau có thể đọc trực tiếp trên điện thoại thay vì tạo audio trước.
