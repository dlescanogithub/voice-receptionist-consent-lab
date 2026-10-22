"""Record agent turns from the Conversational AI WebSocket.

The caller script is fixed so the same sentence can be compared at T1, T2, and
T3. Nothing here runs unless the caller has already passed the live-enabled
check. Connect retries are bounded. A turn that has started is not retried.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import random
import wave
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Protocol

from consent_lab.clock import Clock, WallClock
from consent_lab.config import Settings
from consent_lab.errors import ProbeError, SignedUrlError
from consent_lab.logging_setup import log
from consent_lab.retry import retry_delay_s
from consent_lab.signed_url import Opener, fetch_signed_url

_LOGGER = logging.getLogger("consent_lab.probe")
_SAMPLE_WIDTH = 2

CALLER_SCRIPT: tuple[str, ...] = (
    "Hola, quiero un turno con clínica médica",
    "Sí",
    "El viernes a la mañana",
)


class Socket(Protocol):
    async def send(self, data: str) -> None: ...

    async def recv(self) -> str | bytes: ...


class ConnectCM(Protocol):
    async def __aenter__(self) -> Socket: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


class Connector(Protocol):
    def __call__(self, url: str) -> ConnectCM: ...


@dataclass
class SessionState:
    last: float | None = None
    first_audio: float | None = None
    fmt: str | None = None


def default_connector(url: str) -> ConnectCM:
    import websockets

    return websockets.connect(url, max_size=None)


def apply_event(
    event: dict[str, object],
    cur: bytearray,
    texts: list[str],
    state: SessionState,
    clock: Clock,
) -> dict[str, object] | None:
    """Update ``state`` from one server frame. Return a pong to send, if any."""

    kind = event.get("type")
    if kind == "ping":
        ping = event.get("ping_event")
        if not isinstance(ping, dict) or "event_id" not in ping:
            raise ProbeError("ping")
        return {"type": "pong", "event_id": ping["event_id"]}
    if kind == "conversation_initiation_metadata":
        meta = event.get("conversation_initiation_metadata_event")
        if not isinstance(meta, dict):
            raise ProbeError("metadata")
        fmt = meta.get("agent_output_audio_format")
        state.fmt = fmt if isinstance(fmt, str) else None
        return None
    if kind == "audio":
        audio_event = event.get("audio_event")
        if not isinstance(audio_event, dict) or "audio_base_64" not in audio_event:
            raise ProbeError("audio")
        encoded = audio_event["audio_base_64"]
        if not isinstance(encoded, str):
            raise ProbeError("audio")
        try:
            chunk = base64.b64decode(encoded)
        except (ValueError, TypeError) as exc:
            raise ProbeError("audio") from exc
        if not cur:
            state.first_audio = clock.now()
        cur.extend(chunk)
        state.last = clock.now()
        return None
    if kind == "agent_response":
        body = event.get("agent_response_event")
        text = body.get("agent_response") if isinstance(body, dict) else None
        if not isinstance(text, str):
            raise ProbeError("agent_response")
        texts.append(text)
        return None
    return None


def write_wav(path: Path, payload: bytes, sample_rate: int) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(_SAMPLE_WIDTH)
        handle.setframerate(sample_rate)
        handle.writeframes(payload)


def write_meta(path: Path, fmt: str | None, texts: list[str], durs: list[float]) -> None:
    payload = {"fmt": fmt, "texts": texts, "durs": durs}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def _decode_event(raw: str | bytes) -> dict[str, object]:
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProbeError("json") from exc
    if not isinstance(loaded, dict):
        raise ProbeError("json")
    typed: dict[str, object] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise ProbeError("json")
        typed[key] = value
    return typed


async def recv_until_quiet(
    ws: Socket,
    cur: bytearray,
    texts: list[str],
    state: SessionState,
    clock: Clock,
    settings: Settings,
) -> None:
    started = clock.now()
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=settings.poll_timeout_s)
        except TimeoutError:
            clock.advance(settings.poll_timeout_s)
            now = clock.now()
            if cur and state.last is not None and now - state.last > settings.quiet_after_s:
                return
            if now - started > settings.overall_timeout_s:
                return
            continue
        event = _decode_event(raw)
        outgoing = apply_event(event, cur, texts, state, clock)
        if outgoing is not None:
            await ws.send(json.dumps(outgoing))


def _connect_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (TimeoutError, ConnectionError, OSError))


async def connect_bounded(
    connector: Connector,
    url: str,
    settings: Settings,
    clock: Clock,
    rng: random.Random,
) -> tuple[ConnectCM, Socket]:
    attempt = 1
    while True:
        try:
            cm = connector(url)
            socket = await cm.__aenter__()
        except Exception as exc:
            if attempt >= settings.max_attempts or not _connect_retryable(exc):
                raise
            delay = retry_delay_s(
                attempt,
                None,
                base_s=settings.backoff_base_s,
                cap_s=settings.backoff_cap_s,
                rng=rng,
            )
            log(
                _LOGGER,
                logging.WARNING,
                "socket retry",
                event="socket_retry",
                attempt=attempt,
                error_class=type(exc).__name__,
                delay_s=round(delay, 3),
            )
            await clock.sleep(delay)
            attempt += 1
            continue
        return cm, socket


async def run_session(
    ws: Socket,
    *,
    script: Sequence[str],
    out_dir: Path,
    clock: Clock,
    settings: Settings,
) -> list[float]:
    init: dict[str, str] = {"type": "conversation_initiation_client_data"}
    if settings.branch_id:
        init["branch_id"] = settings.branch_id
    await ws.send(json.dumps(init))
    cur = bytearray()
    texts: list[str] = []
    durs: list[float] = []
    state = SessionState()
    silence = base64.b64encode(b"\x00" * settings.silence_bytes).decode("ascii")
    bytes_per_second = settings.sample_rate * _SAMPLE_WIDTH

    async def feed() -> None:
        while True:
            await ws.send(json.dumps({"user_audio_chunk": silence}))
            await clock.sleep(settings.feed_interval_s)

    feeder = asyncio.create_task(feed())
    try:
        for index in range(len(script) + 1):
            await recv_until_quiet(ws, cur, texts, state, clock, settings)
            dur = len(cur) / float(bytes_per_second)
            durs.append(dur)
            payload = bytes(cur)
            write_wav(out_dir / f"T{index + 1}.wav", payload, settings.sample_rate)
            log(
                _LOGGER,
                logging.INFO,
                "turn saved",
                event="turn_saved",
                turn=index + 1,
                nbytes=len(payload),
            )
            cur.clear()
            state.last = None
            if state.first_audio is not None:
                wait = state.first_audio + dur + settings.playback_pad_s - clock.now()
                if wait > 0:
                    await clock.sleep(wait)
            if index < len(script):
                await ws.send(json.dumps({"type": "user_message", "text": script[index]}))
    finally:
        feeder.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await feeder
    write_meta(out_dir / "meta.json", state.fmt, texts, durs)
    return durs


async def run_probe(
    *,
    settings: Settings,
    out_dir: Path,
    opener: Opener | None = None,
    connector: Connector | None = None,
    clock: Clock | None = None,
    rng: random.Random | None = None,
    script: Sequence[str] | None = None,
) -> list[float]:
    """Fetch a signed URL, record one scripted call, and write ``T*.wav`` plus ``meta.json``.

    ``meta.json`` stores the audio format, the agent texts, and durations.
    It does not store a conversation id.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    chosen = clock if clock is not None else WallClock()
    source = rng if rng is not None else random.Random(settings.seed)
    lines = tuple(script) if script is not None else CALLER_SCRIPT
    log(
        _LOGGER,
        logging.INFO,
        "probe start",
        event="probe_start",
        run=out_dir.name,
        turns=len(lines) + 1,
    )

    def sync_sleep(seconds: float) -> None:
        # Signed-URL retries are synchronous. Tests inject ``opener`` and a clock
        # by calling ``fetch_signed_url`` themselves; this path sleeps for real
        # only when the default opener is in use. The async clock cannot be
        # awaited here. A zero delay is a no-op.
        if seconds > 0 and opener is None:
            import time

            time.sleep(seconds)

    try:
        signed = fetch_signed_url(settings, opener=opener, sleep=sync_sleep, rng=source)
    except SignedUrlError:
        log(_LOGGER, logging.ERROR, "signed url failed", event="signed_url_failed")
        raise
    log(_LOGGER, logging.INFO, "signed url fetched", event="signed_url_fetched")
    connect = connector if connector is not None else default_connector
    cm, socket = await connect_bounded(connect, signed, settings, chosen, source)
    try:
        durs = await run_session(
            socket, script=lines, out_dir=out_dir, clock=chosen, settings=settings
        )
    finally:
        await cm.__aexit__(None, None, None)
    log(_LOGGER, logging.INFO, "probe done", event="probe_done", turns=len(durs))
    return durs
