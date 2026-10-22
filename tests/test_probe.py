from __future__ import annotations

import asyncio
import base64
import json
import wave
from pathlib import Path

import pytest

from consent_lab.clock import WallClock
from consent_lab.config import Settings
from consent_lab.errors import ProbeError
from consent_lab.probe import (
    CALLER_SCRIPT,
    SessionState,
    apply_event,
    connect_bounded,
    default_connector,
    run_probe,
    run_session,
)


class ManualClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds
        await asyncio.sleep(0)


class FakeSocket:
    def __init__(self, frames: list[object]) -> None:
        self.frames = list(frames)
        self.sent: list[object] = []

    async def send(self, data: str) -> None:
        self.sent.append(json.loads(data))

    async def recv(self) -> str:
        await asyncio.sleep(0)
        if not self.frames:
            raise TimeoutError
        item = self.frames.pop(0)
        if item is None:
            raise TimeoutError
        if isinstance(item, str):
            return item
        return json.dumps(item)


class FakeCM:
    def __init__(self, socket: FakeSocket, fails: int = 0) -> None:
        self.socket = socket
        self.fails = fails
        self.exited = 0
        self.entered = 0

    async def __aenter__(self) -> FakeSocket:
        self.entered += 1
        if self.fails:
            self.fails -= 1
            raise ConnectionError("reset")
        return self.socket

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        del exc_type, exc, tb
        self.exited += 1
        return False


def _settings(**extra: str) -> Settings:
    env = {
        "LIVE_ENABLED": "1",
        "ELEVENLABS_API_KEY": "test-key-not-real",
        "ELEVENLABS_AGENT_ID": "agent-test",
        "CONSENT_LAB_POLL_TIMEOUT_S": "0.05",
        "CONSENT_LAB_QUIET_AFTER_S": "0",
        "CONSENT_LAB_OVERALL_TIMEOUT_S": "2",
        "CONSENT_LAB_PLAYBACK_PAD_S": "5",
        "CONSENT_LAB_FEED_INTERVAL_S": "0",
        "CONSENT_LAB_MAX_ATTEMPTS": "3",
    }
    env.update(extra)
    return Settings.from_env(env)


def _audio(payload: bytes = b"\x01\x02" * 80) -> dict[str, object]:
    return {
        "type": "audio",
        "audio_event": {"audio_base_64": base64.b64encode(payload).decode("ascii")},
    }


def test_caller_script_is_the_fixed_three_lines() -> None:
    assert CALLER_SCRIPT == (
        "Hola, quiero un turno con clínica médica",
        "Sí",
        "El viernes a la mañana",
    )


def test_apply_event_branches() -> None:
    clock = ManualClock()
    state = SessionState()
    cur = bytearray()
    texts: list[str] = []
    pong = apply_event({"type": "ping", "ping_event": {"event_id": 7}}, cur, texts, state, clock)
    assert pong == {"type": "pong", "event_id": 7}
    apply_event(
        {
            "type": "conversation_initiation_metadata",
            "conversation_initiation_metadata_event": {"agent_output_audio_format": "pcm_16000"},
        },
        cur,
        texts,
        state,
        clock,
    )
    assert state.fmt == "pcm_16000"
    assert (
        apply_event(
            {"type": "audio", "audio_event": {"audio_base_64": base64.b64encode(b"ab").decode()}},
            cur,
            texts,
            state,
            clock,
        )
        is None
    )
    first = state.first_audio
    apply_event(
        {"type": "audio", "audio_event": {"audio_base_64": base64.b64encode(b"cd").decode()}},
        cur,
        texts,
        state,
        clock,
    )
    assert state.first_audio == first
    assert (
        apply_event(
            {"type": "agent_response", "agent_response_event": {"agent_response": "hola"}},
            cur,
            texts,
            state,
            clock,
        )
        is None
    )
    assert texts == ["hola"]
    assert apply_event({"type": "ignored"}, cur, texts, state, clock) is None
    with pytest.raises(ProbeError, match="ping"):
        apply_event({"type": "ping"}, cur, texts, state, clock)
    with pytest.raises(ProbeError, match="metadata"):
        apply_event({"type": "conversation_initiation_metadata"}, cur, texts, state, clock)
    with pytest.raises(ProbeError, match="audio"):
        apply_event(
            {"type": "audio", "audio_event": {"audio_base_64": 5}}, cur, texts, state, clock
        )
    with pytest.raises(ProbeError, match="audio"):
        apply_event({"type": "audio"}, cur, texts, state, clock)
    with pytest.raises(ProbeError, match="agent_response"):
        apply_event(
            {"type": "agent_response", "agent_response_event": {}}, cur, texts, state, clock
        )


