"""Các giọng đọc mà thư viện cung cấp cho người nghe chọn.

Mỗi giọng là một bản DAISY đầy đủ của cuốn sách, nằm ở
books/<slug>/voices/<id>/ (cùng cấu trúc metadata/ + build/chapter_NN/ như thư
mục gốc của sách). Thư mục gốc books/<slug>/build/ giữ văn bản nguồn và bản
Piper cũ, dùng làm giọng dự phòng cho những phần chưa dựng xong giọng mới.
"""

VOICES = {
    "nu": {"engine": "vieneu", "voice": "Ngọc Linh", "label": "Giọng nữ", "name": "Ngọc Linh"},
    "nam": {"engine": "vieneu", "voice": "Thiện Minh", "label": "Giọng nam", "name": "Thiện Minh"},
}
FALLBACK = {"id": "piper", "label": "Giọng dự phòng", "name": "Piper"}


def narrator(vid: str) -> str:
    v = VOICES[vid]
    return f"{v['name']}, {v['label'].lower()} (VieNeu-TTS v3 Turbo, giọng tổng hợp mã nguồn mở)"
