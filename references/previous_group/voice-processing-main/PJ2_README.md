# Thống kê Phiên Âm trong Project 2

## (a) Thống kê số lượng âm tiết tiếng Việt trong từ điển

- **Thống kê theo phiên âm**:  
  Tổng số loại âm tiết khác nhau: **6603**  
  (Chi tiết xem trong file `syllable_counts.csv` và `syllable_report.txt`)  

  **Cách chạy code**:  
  ```bash
  python ./project2/statistic.py
  ```  
  Sau khi chạy, sẽ tạo ra 2 file:  
  1. `syllable_counts.csv`: chứa danh sách các âm tiết và số lần xuất hiện trong từ điển.  
  2. `syllable_report.txt`: chứa báo cáo chi tiết thống kê các âm tiết theo phiên âm.  

- **Thống kê theo âm tiết trực tiếp**:  
  Tổng số loại âm tiết khác nhau: **6775**  

  **Cách chạy code**:  
  ```bash
  python ./project2/main.py
  ```  
  Sau khi chạy, sẽ tạo ra 2 file:  
  1. `syllable.txt`: chứa danh sách các âm tiết trực tiếp (Không phiên âm)
  2. `undefined.txt`: danh sách các âm tiết không đém được

---

## (b) Thống kê số lượng âm tiết khả dĩ theo tổ hợp

Công thức:  
```
Phụ_âm_đầu × Âm_đệm × Âm_chính × Âm_cuối × Thanh_điệu
```

Với:  
- Phụ âm đầu: 22  
- Âm đệm: 2  
- Âm chính: 16  
- Âm cuối: 9  
- Thanh điệu: 6  

👉 Tổng số tổ hợp khả dĩ: **130,878**  

(Chi tiết xem trong file `syllable_counts.txt` và `syllable_combinations.csv`)  

**Cách chạy code**:  
```bash
python ./project2/generate_combinations.py
```

---

## (c) So sánh kết quả (a) và (b)

- Số lượng âm tiết thực tế trong từ điển (~6,600 – 6,700) nhỏ hơn rất nhiều so với số lượng âm tiết khả dĩ (~130,000).  
- **Nguyên nhân**:  
  - Không phải mọi tổ hợp phụ âm – âm đệm – âm chính – âm cuối – thanh điệu đều tồn tại trong tiếng Việt.  
  - Một số âm tiết khác nhau về cách viết nhưng lại giống nhau về cách phát âm, dẫn đến chênh lệch giữa thống kê trên tổ hợp lý thuyết và thực tế.
