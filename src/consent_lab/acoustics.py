"""Per-utterance acoustic features (offline, no network).

``feats`` matches the 2026-10-21 measurement script: Praat F0 via
parselmouth, spectral centroid via librosa, and the internal pause profile.
A pitched-up playback of the same text shows up as a higher F0 and centroid.
"""

from __future__ import annotations

from typing import Any, TypedDict

import librosa
import numpy as np
import parselmouth


class FeatureSet(TypedDict):
    dur: float
    f0_med: float
    f0_sd_st: float
    f0_p10: float
    f0_p90: float
    centroid: int
    loud_db: float
    hnr: float
    syl_per_s: float | None
    gaps_gt150: int
    gaps_gt300: int
    max_gap: float


def feats(
    y: np.ndarray[Any, Any],
    sr: int,
    text: str | None = None,
) -> tuple[FeatureSet, np.ndarray[Any, Any]] | None:
    intervals = librosa.effects.split(y, top_db=35, frame_length=512, hop_length=128)
    if len(intervals) == 0:
        return None
    y2 = y[int(intervals[0][0]) : int(intervals[-1][1])]
    dur = len(y2) / sr
    gaps = [
        (int(intervals[i + 1][0]) - int(intervals[i][1])) / sr for i in range(len(intervals) - 1)
    ]
    sound = parselmouth.Sound(y2, sampling_frequency=sr)
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=500)
    frequencies = np.asarray(pitch.selected_array["frequency"], dtype=np.float64)
    voiced = frequencies[frequencies > 0]
    if len(voiced):
        semitones = 12 * np.log2(voiced / 100)
        f0_med = round(float(np.median(voiced)), 1)
        f0_p10 = round(float(np.percentile(voiced, 10)), 1)
        f0_p90 = round(float(np.percentile(voiced, 90)), 1)
    else:
        semitones = np.array([0.0])
        f0_med = 0.0
        f0_p10 = 0.0
        f0_p90 = 0.0
    centroid = librosa.feature.spectral_centroid(y=y2, sr=sr).mean()
    rms = librosa.feature.rms(y=y2)[0]
    loud = 20 * np.log10(float(rms[rms > 1e-4].mean()) + 1e-9)
    mfcc = librosa.feature.mfcc(y=y2, sr=sr, n_mfcc=20)[1:].mean(axis=1)
    # Accented vowels stay in the set so a syllable estimate still counts them.
    vowels = sum(char in "aeiouáéíóú" for char in (text or "").lower())
    harmonicity = sound.to_harmonicity()
    hnr = float(parselmouth.praat.call(harmonicity, "Get mean", 0, 0))
    max_gap = round(max(gaps), 2) if gaps else 0.0
    features: FeatureSet = {
        "dur": round(float(dur), 2),
        "f0_med": float(f0_med),
        "f0_sd_st": round(float(semitones.std()), 2),
        "f0_p10": float(f0_p10),
        "f0_p90": float(f0_p90),
        "centroid": round(float(centroid)),
        "loud_db": round(float(loud), 1),
        "hnr": round(hnr, 1),
        "syl_per_s": round(vowels / dur, 2) if text else None,
        "gaps_gt150": int(sum(gap > 0.15 for gap in gaps)),
        "gaps_gt300": int(sum(gap > 0.3 for gap in gaps)),
        "max_gap": float(max_gap),
    }
    return features, np.asarray(mfcc)


def cos(a: np.ndarray[Any, Any], b: np.ndarray[Any, Any]) -> float:
    return float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
