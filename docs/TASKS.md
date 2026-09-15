# Phân công nhiệm vụ nhóm Totto-chan — Đồ án giữa kỳ DAISY

> **Sách:** Totto-chan Bên Cửa Sổ — Tetsuko Kuroyanagi (ISBN: 9786041194861, ~46 chương, ước tính ≈6.6 giờ audio)
> **Deadline nộp:** 30/09 · **Yêu cầu:** mỗi thành viên ≥60 phút audio (tổng ≥240 phút), làm trọn vẹn cả cuốn
> **Lưu ý từ GV:** làm xong một ít (chương 1) thì **gửi xem trước**, được duyệt mới làm toàn bộ

**Dây chuyền tổng thể:** Lộc làm ra chữ → Vy biến chữ thành tiếng → Đạt ghép chữ với tiếng thành sách DAISY → Hà Anh kiểm tra và viết báo cáo.

```
EPUB ──> LỘC: dtbook.xml (id từng đoạn) ──┬──> ĐẠT: smil + opf + ncx ──> zip + sha256
              │ text sạch                  │            │
              └──> VY: mp3 + timestamp ────┘            └──> HÀ ANH: QA ──> Báo cáo + Slide ──> Nộp 30/09
```

---

## 👤 Đình Lộc — Nội dung (DTBook XML)

**Nhiệm vụ:** biến file EPUB thành văn bản có cấu trúc chuẩn DAISY.

- [ ] Extract text từ `Totto-chan.epub` (có sẵn trên Drive nhóm, không DRM)
- [ ] Làm sạch text: sửa lỗi ngắt dòng, ký tự lạ, kiểm tra chính tả
- [ ] Viết thành file `dtbook.xml` cho từng chương: mỗi đoạn văn bọc trong thẻ `<p><sent id="...">` với **id duy nhất** (ví dụ `id_1`, `id_2`... theo format nhóm khóa trước)

**Output giao cho ai:**
- `dtbook.xml` từng chương → giao **Đạt** (để trỏ SMIL vào)
- Text sạch từng đoạn (đúng thứ tự id) → giao **Vy** (để đưa vào TTS)

*Hiểu nôm na: Lộc là biên tập viên — sản phẩm là bản thảo sạch, đánh số từng đoạn.*

---

## 👤 Lê Tường Vy — Audio (TTS & MP3)

**Nhiệm vụ:** biến text của Lộc thành giọng đọc.

- [ ] Chọn và test giọng TTS tiếng Việt (ưu tiên **Azure Neural TTS**: giọng Việt tự nhiên + hỗ trợ SSML)
- [ ] Dùng SSML tinh chỉnh: ngắt nghỉ giữa đoạn, tốc độ, tránh đọc sai số/từ nước ngoài
- [ ] Chạy TTS toàn bộ 46 chương → xuất **1 file mp3 mỗi chương**
- [ ] **Ghi bảng timestamp**: đoạn `id_1` bắt đầu/kết thúc giây nào trong mp3 (Azure trả về word boundary tự động — lấy từ API thay vì căn tay)
- [ ] Nghe kiểm tra chất lượng, đảm bảo tổng ≥240 phút

**Output giao cho ai:**
- File `chuongNN.mp3` + bảng timestamp (`id, clipBegin, clipEnd`) → giao **Đạt**

*Hiểu nôm na: Vy là "người đọc sách" — sản phẩm là audio kèm biên bản ghi giờ.*

---

## 👤 Minh Đạt — Kỹ thuật (SMIL/OPF/NCX + đóng gói)

**Nhiệm vụ:** ghép sản phẩm của Lộc và Vy thành sách DAISY hoàn chỉnh.

- [ ] Viết script sinh `mo0.smil` từng chương: nối `id` trong XML của Lộc với timestamp của Vy
- [ ] Viết script sinh `book.opf` (metadata 9 trường + manifest), `navigation.ncx` (mục lục), `resources.res`
- [ ] Test sách trong Thorium Reader: bấm mục lục nhảy đúng, audio khớp highlight
- [ ] Đóng gói: `Totto-chan.zip` + `sha256sums.txt` từng chương, xếp đúng cấu trúc thư mục nộp

