# Ứng dụng đọc sách tiếng Việt cho người khiếm thị trên thiết bị di động

Đồ án cuối kỳ môn Xử lý tiếng nói (branch `final_project`).

## Cấu trúc

| Thư mục | Nội dung | Rubric |
|---|---|---|
| `literature/papers/` | PDF các bài báo (Q1/Q2, CORE A/A*) | 30% |
| `literature/notes/` | Tóm tắt, phân tích ưu/nhược từng bài | 30% |
| `demo/` | Pipeline OCR → chuẩn hóa → TTS chạy bằng code mở | 20% |
| `app/` | Ứng dụng di động (client) + backend FastAPI | 30% |
| `report/` | Báo cáo cuối kỳ, slide, số liệu đánh giá | 20% |

## Pipeline

```
Ảnh trang sách (camera) → OCR tiếng Việt → Chuẩn hóa văn bản → TTS tiếng Việt → Phát audio + điều khiển trợ năng
```

## Môi trường

- Python 3.12, `.venv/` ở thư mục gốc
- Máy dev: CPU 16 nhân, 62 GB RAM, GPU AMD Vega tích hợp (không có CUDA) → ưu tiên mô hình chạy CPU hoặc API
