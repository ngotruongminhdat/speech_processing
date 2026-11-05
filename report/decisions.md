# Nhật ký quyết định thiết kế

| Ngày | Quyết định | Lý do | Phương án thay thế |
|---|---|---|---|
| 2026-11-04 | Chọn hướng ứng dụng (3b) | Đề tài là "ứng dụng"; demo và app dùng chung pipeline | Hướng nghiên cứu (ablation) |
| 2026-11-04 | Mô hình chạy CPU hoặc API, fine-tune trên Colab/Kaggle | Máy dev không có CUDA | Thuê GPU cloud |
| 2026-11-05 | Đổi trọng tâm từ OCR sách giấy sang **ứng dụng đọc sách DAISY**, kế thừa đồ án giữa kỳ | Đề bài không yêu cầu sách giấy; giữa kỳ đã tạo sách DAISY, cuối kỳ làm app để nghe chúng là mạch tự nhiên của môn học; phần tiếng nói là lõi | Giữ hướng OCR (rủi ro cao, lệch môn) |
| 2026-11-05 | Thư viện nhiều sách, nguồn là tác phẩm **thuộc phạm vi công cộng** trên Wikisource | Có nhiều sách thật để demo; không vướng bản quyền khi deploy công khai (Luật SHTT Điều 27: suốt đời tác giả + 50 năm) | Xin sách của nhóm khác; dùng sách còn bản quyền |
| 2026-11-05 | TTS chuyển từ edge-tts sang **Piper `vi_VN-vais1000-medium`** chạy trên CPU | edge-tts bị bóp tần suất, 40 phút mới được 25/77 đoạn; Piper nhanh gấp 27–40 lần thời gian thực, WER 10,0% so với 5,3%; xem `tts_comparison.md` | Azure TTS trả phí; F5-TTS (chậm trên CPU) |
| 2026-11-05 | Loại giọng Piper `25hours_single-low` | Bảng âm vị không có ký hiệu thanh điệu, 10% âm vị bị bỏ, WER 38% | – |
| 2026-11-05 | Đồng bộ văn bản với audio ở **mức câu** | Piper trả audio theo câu nên có mốc câu miễn phí; giữa kỳ chỉ có mức đoạn, tua thô | Forced alignment bằng mô hình riêng |
| 2026-11-05 | App là **web tĩnh + PWA**, không phải app gốc | Chạy ngay trên mọi điện thoại, deploy bằng GitHub Pages, kế thừa giao diện giữa kỳ; vẫn có điều khiển màn hình khóa và nghe ngoại tuyến | Flutter, React Native |
| 2026-11-05 | Sách lưu ngoại tuyến để trong **IndexedDB**, không qua service worker | Phát audio từ bộ đệm của service worker cần tự xử lý yêu cầu Range; phát từ Blob thì không | Cache API + xử lý Range |
| 2026-11-05 | Deploy lên branch `gh-pages`, **giữ nguyên `build/` của giữa kỳ** | Link giữa kỳ đã nộp không được hỏng; branch `mid_term_project` không bị sửa | Đổi nguồn Pages và bỏ trang cũ; repo mới |
