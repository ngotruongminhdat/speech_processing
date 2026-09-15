import json
import ollama

JSON_PATH = "./alignResult/ngu_van_aligned_result.json"  # đổi đường dẫn cho phù hợp
OUTPUT = "./alignResult/ngu_van_aligned_result_corrected.json"

BOOK_TITLE = "Bộ sách cánh diều - Ngữ Văn Lớp 6 Tập 2"

# Đọc file JSON chứa segments
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Đang hiệu đính {len(data['segments'])} segments...\n")

for i, seg in enumerate(data["segments"]):
    seg_text = seg["text"].strip()
    print(f"--- Segment {i+1}/{len(data['segments'])} ---")
    print(f"Text gốc: {seg_text}")

    prompt = (
        f"Bạn là biên tập viên sách giáo khoa, hãy hiệu đính chính tả và dấu câu "
        f"cho đoạn văn dưới đây. Đoạn này trích từ sách '{BOOK_TITLE}'.\n\n"
        f"Đoạn văn:\n{seg_text}\n\n"
        "Yêu cầu:\n"
        "- Chỉ sửa lỗi chính tả, dấu câu, chữ hoa/chữ thường theo chuẩn tiếng Việt, bỏ qua nếu đã đúng chính tả.\n"
        "- Giữ nguyên thuật ngữ và nội dung mang tính giáo dục, tuyệt đối không thêm hoặc bớt ý!\n"
        "- Không giải thích hay tóm tắt.\n"
        "- Văn phong phải nghiêm túc, rõ ràng, phù hợp với sách giáo khoa.\n"
        "- Không thêm dòng này Here is the revised text:\n"
        "- Cũng không thêm note giống như vậy: (Note: No changes made to the content or wording)"
        "- Chỉ trả về văn bản đã hiệu đính, tuyệt đối không kèm tiêu đề hay mô tả hay kèm note thêm gì cả\n"
    )

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
        )

        corrected = response["message"]["content"].strip()
        print(f"Sau correct: {corrected}\n")

        # Cập nhật segment
        seg["text"] = corrected

    except Exception as e:
        print(f"[Lỗi] khi gọi LLaMA: {e}")
        print("Giữ nguyên text gốc\n")

# Lưu file kết quả
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Hoàn thành! Kết quả đã lưu vào {OUTPUT}")