**Output từng chương (4 file do Đạt tạo):**

```
Totto-chan-Chương 1/
├── dtbook.xml        ← Lộc làm
├── chuong01.mp3      ← Vy làm
├── mo0.smil          ← ĐẠT: đồng bộ text-audio
├── book.opf          ← ĐẠT: manifest + metadata 9 trường
├── navigation.ncx    ← ĐẠT: mục lục điều hướng
└── resources.res     ← ĐẠT: file tài nguyên chuẩn DAISY
```

**Output giao cho ai:**
- Sách DAISY chạy được → giao **Hà Anh** để QA
- Bộ nộp cuối (zip + hash, đúng cấu trúc `MSHV1_MSHV2_MSHV3_MSHV4/Totto-chan-Chương N/`) → nộp GV 30/09

*Hiểu nôm na: Đạt là thợ đóng sách — nhận bản thảo và băng ghi âm, đóng thành cuốn sách hoàn chỉnh có mục lục.*

---

## 👤 Hà Anh — QA + Báo cáo & Slide

**Nhiệm vụ:** kiểm định chất lượng và trình bày kết quả.

- [ ] Cài Thorium Reader, QA từng sách theo checklist: nghe thử từng mp3, kiểm tra đồng bộ text-audio, điều hướng mục lục, soát chính tả, kiểm tra nội dung zip
- [ ] Tổng hợp phần viết của 3 người → **báo cáo** (tham khảo `references/previous_group/BaoCao.pdf`)
- [ ] Làm **slide thuyết trình** (tham khảo `references/previous_group/Slide_GK.pdf`)
- [ ] Gửi bản chương 1 cho GV **xem trước** như yêu cầu

**Output:** báo cáo + slide + xác nhận QA từng sản phẩm.

*Hiểu nôm na: Hà Anh là người nghiệm thu và phát ngôn của nhóm.*

---

## 📌 Quy định bổ sung từ GV (cập nhật 15/09)

- **Footnote phải "chia riêng"** (trả lời trên nhóm lớp): không đọc chú thích chèn vào giữa câu. Trong DAISY 3: đánh dấu `<noteref>` tại vị trí tham chiếu + khối `<note>` riêng có audio clip riêng, để trình đọc cho phép bật/tắt phần chú thích. *Totto-chan có đúng 1 footnote* — `[1]` trong chương "Con Rocky biến mất" (nội dung chú thích nằm cuối sách, sau chữ HẾT).
- **Mục lục EPUB bị thiếu**: NCX chỉ liệt kê 47 chương nhưng sách thực tế còn ~25 phần nữa (14 chương từ "Ngôi trường cũ đổ nát" đến "Sayonara, Sayonara", Lời kết, và 10 hồ sơ bạn học trường Tomoe). Khi làm trọn cuốn phải lấy đủ theo spine, không dựa vào mục lục EPUB. Tổng sách ≈ 5,5 giờ audio → dư chuẩn 4 giờ.

## ⚠️ 3 thỏa thuận cần chốt ngay tuần này

| # | Giữa ai | Nội dung cần chốt |
|---|---------|-------------------|
| 1 | Lộc ↔ Đạt | Quy ước đặt `id` trong dtbook.xml (ví dụ `id_1`, `id_2`... liên tục theo chương) |
| 2 | Vy ↔ Đạt | Format bảng timestamp: CSV `id, file_mp3, clipBegin, clipEnd` |
| 3 | Cả nhóm | Làm **chương 1 chạy hết dây chuyền trước** → gửi thầy duyệt → mới nhân rộng ra 45 chương còn lại |

## 📚 Tài nguyên tham khảo

- EPUB sách + kế hoạch nhóm: `sources/`
- Code + báo cáo + slide mẫu của nhóm khóa trước: `references/previous_group/` (pipeline mẫu: `voice-processing-main/` — xem `map_to_smill.py`, `create_daisy_file.py`)
- Drive nhóm: https://drive.google.com/drive/folders/1DSqBv-qDfXocF1TV8Z0PUZkjtNKzqQeE
- Drive bài mẫu khóa trước: https://drive.google.com/drive/folders/1-8dyNoivdWQCUihe4r26vSjx-OI603LH
