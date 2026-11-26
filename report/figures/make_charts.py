"""Vẽ các biểu đồ của báo cáo từ số liệu ở report/tts_comparison.md.

Chạy: .venv/bin/python report/figures/make_charts.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
COLOR = {"edge-tts": "#1b6ca8", "Piper": "#c8553d", "VieNeu-TTS": "#3a8f5c"}

# (giọng, hệ, WER %, CER %)
WER = [
    ("VieNeu Quỳnh Anh", "VieNeu-TTS", 4.20, 1.79),
    ("VieNeu Ngọc Huyền", "VieNeu-TTS", 4.43, 2.43),
    ("VieNeu Ngọc Linh", "VieNeu-TTS", 5.10, 2.19),
    ("Hoài My (edge-tts)", "edge-tts", 5.25, 2.21),
    ("VieNeu Thiện Minh", "VieNeu-TTS", 5.40, 2.97),
    ("Piper vais1000", "Piper", 9.98, 5.00),
    ("Piper 25hours", "Piper", 38.11, 21.75),
]
# (giọng, hệ, âm tiết/phút, % khoảng lặng)
PACE = [
    ("Hoài My (edge-tts)", "edge-tts", 186, 34.8),
    ("VieNeu Ngọc Linh", "VieNeu-TTS", 241, 15.1),
    ("VieNeu Thiện Minh", "VieNeu-TTS", 254, 20.7),
    ("Piper vais1000", "Piper", 275, 6.7),
]


def vi(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def legend(ax):
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLOR.values()]
    ax.legend(handles, COLOR.keys(), frameon=False, loc="upper right")


def wer_chart():
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    names = [r[0] for r in WER][::-1]
    vals = [r[2] for r in WER][::-1]
    bars = ax.barh(names, vals, color=[COLOR[r[1]] for r in WER][::-1], height=0.62)
    for b, v in zip(bars, vals):
        ax.text(v + 0.6, b.get_y() + b.get_height() / 2, vi(v, 2) + "%", va="center", fontsize=9)
    ax.set_xlabel("Tỉ lệ lỗi từ (WER, %), thấp hơn là rõ hơn")
    ax.set_xlim(0, 44)
    ax.tick_params(axis="y", length=0)
    legend(ax)
    fig.tight_layout()
    fig.savefig(OUT / "bieu-do-wer.pdf")


def pace_chart():
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.5), sharey=True)
    names = [r[0] for r in PACE][::-1]
    colors = [COLOR[r[1]] for r in PACE][::-1]
    rate = [r[2] for r in PACE][::-1]
    sil = [r[3] for r in PACE][::-1]
    for ax, vals, label, fmt, inside in ((a, rate, "Tốc độ đọc (âm tiết/phút)", str, True),
                                         (b, sil, "Phần thời gian là khoảng lặng (%)", lambda v: vi(v) + "%", False)):
        bars = ax.barh(names, vals, color=colors, height=0.6)
        for bar, v in zip(bars, vals):
            x = v - max(vals) * 0.03 if inside else v + max(vals) * 0.02
            ax.text(x, bar.get_y() + bar.get_height() / 2, fmt(v), va="center", fontsize=9,
                    ha="right" if inside else "left", color="white" if inside else "black")
        ax.set_xlabel(label)
        ax.set_xlim(0, max(vals) * 1.22)
        ax.tick_params(axis="y", length=0)
    a.axvline(201, color="#555", linestyle="--", linewidth=1)
    a.set_ylim(-0.5, 4.0)
    a.text(205, 3.6, "PhoAudiobook: 201", ha="left", fontsize=8, color="#333")
    fig.tight_layout()
    fig.savefig(OUT / "bieu-do-nhip-doc.pdf")


if __name__ == "__main__":
    wer_chart()
    pace_chart()
