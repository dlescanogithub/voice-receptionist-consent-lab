from __future__ import annotations

import csv
import wave
from pathlib import Path

import numpy as np
import pytest

from consent_lab.acoustics import FeatureSet
from consent_lab.errors import MeasurementError
from consent_lab.measure import (
    TurnMeasurement,
    default_loader,
    display_path,
    format_line,
    load_feats,
    measure_tree,
    turn_index,
    write_csv,
)


def _features() -> FeatureSet:
    return {
        "dur": 1.25,
        "f0_med": 200.0,
        "f0_sd_st": 0.1,
        "f0_p10": 190.0,
        "f0_p90": 210.0,
        "centroid": 1800,
        "loud_db": -20.0,
        "hnr": 10.0,
        "syl_per_s": None,
        "gaps_gt150": 0,
        "gaps_gt300": 0,
        "max_gap": 0.0,
    }


def _touch(path: Path, samples: int = 3200) -> None:
    path.write_bytes(b"\x00\x01" * samples)


def test_turn_index_and_bad_name(tmp_path: Path) -> None:
    assert turn_index(tmp_path / "T12.wav") == 12
    with pytest.raises(MeasurementError, match="bad turn name"):
        turn_index(tmp_path / "T.wav")


def test_display_path_hides_outside_absolute(tmp_path: Path) -> None:
    assert display_path(Path("evidence/ab/measurements.csv")) == "evidence/ab/measurements.csv"
    shown = display_path(tmp_path / "measurements.csv")
    assert not shown.startswith("/")
    assert shown.endswith("measurements.csv")


def test_format_line_matches_the_old_script() -> None:
    row = TurnMeasurement("CALM", "T1", "Hola", 197.0, 1780, 3.86, -20.7, 0.34)
    assert format_line(row) == "CALM     T1  F0  197.0 Hz  centroid  1780 Hz   3.86 s  Hola"


def test_measure_tree_with_fakes(tmp_path: Path) -> None:
    run_b = tmp_path / "B"
    run_a = tmp_path / "A"
    run_b.mkdir()
    run_a.mkdir()
    (run_a / "meta.json").write_text(
        '{"texts":["alpha","beta"],"conv":"SHOULD-NOT-LEAK"}',
        encoding="utf-8",
    )
    (run_b / "meta.json").write_text('{"texts":["bee"]}', encoding="utf-8")
    _touch(run_a / "T1.wav")
    _touch(run_a / "T2.wav", samples=10)
    _touch(run_b / "T1.wav")
    (run_a / "note.txt").write_text("ignore", encoding="utf-8")

    def loader(
        path: Path, sample_rate: int
    ) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int]:
        del sample_rate
        if path.name == "T2.wav":
            return np.zeros(10), 16000
        if path.parent.name == "B":
            return np.zeros(2000), 16000
        return np.ones(2000), 16000

    def feats(
        y: np.ndarray[tuple[int], np.dtype[np.float64]],
        sr: int,
        text: str | None = None,
    ) -> tuple[FeatureSet, np.ndarray[tuple[int], np.dtype[np.float64]]] | None:
        del sr, text
        if float(y[0]) == 0.0:
            return None
        return _features(), np.zeros(3)

    rows = measure_tree(tmp_path, loader=loader, feats_fn=feats)
    assert [row.run for row in rows] == ["A"]
    assert rows[0].turn == "T1"
    assert rows[0].text == "alpha"
    dest = tmp_path / "measurements.csv"
    write_csv(rows, dest)
    text = dest.read_text(encoding="utf-8")
    assert "SHOULD-NOT-LEAK" not in text
    parsed = list(csv.DictReader(text.splitlines()))
    assert parsed[0]["f0_median_hz"] == "200.0"
    assert parsed[0]["centroid_hz"] == "1800"


def test_missing_text_is_blank(tmp_path: Path) -> None:
    run = tmp_path / "RUN"
    run.mkdir()
    (run / "meta.json").write_text('{"texts":[]}', encoding="utf-8")
    _touch(run / "T3.wav")

    def loader(
        path: Path, sample_rate: int
    ) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int]:
        del path, sample_rate
        return np.ones(2000), 16000

    def feats(
        y: np.ndarray[tuple[int], np.dtype[np.float64]],
        sr: int,
        text: str | None = None,
    ) -> tuple[FeatureSet, np.ndarray[tuple[int], np.dtype[np.float64]]] | None:
        del y, sr, text
        return _features(), np.zeros(3)

    rows = measure_tree(tmp_path, loader=loader, feats_fn=feats)
    assert rows[0].text == ""
    assert rows[0].turn == "T3"


