"""Recompute F0 and spectral centroid for ``evidence/ab`` style directories.

Offline. No network and no API key. The CSV columns match the 2026-10-21
``measurements.csv``: run, turn, text, f0_median_hz, centroid_hz, dur_s,
loud_dbfs, max_gap_s. Turns shorter than ``min_samples`` are skipped. A turn
with no voiced interval is skipped and logged, instead of aborting the table.
"""

from __future__ import annotations

import csv
import importlib
import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

import numpy as np

from consent_lab.errors import MeasurementError
from consent_lab.logging_setup import log

if TYPE_CHECKING:
    from consent_lab.acoustics import FeatureSet

_LOGGER = logging.getLogger("consent_lab.measure")

FIELDNAMES: tuple[str, ...] = (
    "run",
    "turn",
    "text",
    "f0_median_hz",
    "centroid_hz",
    "dur_s",
    "loud_dbfs",
    "max_gap_s",
)


class FeatsFn(Protocol):
    def __call__(
        self,
        y: np.ndarray[Any, Any],
        sr: int,
        text: str | None = None,
    ) -> tuple[FeatureSet, np.ndarray[Any, Any]] | None: ...


Loader = Callable[[Path, int], tuple[np.ndarray[Any, Any], int]]


@dataclass(frozen=True)
class TurnMeasurement:
    run: str
    turn: str
    text: str
    f0_median_hz: float
    centroid_hz: int
    dur_s: float
    loud_dbfs: float
    max_gap_s: float

    def as_row(self) -> dict[str, object]:
        return {
            "run": self.run,
            "turn": self.turn,
            "text": self.text,
            "f0_median_hz": self.f0_median_hz,
            "centroid_hz": self.centroid_hz,
            "dur_s": self.dur_s,
            "loud_dbfs": self.loud_dbfs,
            "max_gap_s": self.max_gap_s,
        }


def turn_index(path: Path) -> int:
    stem = path.stem
    if not stem.startswith("T") or not stem[1:].isdigit():
        raise MeasurementError(f"bad turn name: {path.name}")
    return int(stem[1:])


def display_path(path: Path) -> str:
    """A path safe to print. Absolute paths are reduced to the file name."""

    if path.is_absolute():
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return path.name
    return path.as_posix()


def format_line(row: TurnMeasurement) -> str:
    return (
        f"{row.run:8} {row.turn}  F0 {row.f0_median_hz:6.1f} Hz  "
        f"centroid {row.centroid_hz:5d} Hz  {row.dur_s:5.2f} s  {row.text[:60]}"
    )


def load_feats() -> FeatsFn:
    try:
        module = importlib.import_module("consent_lab.acoustics")
    except ImportError as exc:
        raise MeasurementError("audio extra is not installed") from exc
    feats = module.feats
    return cast(FeatsFn, feats)


def default_loader(path: Path, sample_rate: int) -> tuple[np.ndarray[Any, Any], int]:
    try:
        librosa = importlib.import_module("librosa")
    except ImportError as exc:
        raise MeasurementError("audio extra is not installed") from exc
    audio, sr = librosa.load(path, sr=sample_rate)
    return np.asarray(audio), int(sr)


def _texts(meta: object) -> list[str]:
    if not isinstance(meta, dict):
        return []
    raw = meta.get("texts", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def measure_tree(
    root: Path,
    *,
    sample_rate: int = 16000,
    min_samples: int = 1600,
    only: Sequence[str] | None = None,
    loader: Loader | None = None,
    feats_fn: FeatsFn | None = None,
) -> list[TurnMeasurement]:
    if not root.is_dir():
        raise MeasurementError(f"not a directory: {root.name}")
    load = loader if loader is not None else default_loader
    feats = feats_fn if feats_fn is not None else load_feats()
    wanted = set(only) if only is not None else None
    rows: list[TurnMeasurement] = []
    labs = sorted(path for path in root.iterdir() if path.is_dir())
    for lab in labs:
        if wanted is not None and lab.name not in wanted:
            continue
        meta_path = lab / "meta.json"
        if not meta_path.is_file():
            raise MeasurementError(f"missing meta.json in {lab.name}")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MeasurementError(f"bad meta.json in {lab.name}") from exc
        texts = _texts(meta)
        for wav in sorted(lab.glob("T*.wav")):
            index = turn_index(wav)
            audio, sr = load(wav, sample_rate)
            if len(audio) < min_samples:
                log(
                    _LOGGER,
                    logging.INFO,
                    "skip turn",
                    event="turn_skipped",
                    run=lab.name,
                    turn=wav.name,
                    reason="short",
                )
                continue
            found = feats(audio, sr)
            if found is None:
                log(
                    _LOGGER,
                    logging.INFO,
                    "skip turn",
                    event="turn_skipped",
                    run=lab.name,
                    turn=wav.name,
                    reason="unvoiced",
                )
                continue
            features, _mfcc = found
            text = texts[index - 1] if 0 < index <= len(texts) else ""
            rows.append(
                TurnMeasurement(
                    run=lab.name,
                    turn=f"T{index}",
                    text=text,
                    f0_median_hz=float(features["f0_med"]),
                    centroid_hz=int(features["centroid"]),
                    dur_s=float(features["dur"]),
                    loud_dbfs=float(features["loud_db"]),
                    max_gap_s=float(features["max_gap"]),
                )
            )
    return rows


def write_csv(rows: Sequence[TurnMeasurement], dest: Path) -> None:
    with dest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDNAMES))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_row())
