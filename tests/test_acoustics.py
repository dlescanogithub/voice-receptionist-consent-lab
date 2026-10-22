from __future__ import annotations

import numpy as np
import pytest

from consent_lab.acoustics import cos, feats


def _sine(
    freq: float, seconds: float = 0.6, sr: int = 16000
) -> np.ndarray[tuple[int], np.dtype[np.float64]]:
    samples = int(sr * seconds)
    time = np.arange(samples) / sr
    return (0.2 * np.sin(2 * np.pi * freq * time)).astype(np.float64)


def test_sine_f0_is_near_the_tone() -> None:
    features, mfcc = feats(_sine(200), 16000)
    assert features is not None
    assert abs(features["f0_med"] - 200) < 5
    assert features["centroid"] > 0
    assert features["dur"] > 0
    assert features["syl_per_s"] is None
    assert features["f0_p10"] <= features["f0_med"] <= features["f0_p90"]
    assert mfcc.shape[0] == 19


def test_text_counts_vowels() -> None:
    features, _mfcc = feats(_sine(180), 16000, text="hola")
    assert features is not None
    assert features["syl_per_s"] is not None
    assert features["syl_per_s"] > 0


def test_digital_silence_uses_the_unvoiced_branch() -> None:
    # The 2026 script returns features with F0 0 when Praat finds no voiced
    # frames. librosa.effects.split still marks a stretch of digital silence
    # as one interval, so this is not the empty-interval path.
    features, _mfcc = feats(np.zeros(16000), 16000)
    assert features is not None
    assert features["f0_med"] == 0.0
    assert features["f0_p10"] == 0.0
    assert features["f0_p90"] == 0.0
    assert features["gaps_gt150"] == 0


def test_no_intervals_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "consent_lab.acoustics.librosa.effects.split",
        lambda *_args, **_kwargs: np.zeros((0, 2), dtype=int),
    )
    assert feats(np.zeros(16000), 16000) is None


def test_gap_between_bursts() -> None:
    sr = 16000
    tone = _sine(190, seconds=0.3, sr=sr)
    gap = np.zeros(int(sr * 0.25))
    audio = np.concatenate([tone, gap, tone])
    features, _mfcc = feats(audio, sr)
    assert features is not None
    assert features["gaps_gt150"] >= 1
    assert features["max_gap"] >= 0.15


def test_cosine_of_identical_and_orthogonal_vectors() -> None:
    same = np.array([1.0, 2.0, 3.0])
    assert cos(same, same) == pytest.approx(1.0)
    assert abs(cos(np.array([1.0, 0.0]), np.array([0.0, 1.0]))) < 1e-9