def test_only_filters_runs(tmp_path: Path) -> None:
    for name in ("KEEP", "DROP"):
        run = tmp_path / name
        run.mkdir()
        (run / "meta.json").write_text('{"texts":["x"]}', encoding="utf-8")
        _touch(run / "T1.wav")

    def loader(
        path: Path, sample_rate: int
    ) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int]:
        del path, sample_rate
        return np.ones(2000), 16000

    def feats(
        y: np.ndarray[tuple[int], np.dtype[np.float64]],
        sr: int,
        text: str | None = None,
    ) -> tuple[FeatureSet, np.ndarray[tuple[int], np.dtype[np.float64]]] | None:
        del y, sr, text
        return _features(), np.zeros(3)

    rows = measure_tree(tmp_path, only=["KEEP"], loader=loader, feats_fn=feats)
    assert [row.run for row in rows] == ["KEEP"]


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (None, "not a directory"),
        ("bad-meta", "bad meta.json"),
        ("no-meta", "missing meta.json"),
    ],
)
def test_measure_errors(tmp_path: Path, payload: str | None, match: str) -> None:
    if payload is None:
        with pytest.raises(MeasurementError, match=match):
            measure_tree(tmp_path / "missing")
        return
    run = tmp_path / "RUN"
    run.mkdir()
    if payload == "bad-meta":
        (run / "meta.json").write_text("{", encoding="utf-8")
    with pytest.raises(MeasurementError, match=match):
        measure_tree(tmp_path)


def test_non_dict_meta_is_empty_text(tmp_path: Path) -> None:
    run = tmp_path / "RUN"
    run.mkdir()
    (run / "meta.json").write_text("[1, 2]", encoding="utf-8")
    _touch(run / "T1.wav")

    def loader(
        path: Path, sample_rate: int
    ) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int]:
        del path, sample_rate
        return np.ones(2000), 16000

    def feats(
        y: np.ndarray[tuple[int], np.dtype[np.float64]],
        sr: int,
        text: str | None = None,
    ) -> tuple[FeatureSet, np.ndarray[tuple[int], np.dtype[np.float64]]] | None:
        del y, sr, text
        return _features(), np.zeros(3)

    rows = measure_tree(tmp_path, loader=loader, feats_fn=feats)
    assert rows[0].text == ""


def test_bad_turn_name_raises(tmp_path: Path) -> None:
    run = tmp_path / "RUN"
    run.mkdir()
    (run / "meta.json").write_text("{}", encoding="utf-8")
    (run / "Tx.wav").write_bytes(b"\x00\x00")
    with pytest.raises(MeasurementError, match="bad turn name"):
        measure_tree(
            tmp_path, loader=lambda _p, _s: (np.ones(10), 16000), feats_fn=lambda _y, _sr: None
        )


def test_load_feats_and_missing_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    assert callable(load_feats())

    def boom(name: str, package: str | None = None) -> object:
        del package
        if name == "consent_lab.acoustics":
            raise ImportError(name)
        raise AssertionError(name)

    monkeypatch.setattr("consent_lab.measure.importlib.import_module", boom)
    with pytest.raises(MeasurementError, match="audio extra"):
        load_feats()


def test_default_loader_reads_wav_and_reports_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "tone.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x10" * 1600)
    audio, sr = default_loader(path, 16000)
    assert sr == 16000
    assert len(audio) == 1600

    def boom(name: str, package: str | None = None) -> object:
        del package
        if name == "librosa":
            raise ImportError(name)
        raise AssertionError(name)

    monkeypatch.setattr("consent_lab.measure.importlib.import_module", boom)
    with pytest.raises(MeasurementError, match="audio extra"):
        default_loader(path, 16000)


def test_committed_table_and_calm_recompute() -> None:
    repo = Path(__file__).resolve().parents[1]
    table = repo / "evidence" / "ab" / "measurements.csv"
    rows = list(csv.DictReader(table.open(encoding="utf-8")))
    v0 = next(row for row in rows if row["run"] == "V0" and row["turn"] == "T1")
    assert v0["f0_median_hz"] == "211.4"
    assert v0["centroid_hz"] == "1957"
    expected = [row for row in rows if row["run"] == "CALM"]
    got = measure_tree(repo / "evidence" / "ab", only=["CALM"])
    assert len(got) == len(expected) == 3
    for exp, row in zip(expected, got, strict=True):
        assert row.turn == exp["turn"]
        assert row.text == exp["text"]
        assert abs(row.f0_median_hz - float(exp["f0_median_hz"])) <= 0.6
        assert abs(row.centroid_hz - int(exp["centroid_hz"])) <= 5


def test_texts_ignore_non_strings(tmp_path: Path) -> None:
    run = tmp_path / "RUN"
    run.mkdir()
    (run / "meta.json").write_text('{"texts":["ok", 5, null]}', encoding="utf-8")
    _touch(run / "T1.wav")

    def loader(
        path: Path, sample_rate: int
    ) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int]:
        del path, sample_rate
        return np.ones(2000), 16000

    def feats(
        y: np.ndarray[tuple[int], np.dtype[np.float64]],
        sr: int,
        text: str | None = None,
    ) -> tuple[FeatureSet, np.ndarray[tuple[int], np.dtype[np.float64]]] | None:
        del y, sr, text
        return _features(), np.zeros(3)

    rows = measure_tree(tmp_path, loader=loader, feats_fn=feats)
    assert rows[0].text == "ok"
