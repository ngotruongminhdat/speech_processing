#!/usr/bin/env python3
from pathlib import Path
import sys

# đảm bảo import được project1.mappings
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'project1'))

from mappings import am_dau_map, am_dem_map, am_chinh_map, am_cuoi_map, TONE_DIACRITIC_TO_NUM, TONE_NUM_DEFAULT

def _count_phonemes(d):
    # Đếm số lượng âm vị unique (keys) từ bên trái
    return len(set(d.keys()))

def _flatten_values(d):
    vals = []
    for v in d.values():
        vals.extend(v)
    # giữ nguyên chuỗi rỗng (không hiện) nhưng loại duplicates
    return sorted({s for s in vals})

def generate_combinations(out_csv: Path):
    # Đếm số lượng âm vị (phonemes)
    num_initials = _count_phonemes(am_dau_map)
    num_medials = _count_phonemes(am_dem_map)
    num_nuclei = _count_phonemes(am_chinh_map)
    num_codas = _count_phonemes(am_cuoi_map)

    # Lấy danh sách các giá trị để tạo tổ hợp
    initials = _flatten_values(am_dau_map)
    medials = _flatten_values(am_dem_map)
    nuclei = _flatten_values(am_chinh_map)
    codas = _flatten_values(am_cuoi_map)
    # tone numbers: default + mapped ones
    tones = sorted({TONE_NUM_DEFAULT} | set(TONE_DIACRITIC_TO_NUM.values()), key=int)
    num_tones = len(tones)

    seen = set()
    rows = []
    for ini in initials:
        for med in medials:
            for nuc in nuclei:
                for coda in codas:
                    base = f"{ini}{med}{nuc}{coda}"
                    # skip empty base (tất cả thành phần rỗng)
                    if base == "":
                        continue
                    for t in tones:
                        token = f"{base}_{t}"
                        if token in seen:
                            continue
                        seen.add(token)
                        rows.append((ini, med, nuc, coda, t, token))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open('w', encoding='utf-8') as fh:
        fh.write("initial,medial,nucleus,coda,tone,syllable\n")
        for ini, med, nuc, coda, t, tok in rows:
            # escape commas if any component contains comma (unlikely here)
            fh.write(f'"{ini}","{med}","{nuc}","{coda}","{t}","{tok}"\n')

    print(f"Wrote {len(rows)} unique combinations to {out_csv}")
    print(f"Number of phonemes: initials={num_initials}, medials={num_medials}, nuclei={num_nuclei}, codas={num_codas}, tones={num_tones}")

    # Also write a plain-text summary with counts
    txt_path = out_csv.parent / 'syllable_counts.txt'
    with txt_path.open('w', encoding='utf-8') as t:
        t.write(f"total_combinations: {len(rows)}\n")
        t.write(f"initials: {num_initials}\n")
        t.write(f"medials: {num_medials}\n")
        t.write(f"nuclei: {num_nuclei}\n")
        t.write(f"codas: {num_codas}\n")
        t.write(f"tones: {num_tones}\n")

    print(f"Wrote summary TXT to {txt_path}")
    return len(rows)

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "syllable_combinations.csv"
    generate_combinations(out)