def test_metadata_without_format_string() -> None:
    state = SessionState()
    apply_event(
        {
            "type": "conversation_initiation_metadata",
            "conversation_initiation_metadata_event": {"agent_output_audio_format": 1},
        },
        bytearray(),
        [],
        state,
        ManualClock(),
    )
    assert state.fmt is None


def test_session_writes_wavs_and_meta_without_a_conversation_id(tmp_path: Path) -> None:
    frames: list[object] = [
        {"type": "ping", "ping_event": {"event_id": 3}},
        {
            "type": "conversation_initiation_metadata",
            "conversation_initiation_metadata_event": {"agent_output_audio_format": "pcm_16000"},
        },
        _audio(),
        {"type": "agent_response", "agent_response_event": {"agent_response": "uno"}},
        None,
        _audio(b"\x03\x04" * 40),
        {"type": "agent_response", "agent_response_event": {"agent_response": "dos"}},
        {"type": "something-else"},
        None,
    ]
    socket = FakeSocket(frames)
    clock = ManualClock()
    settings = _settings(ELEVENLABS_BRANCH_ID="branch-9")
    durs = asyncio.run(
        run_session(socket, script=("sí",), out_dir=tmp_path, clock=clock, settings=settings)
    )
    assert len(durs) == 2
    sent = [item for item in socket.sent if isinstance(item, dict)]
    assert sent[0]["type"] == "conversation_initiation_client_data"
    assert sent[0]["branch_id"] == "branch-9"
    assert {"type": "pong", "event_id": 3} in sent
    user_lines = [item["text"] for item in sent if item.get("type") == "user_message"]
    assert user_lines == ["sí"]
    assert any(item.get("user_audio_chunk") for item in sent)
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert set(meta) == {"fmt", "texts", "durs"}
    assert meta["texts"] == ["uno", "dos"]
    assert meta["fmt"] == "pcm_16000"
    with wave.open(str(tmp_path / "T1.wav")) as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == 16000
        assert handle.getnframes() == 80
    assert any(item >= 1 for item in clock.sleeps)


def test_session_without_branch_and_without_audio(tmp_path: Path) -> None:
    socket = FakeSocket([None])
    clock = ManualClock()
    settings = _settings(CONSENT_LAB_PLAYBACK_PAD_S="0", CONSENT_LAB_OVERALL_TIMEOUT_S="0.05")
    durs = asyncio.run(
        run_session(socket, script=(), out_dir=tmp_path, clock=clock, settings=settings)
    )
    assert durs == [0.0]
    sent = [item for item in socket.sent if isinstance(item, dict)]
    assert sent[0] == {"type": "conversation_initiation_client_data"}
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta["texts"] == []
    assert (tmp_path / "T1.wav").is_file()


def test_bad_json_frame(tmp_path: Path) -> None:
    socket = FakeSocket(["{"])
    with pytest.raises(ProbeError, match="json"):
        asyncio.run(
            run_session(
                socket,
                script=(),
                out_dir=tmp_path,
                clock=ManualClock(),
                settings=_settings(),
            )
        )


