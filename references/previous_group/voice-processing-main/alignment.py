from xml.etree.ElementTree import Element, SubElement, ElementTree
import whisperx
import torch
from lxml import etree
import json

LANG = "vi"
compute_type = "float16"

try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
except Exception:
    device = "cpu"
print(f"🔄 Đang chạy trên device={device}...")

def alignment(audio_path, output_path):
    # 1) Load transcription model và transcribe
    print("🔄 Đang load model transcription và thực hiện transcription...")
    model = whisperx.load_model("turbo", device=device, compute_type=compute_type, language=LANG)
    result = model.transcribe(audio_path, language=LANG)
    print(f"✅ Transcription xong: {len(result.get('segments', []))} segments")

    # 2) Load align model và align
    print("🔄 Đang load model align...")
    model_a, metadata = whisperx.load_align_model(language_code=LANG, device=device)

    print("🔄 Đang thực hiện forced alignment với transcript từ WhisperX...")
    aligned_result = whisperx.align(result["segments"], model_a, metadata, audio_path, device)
    print(f"✅ Hoàn thành alignment. Có {len(aligned_result.get('segments', []))} đoạn.")

    # 3) Xuất kết quả alignment ra JSON (tương thích UTF-8)
    export_data = {
        "transcription_model": "turbo",
        "device": device,
        "audio_file": audio_path,
        "segments": aligned_result.get("segments"),
        # một số phiên bản whisperx trả về word-level dưới key khác nhau; gồm cả để an toàn
        "word_segments": aligned_result.get("word_segments") or aligned_result.get("words") or aligned_result.get("tokens")
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"✅ Đã xuất kết quả alignment: {output_path}")
