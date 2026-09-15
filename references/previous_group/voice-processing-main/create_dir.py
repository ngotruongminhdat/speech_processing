import os

def create_dir(range, base_dir):
    # Tạo thư mục cho x hồi
    for i in range:
        # Tên thư mục: ./output/[Thuỷ Hử] Hồi {i}
        dir_path = os.path.join(base_dir, f"[Thuỷ Hử] Hồi {i}")
        
        # Tạo thư mục (bao gồm cả các thư mục cha nếu chưa có)
        os.makedirs(dir_path, exist_ok=True)

    print("Đã tạo xong thư mục cho các hồi!")
