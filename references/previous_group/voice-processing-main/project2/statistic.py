#!/usr/bin/env python3
from pathlib import Path
import sys
import re
from collections import Counter

# Ensure project root is on sys.path so we can import project1.phonemizeText
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# Also add project1 directory so phonemizeText's local import of mappings works
sys.path.insert(0, str(ROOT / 'project1'))
try:
    # phonemizeText does a local import of `mappings`, so import it from project1 path
    from phonemizeText import phonemize_syllable
except Exception as e:
    raise ImportError(f"Couldn't import phonemize_syllable from project1: {e}")


def extract_headword(line: str):
    """Return the headword (the first column) from a VDic line or None."""
    if not line:
        return None
    # The file uses tabs after the headword; fall back to whitespace if missing
    parts = line.split('\t')
    head = parts[0].strip()
    if head == "":
        toks = line.strip().split()
        head = toks[0] if toks else None
    return head


def split_into_syllables(head: str):
    """Split a headword into syllables by spaces and hyphens.

    Examples:
    - "a dua" -> ["a", "dua"]
    - "a-dốt" -> ["a", "dốt"]
    """
    if not head:
        return []
    output = [s for s in re.split(r'[\s\-]+', head) if s]
    return output

# Added: list of exact headwords to ignore and helper
IGNORED_HEADWORDS = {
    ".", "...", "\"", "'", "-", "?", ":", ";", "!", "?isName?", "?isDigit?"
}
def is_ignored_headword(head: str) -> bool:
    """Return True for headwords that should be skipped for counting."""
    if not head:
        return True
    h = head.strip().lower()
    if h in IGNORED_HEADWORDS:
        return True
    return False

# ...existing code...
def count_phoneme_counts(vdic_path: Path):
    """Return Counter mapping phoneme -> occurrences across the VDic file."""
    counts = Counter()
    with vdic_path.open('r', encoding='utf-8') as fh:
        for ln in fh:
            if not ln.strip():
                continue
            head = extract_headword(ln)
            if not head:
                continue
            head = head.lower()
            if is_ignored_headword(head):
                continue
            syllables = split_into_syllables(head)
            for s in syllables:
                s = s.strip()
                if not s:
                    continue
                phon = phonemize_syllable(s)
                if phon:
                    counts[phon] += 1
    return counts


def main():
    vd = Path(__file__).resolve().parent / 'VDic_uni.txt'
    if not vd.exists():
        print(f"VDic_uni.txt not found at {vd}")
        return 1
    counts = count_phoneme_counts(vd)
    unique_count = len(counts)
    total_tokens = sum(counts.values())
    duplicates = {p: c for p, c in counts.items() if c > 1}

    report_path = Path(__file__).resolve().parent / 'syllable_report.txt'
    with report_path.open('w', encoding='utf-8') as out:
        out.write(f"Total unique phonemes: {unique_count}\n")
        out.write(f"Total syllable tokens: {total_tokens}\n")
        out.write(f"Duplicate phonemes (count>1): {len(duplicates)}\n\n")

        out.write("Duplicates (count \\t phoneme):\n")
        for p, c in sorted(duplicates.items(), key=lambda x: -x[1]):
            out.write(f"{c}\t{p}\n")

        out.write("\nAll unique phonemes (sorted):\n")
        for p in sorted(counts.keys()):
            out.write(f"{p}\n")

    # Print counts to console (most frequent first)
    print(f"Wrote report to {report_path}")
    print("\nTop syllable counts (count \t syllable):")
    for phon, cnt in sorted(counts.items(), key=lambda x: -x[1])[:200]:
        print(f"{cnt}\t{phon}")

    # Optional: export full counts CSV
    csv_path = Path(__file__).resolve().parent / 'syllable_counts.csv'
    with csv_path.open('w', encoding='utf-8') as csvf:
        csvf.write("phoneme,count\n")
        for phon, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            csvf.write(f"{phon},{cnt}\n")

    print(f"Wrote CSV to {csv_path}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
