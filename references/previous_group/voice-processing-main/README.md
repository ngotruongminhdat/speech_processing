# Hướng dẫn tạo sách Daisy trên Python 3.10 (Project 3)

## Bước 1: Chuẩn bị dữ liệu
1.1. Tạo thư mục `audio` và lưu các file âm thanh `.mp3` theo định dạng:  
```
audio/Thuy-Hu-{hoi}.mp3
```
Ví dụ:  
```
audio/Thuy-Hu-68.mp3
```

1.2. Tạo thư mục `doc` chứa các file văn bản `.docx` của từng hồi, đặt tên theo định dạng:  
```
doc/Hoi{hoi}.docx
```
Ví dụ:  
```
doc/Hoi1.docx
```

---

## Bước 2: Cài đặt môi trường
Tạo môi trường và cài đặt thư viện cần thiết từ file `requirements.txt`:  
```bash
conda create --name <env> --file requirements.txt
```

---

## Bước 3: Tải mô hình LLM
Mục đích của bước này là để LLM tự động hiệu đính chính tả dựa trên nội dung tham chiếu từ file `.docx`.  

Tải mô hình về máy:  
```bash
ollama pull llama3
```

---

## Bước 4: Cấu hình phạm vi chạy
Mở file `daisy_pipeline.py` và chỉnh sửa giá trị `range` để chọn các hồi cần xử lý.  

Ví dụ, nếu chỉ muốn kiểm thử hồi 1:  
```python
range = range(1, 2)
```

> Nhóm đã cung cấp sẵn một đoạn test cho hồi 1.

---

## Bước 5: Chạy pipeline
```python
python ./daisy_pipeline.py
```

---

## Bước 6: Kiểm thử
Mở file sách Daisy bằng **Easy Reader** để kiểm thử kết quả.
