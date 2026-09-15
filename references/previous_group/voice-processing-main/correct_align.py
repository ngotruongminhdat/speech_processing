import json
import docx
import ollama
from difflib import SequenceMatcher


def find_best_match(target_text, reference_text, threshold=0.6):
    """
    Tìm đoạn text tương đồng nhất trong reference
    """
    target_words = target_text.lower().split()
    if len(target_words) == 0:
        return None, 0, 0
    
    # Tìm kiếm sliding window
    best_match = ""
    best_score = 0
    best_start = 0
    best_end = 0
    
    # Thử các kích thước cửa sổ khác nhau
    for window_size in [len(target_words), len(target_words) * 2, len(target_words) * 3]:
        ref_words = reference_text.lower().split()
        
        for i in range(max(1, len(ref_words) - window_size + 1)):
            window_text = " ".join(ref_words[i:i + window_size])
            
            # Tính độ tương đồng
            similarity = SequenceMatcher(None, target_text.lower(), window_text).ratio()
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = " ".join(reference_text.split()[i:i + window_size])
                best_start = i
                best_end = i + window_size
    
    return best_match if best_score >= threshold else None, best_start, best_end

def remove_text_from_reference(reference_text, start_word_idx, end_word_idx):
    """
    Loại bỏ đoạn text đã sử dụng khỏi reference
    """
    words = reference_text.split()
    remaining_words = words[:start_word_idx] + words[end_word_idx:]
    return " ".join(remaining_words)

def correct_text(align_result, doc_input, correct_output):
    print(f"\n=== Xử lý {align_result} ===")
    # Đọc file Word tham chiếu
    doc = docx.Document(doc_input)
    ref_text = " ".join([p.text for p in doc.paragraphs if p.text.strip()])

    # Đọc file JSON chứa segment
    with open(align_result, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Độ dài reference ban đầu: {len(ref_text.split())} từ\n")

    for i, seg in enumerate(data["segments"]):
        seg_text = seg["text"].strip()
        print(f"--- Segment {i+1} ---")
        print(f"Text gốc: {seg_text}")
        
        # Tìm đoạn tương ứng trong reference
        matched_ref, start_idx, end_idx = find_best_match(seg_text, ref_text)
        
        if matched_ref:
            print(f"Tìm thấy reference: {matched_ref}")
            
            # Gọi LLaMA 3 để hiệu đính
            prompt = (
                "Bạn là chuyên gia về tiếng Việt, có nhiệm vụ hiệu đính chính tả.\n\n"
                f"Đoạn văn nhận dạng từ giọng nói:\n{seg_text}\n\n"
                f"Văn bản chuẩn để tham khảo:\n{matched_ref}\n\n"
                "Yêu cầu:\n"
                "- Hiệu đính chính tả và dấu câu của đoạn văn gốc để khớp với văn bản tham chiếu.\n"
                "- Giữ nguyên số lượng từ, không được thêm hoặc bớt từ.\n"
                "- Chỉ trả về văn bản đã hiệu đính, không được giải thích, không thêm tiêu đề hay mô tả như "
                "'Đây là kết quả' hoặc 'Here is the revised text'.\n"
                "- Trả về kết quả dưới dạng văn bản thuần túy."
            )
            
            try:
                response = ollama.chat(
                    model="llama3",
                    messages=[{"role": "user", "content": prompt}],
                )
                
                corrected = response["message"]["content"].strip()
                
                # Loại bỏ các dòng giải thích nếu có
                lines = corrected.split('\n')
                corrected = lines[0] if lines else corrected
                
                print(f"Sau correct: {corrected}")
                
                # Cập nhật segment
                seg["text"] = corrected
                
                # Loại bỏ đoạn đã sử dụng khỏi reference
                ref_text = remove_text_from_reference(ref_text, start_idx, end_idx)
                print(f"Còn lại {len(ref_text.split())} từ trong reference")
                
            except Exception as e:
                print(f"Lỗi khi gọi LLaMA: {e}")
                print("Giữ nguyên text gốc")
        else:
            print("Không tìm thấy reference phù hợp, giữ nguyên text gốc")
        
        print()

    # Lưu file kết quả
    with open(correct_output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Hoàn thành! Kết quả đã lưu vào {correct_output}")
