"""Per-utterance acoustic features used in this lab (offline, no network).

feats(y, sr) returns duration, median F0 (Praat via parselmouth), F0 spread in
semitones, spectral centroid, loudness, HNR and the internal pause profile.
A pitched-up or sped-up playback shows as higher F0 and centroid on the same text.
"""
import numpy as np
import librosa
import parselmouth


def feats(y, sr, text=None):
    iv = librosa.effects.split(y, top_db=35, frame_length=512, hop_length=128)
    if len(iv) == 0:
        return None
    y2 = y[iv[0][0]:iv[-1][1]]
    dur = len(y2) / sr
    gaps = [(iv[i + 1][0] - iv[i][1]) / sr for i in range(len(iv) - 1)]
    snd = parselmouth.Sound(y2, sr)
    p = snd.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=500).selected_array["frequency"]
    p = p[p > 0]
    st = 12 * np.log2(p / 100) if len(p) else np.array([0])
    cen = librosa.feature.spectral_centroid(y=y2, sr=sr).mean()
    rms = librosa.feature.rms(y=y2)[0]
    loud = 20 * np.log10(rms[rms > 1e-4].mean() + 1e-9)
    mf = librosa.feature.mfcc(y=y2, sr=sr, n_mfcc=20)[1:].mean(axis=1)
    vowels = sum(c in "aeiouáéíóú" for c in (text or "").lower())
    hnr = parselmouth.praat.call(snd.to_harmonicity(), "Get mean", 0, 0)
    return dict(
        dur=round(dur, 2),
        f0_med=round(float(np.median(p)), 1) if len(p) else 0,
        f0_sd_st=round(float(st.std()), 2),
        f0_p10=round(float(np.percentile(p, 10)), 1) if len(p) else 0,
        f0_p90=round(float(np.percentile(p, 90)), 1) if len(p) else 0,
        centroid=round(float(cen)),
        loud_db=round(float(loud), 1),
        hnr=round(float(hnr), 1),
        syl_per_s=round(vowels / dur, 2) if text else None,
        gaps_gt150=sum(g > 0.15 for g in gaps),
        gaps_gt300=sum(g > 0.3 for g in gaps),
        max_gap=round(max(gaps), 2) if gaps else 0,
    ), mf


def cos(a, b):
    return float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
