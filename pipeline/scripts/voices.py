"""Các giọng đọc mà thư viện cung cấp cho người nghe.

Mỗi giọng là một bản DAISY đầy đủ của cuốn sách, nằm ở
books/<slug>/voices/<id>/ (cùng cấu trúc metadata/ + build/chapter_NN/ như thư
mục gốc của sách). Phần nào chưa dựng xong giọng chính thì trang web tạm phát một
giọng dự phòng theo thứ tự FALLBACKS: bản VieNeu nữ (voices/nu/) nếu có, không
thì bản Piper ở thư mục gốc của sách.

Lịch sử: 05/11/2026 thư viện dùng hai giọng VieNeu-TTS (nu: Ngọc Linh, nam: Thiện
Minh). 16/11/2026 người dùng chọn quay về giọng Hoài My của Microsoft (edge-tts)
vì ngữ điệu hay hơn; hai bản VieNeu vẫn nằm trên đĩa, thêm lại vào VOICES là dùng
được ngay.
"""

VOICES = {
    "hm": {"engine": "edge", "voice": "vi-VN-HoaiMyNeural", "label": "Giọng nữ", "name": "Hoài My"},
}

# Giọng dự phòng cho phần chưa có giọng chính, ưu tiên theo thứ tự. "dir" tính từ
# thư mục gốc của sách (rỗng = chính thư mục gốc, nơi có bản Piper cũ).
FALLBACKS = [
    {"id": "nu", "label": "Giọng nữ", "name": "Ngọc Linh", "dir": "voices/nu", "fallback": True},
    {"id": "piper", "label": "Giọng dự phòng", "name": "Piper", "dir": "", "fallback": True},
]

ENGINE_NOTE = {
    "edge": "Microsoft Neural TTS, qua edge-tts",
    "vieneu": "VieNeu-TTS v3 Turbo, giọng tổng hợp mã nguồn mở",
}
TTS_SCRIPT = {"edge": "tts_chapter_edge.py", "vieneu": "tts_chapter_vieneu.py"}


def narrator(vid: str) -> str:
    v = VOICES[vid]
    return f"{v['name']}, {v['label'].lower()} ({ENGINE_NOTE[v['engine']]})"
