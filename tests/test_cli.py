from __future__ import annotations

import importlib.util
import wave
from pathlib import Path

import pytest

from consent_lab import __version__
from consent_lab.cli import console_main
from consent_lab.secretscan import format_report, scan_path, scan_text


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_about() -> None:
    code, out, err = _run(["about"])
    assert code == 0
    assert err == ""
    assert f"consent_lab {__version__}" in out
    assert "live_enabled=false" in out


def test_bad_log_level() -> None:
    code, _out, err = _run(["about"], env={"LOG_LEVEL": "LOUD"})
    assert code == 2
    assert "LOG_LEVEL" in err


def test_probe_refuses_before_any_credential_use() -> None:
    code, _out, err = _run(["probe"])
    assert code == 2
    assert err.strip() == "refusing: this spends ElevenLabs credits. Set LIVE_ENABLED=1 to run."


def test_probe_requires_key_agent_and_dir() -> None:
    code, _out, err = _run(["probe", "out"], env={"LIVE_ENABLED": "1"})
    assert code == 2
    assert "ELEVENLABS_API_KEY" in err
    code, _out, err = _run(
        ["probe"],
        env={"LIVE_ENABLED": "1", "ELEVENLABS_API_KEY": "k", "ELEVENLABS_AGENT_ID": "a"},
    )
    assert code == 2
    assert "output dir" in err


def test_probe_cli_uses_the_library(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    called: dict[str, object] = {}

    async def fake_run(**kwargs: object) -> list[float]:
        called["name"] = Path(str(kwargs["out_dir"])).name
        return [1.25, 0.5]

    monkeypatch.setattr("consent_lab.probe.run_probe", fake_run)

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network")

    monkeypatch.setattr("urllib.request.urlopen", explode)
    code, out, err = _run(
        ["probe", str(tmp_path / "MYRUN")],
        env={
            "LIVE_ENABLED": "1",
            "ELEVENLABS_API_KEY": "test-key-not-real",
            "ELEVENLABS_AGENT_ID": "agent-test",
        },
    )
    assert code == 0
    assert called["name"] == "MYRUN"
    assert "test-key-not-real" not in out
    assert "test-key-not-real" not in err
    assert "[1.25, 0.5]" in out
    assert not str(out).startswith("/")


def test_measure_cli_on_a_sine(tmp_path: Path) -> None:
    import numpy as np

    run = tmp_path / "TONE"
    run.mkdir()
    (run / "meta.json").write_text('{"texts":["tono de prueba"]}', encoding="utf-8")
    sr = 16000
    samples = int(sr * 0.5)
    time = np.arange(samples) / sr
    pcm = (0.2 * np.sin(2 * np.pi * 210 * time) * 32767).astype(np.int16)
    with wave.open(str(run / "T1.wav"), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(pcm.tobytes())
    dest = tmp_path / "out.csv"
    code, out, err = _run(["measure", "--root", str(tmp_path), "--out", str(dest)])
    assert code == 0, err
    assert dest.is_file()
    assert "TONE" in out
    assert "F0" in out
    assert "210" in out or "209" in out or "211" in out
    assert not out.strip().splitlines()[-1].startswith("/")


def test_measure_cli_skips_a_short_wav(tmp_path: Path) -> None:
    run = tmp_path / "SHORT"
    run.mkdir()
    (run / "meta.json").write_text("{}", encoding="utf-8")
    with wave.open(str(run / "T1.wav"), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x00" * 10)
    code, _out, err = _run(["measure", "--root", str(tmp_path), "--out", str(tmp_path / "m.csv")])
    assert code == 2
    assert "no voiced turns" in err


def test_measure_cli_missing_dir(tmp_path: Path) -> None:
    code, _out, err = _run(["measure", "--root", str(tmp_path / "missing")])
    assert code == 1
    assert "not a directory" in err


def test_secretscan_repo_is_clean() -> None:
    findings = scan_path(_repo())
    assert findings == []
    assert format_report([]) == "secret scan: no findings"


def test_secretscan_reports_rule_without_the_secret(tmp_path: Path) -> None:
    key = "AKIA" + ("A" * 16)
    home = "/" + "home" + "/someone/note"
    workspace = "/" + "workspace" + "/proj"
    private = "-----BEGIN " + "PRIVATE KEY-----"
    token = "sk_" + ("a" * 32)
    slack = "xoxb-" + ("a" * 12)
    assigned = "api_key" + ' = "' + ("b" * 12) + '"'
    text = "\n".join([key, home, workspace, private, token, slack, assigned])
    (tmp_path / "leak.txt").write_text(text, encoding="utf-8")
    (tmp_path / "clip.wav").write_bytes(key.encode("ascii"))
    (tmp_path / "binary.bin").write_bytes(b"\x00" + key.encode("ascii"))
    (tmp_path / "odd.txt").write_bytes(b"\xff\xfe")
    findings = scan_path(tmp_path)
    rules = {item.rule for item in findings}
    assert rules == {
        "aws_access_key_id",
        "home_path",
        "workspace_path",
        "private_key_block",
        "elevenlabs_secret_key",
        "slack_token",
        "assigned_live_secret",
    }
    report = format_report(findings)
    assert key not in report
    assert "leak.txt" in report
    assert "clip.wav" not in report
    code, out, _err = _run(["secretscan", str(tmp_path)])
    assert code == 1
    assert key not in out


def test_scan_text_relative_name() -> None:
    found = scan_text("note.txt", "hello")
    assert found == []


def test_console_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("consent_lab.cli.main", lambda: 4)
    with pytest.raises(SystemExit) as caught:
        console_main()
    assert caught.value.code == 4


def test_shims_import() -> None:
    for name in ("analyze.py", "measure_ab.py", "ws_ab.py"):
        path = _repo() / "tools" / name
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


def test_main_module_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("consent_lab.cli.main", lambda: 0)
    import runpy

    with pytest.raises(SystemExit) as caught:
        runpy.run_module("consent_lab", run_name="__main__")
    assert caught.value.code == 0


def _run(argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str, str]:
    import io
    from contextlib import redirect_stderr, redirect_stdout

    from consent_lab.cli import main as entry

    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = entry(argv, env if env is not None else {})
    return code, out.getvalue(), err.getvalue()
