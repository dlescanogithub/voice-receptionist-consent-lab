"""Measure F0 (median, Hz) and spectral centroid (Hz) for every agent turn in evidence/ab/.

Offline, no network, no API key. Usage:
    python tools/measure_ab.py            # prints a table and writes evidence/ab/measurements.csv
"""
import csv, glob, json, os, sys

import librosa

sys.path.insert(0, os.path.dirname(__file__))
from analyze import feats  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "evidence", "ab")


def main() -> None:
    rows = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab)
        if not os.path.isdir(d):
            continue
        meta = json.load(open(os.path.join(d, "meta.json")))
        texts = meta.get("texts", [])
        for wav in sorted(glob.glob(os.path.join(d, "T*.wav"))):
            k = int(os.path.basename(wav)[1:-4])
            y, sr = librosa.load(wav, sr=16000)
            if len(y) < 1600:
                continue
            r, _ = feats(y, sr)
            rows.append(dict(run=lab, turn=f"T{k}", text=texts[k - 1] if k <= len(texts) else "",
                             f0_median_hz=r["f0_med"], centroid_hz=r["centroid"], dur_s=r["dur"],
                             loud_dbfs=r["loud_db"], max_gap_s=r["max_gap"]))
    out = os.path.join(ROOT, "measurements.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['run']:8} {r['turn']}  F0 {r['f0_median_hz']:6.1f} Hz  centroid {r['centroid_hz']:5d} Hz  {r['dur_s']:5.2f} s  {r['text'][:60]}")
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