def test_non_object_json(tmp_path: Path) -> None:
    socket = FakeSocket(["[]"])
    with pytest.raises(ProbeError, match="json"):
        asyncio.run(
            run_session(
                socket, script=(), out_dir=tmp_path, clock=ManualClock(), settings=_settings()
            )
        )


def test_connect_retries_then_closes(tmp_path: Path) -> None:
    del tmp_path
    socket = FakeSocket([None])
    first = FakeCM(socket, fails=1)
    second = FakeCM(socket, fails=0)
    created = [first, second]

    def connector(url: str) -> FakeCM:
        assert url == "wss://example.test/socket"
        return created.pop(0)

    clock = ManualClock()
    settings = _settings()
    cm, opened = asyncio.run(
        connect_bounded(
            connector, "wss://example.test/socket", settings, clock, __import__("random").Random(0)
        )
    )
    assert opened is socket
    assert first.entered == 1
    assert second.entered == 1
    assert clock.sleeps
    asyncio.run(cm.__aexit__(None, None, None))
    assert second.exited == 1


def test_connect_does_not_retry_runtime_error() -> None:
    def connector(url: str) -> FakeCM:
        del url
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        asyncio.run(
            connect_bounded(
                connector,
                "wss://example.test/socket",
                _settings(),
                ManualClock(),
                __import__("random").Random(0),
            )
        )


def test_run_probe_uses_opener_and_does_not_log_secrets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from consent_lab.logging_setup import configure

    configure("INFO")
    socket = FakeSocket(
        [
            _audio(b"\x01\x00" * 20),
            {"type": "agent_response", "agent_response_event": {"agent_response": "ok"}},
            None,
        ]
    )
    cm = FakeCM(socket)

    def connector(url: str) -> FakeCM:
        assert url == "wss://example.test/socket"
        return cm

    def opener(request: object) -> object:
        header = request.get_header("Xi-api-key")  # type: ignore[attr-defined]
        assert header == "test-key-not-real"
        return _Body(b'{"signed_url":"wss://example.test/socket"}')

    durs = asyncio.run(
        run_probe(
            settings=_settings(CONSENT_LAB_PLAYBACK_PAD_S="0"),
            out_dir=tmp_path / "MYRUN",
            opener=opener,  # type: ignore[arg-type]
            connector=connector,
            clock=ManualClock(),
            script=("hola",),
        )
    )
    assert len(durs) == 2
    assert cm.exited == 1
    err = capsys.readouterr().err
    assert "test-key-not-real" not in err
    assert "wss://example.test/socket" not in err
    assert "probe_done" in err


class _Body:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _Body:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_default_connector_does_not_open_a_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()

    def fake_connect(url: str, max_size: object = None) -> object:
        assert url == "wss://example.test/socket"
        assert max_size is None
        return sentinel

    monkeypatch.setattr("websockets.connect", fake_connect)
    assert default_connector("wss://example.test/socket") is sentinel


def test_wall_clock_sleep_zero() -> None:
    clock = WallClock()
    before = clock.now()
    clock.advance(5)
    assert clock.now() >= before
    asyncio.run(clock.sleep(0.01))


def test_run_probe_default_opener_sleeps_on_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import urllib.error
    import urllib.request

    calls = {"n": 0}

    def fake_urlopen(request: urllib.request.Request) -> _Body:
        del request
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.URLError("down")
        return _Body(b'{"signed_url":"wss://example.test/socket"}')

    slept: list[float] = []
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", slept.append)
    socket = FakeSocket([None])
    cm = FakeCM(socket)

    def connector(url: str) -> FakeCM:
        assert url == "wss://example.test/socket"
        return cm

    settings = _settings(CONSENT_LAB_OVERALL_TIMEOUT_S="0.05", CONSENT_LAB_PLAYBACK_PAD_S="0")
    durs = asyncio.run(
        run_probe(
            settings=settings,
            out_dir=tmp_path / "R",
            connector=connector,
            clock=ManualClock(),
            script=(),
        )
    )
    assert durs == [0.0]
    assert slept
    assert cm.exited == 1
