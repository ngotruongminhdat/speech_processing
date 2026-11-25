"""Nạp VieNeu-TTS v3 Turbo (ONNX, chạy CPU) từ thư mục models/vieneu/.

Vì sao cần file này: gói `vieneu` tải mô hình vào bộ nhớ đệm của Hugging Face,
nơi mỗi file là một liên kết tượng trưng. onnxruntime từ bản 1.2x từ chối nạp
trọng số ngoài (`*.data`) qua liên kết đó ("External data path escapes model
directory"). Cách xử lý: tải thành file thật vào models/vieneu/ rồi trỏ engine
vào đó. Gói `vieneu` không cho truyền thư mục codec, nên phải chèn tham số này.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = REPO / "models" / "vieneu"
BACKBONE_REPO = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
CODEC_REPO = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
SAMPLE_RATE = 48_000


def _ensure_files():
    onnx_dir, codec_dir = MODEL_DIR / "onnx_update", MODEL_DIR / "codec"
    if not (onnx_dir / "vieneu_prefill.onnx").exists():
        from huggingface_hub import snapshot_download
        snapshot_download(BACKBONE_REPO, allow_patterns=["onnx_update/*"], local_dir=MODEL_DIR)
    if not (codec_dir / "moss_audio_tokenizer_decode_full.onnx").exists():
        from huggingface_hub import snapshot_download
        snapshot_download(CODEC_REPO, local_dir=codec_dir)
    return onnx_dir, codec_dir


def load_vieneu(threads: int = 0):
    onnx_dir, codec_dir = _ensure_files()
    from vieneu import Vieneu
    from vieneu._v3_turbo_engine import onnx_runtime_lite as orl

    if not getattr(orl.OnnxV3LiteEngine, "_local_codec", False):
        orig = orl.OnnxV3LiteEngine.__init__

        def init(self, *args, **kw):
            kw.setdefault("codec_dir", str(codec_dir))
            return orig(self, *args, **kw)

        orl.OnnxV3LiteEngine.__init__ = init
        orl.OnnxV3LiteEngine._local_codec = True
    return Vieneu(onnx_dir=str(onnx_dir), backend="onnx", threads=threads)
