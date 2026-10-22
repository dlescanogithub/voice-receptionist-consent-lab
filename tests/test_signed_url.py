from __future__ import annotations

import random
import urllib.error
import urllib.request
from io import BytesIO

import pytest

from consent_lab.config import Settings
from consent_lab.errors import SignedUrlError
from consent_lab.signed_url import build_signed_url_request, fetch_signed_url, parse_retry_after


class _Resp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _settings(**overrides: str) -> Settings:
    env = {
        "LIVE_ENABLED": "1",
        "ELEVENLABS_API_KEY": "test-key-not-real",
        "ELEVENLABS_AGENT_ID": "agent-test",
        "CONSENT_LAB_MAX_ATTEMPTS": "3",
    }
    env.update(overrides)
    return Settings.from_env(env)


def test_request_query_and_header() -> None:
    settings = _settings(ELEVENLABS_BRANCH_ID="branch-1")
    request = build_signed_url_request(settings)
    assert request.full_url.startswith("https://")
    assert "agent_id=agent-test" in request.full_url
    assert "branch_id=branch-1" in request.full_url
    assert request.get_header("Xi-api-key") == "test-key-not-real"
    plain = build_signed_url_request(_settings())
    assert "branch_id" not in plain.full_url


def test_parse_retry_after() -> None:
    assert parse_retry_after(None) is None
    assert parse_retry_after("2") == 2.0
    assert parse_retry_after("-1") is None
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") is None


def test_fetch_success_without_sleep() -> None:
    seen: list[urllib.request.Request] = []

    def opener(request: urllib.request.Request) -> _Resp:
        seen.append(request)
        return _Resp(b'{"signed_url":"wss://example.test/socket"}')

    sleeps: list[float] = []
    url = fetch_signed_url(_settings(), opener=opener, sleep=sleeps.append, rng=random.Random(0))
    assert url == "wss://example.test/socket"
    assert sleeps == []
    assert len(seen) == 1


def test_fetch_retries_transport_then_succeeds() -> None:
    calls = {"n": 0}

    def opener(request: urllib.request.Request) -> _Resp:
        del request
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.URLError("down")
        return _Resp(b'{"signed_url":"wss://example.test/socket"}')

    sleeps: list[float] = []
    url = fetch_signed_url(_settings(), opener=opener, sleep=sleeps.append, rng=random.Random(0))
    assert url.startswith("wss://")
    assert len(sleeps) == 1


def test_fetch_does_not_retry_client_error() -> None:
    def opener(request: urllib.request.Request) -> _Resp:
        raise urllib.error.HTTPError(request.full_url, 401, "no", {}, None)

    sleeps: list[float] = []
    with pytest.raises(SignedUrlError, match="http 401") as caught:
        fetch_signed_url(_settings(), opener=opener, sleep=sleeps.append)
    assert caught.value.retryable is False
    assert sleeps == []


def test_fetch_honors_retry_after_cap() -> None:
    calls = {"n": 0}

    def opener(request: urllib.request.Request) -> _Resp:
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                request.full_url, 429, "slow", {"Retry-After": "100"}, None
            )
        return _Resp(b'{"signed_url":"wss://example.test/socket"}')

    sleeps: list[float] = []
    fetch_signed_url(
        _settings(CONSENT_LAB_BACKOFF_CAP_S="8"),
        opener=opener,
        sleep=sleeps.append,
        rng=random.Random(0),
    )
    assert sleeps == [8.0]


def test_fetch_rejects_bad_bodies() -> None:
    bodies = [b"not-json", b"[]", b'{"signed_url":"http://example.test/nope"}', b"{}"]
    for body in bodies:

        def opener(request: urllib.request.Request, payload: bytes = body) -> _Resp:
            del request
            return _Resp(payload)

        with pytest.raises(SignedUrlError):
            fetch_signed_url(
                _settings(CONSENT_LAB_MAX_ATTEMPTS="1"),
                opener=opener,
                sleep=lambda _s: None,
            )


def test_fetch_oserror_is_retryable_and_exhausted() -> None:
    def opener(request: urllib.request.Request) -> _Resp:
        del request
        raise TimeoutError("slow")

    sleeps: list[float] = []
    with pytest.raises(SignedUrlError, match="transport"):
        fetch_signed_url(
            _settings(CONSENT_LAB_MAX_ATTEMPTS="2"),
            opener=opener,
            sleep=sleeps.append,
            rng=random.Random(0),
        )
    assert len(sleeps) == 1


def test_default_sleep_is_used_when_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []
    monkeypatch.setattr("time.sleep", slept.append)

    calls = {"n": 0}

    def opener(request: urllib.request.Request) -> _Resp:
        del request
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.URLError("down")
        return _Resp(b'{"signed_url":"wss://example.test/socket"}')

    fetch_signed_url(_settings(CONSENT_LAB_MAX_ATTEMPTS="2"), opener=opener, rng=random.Random(0))
    assert len(slept) == 1


def test_logs_do_not_echo_the_key_or_url(capsys: pytest.CaptureFixture[str]) -> None:
    from consent_lab.logging_setup import configure

    configure("INFO")

    def opener(request: urllib.request.Request) -> _Resp:
        raise urllib.error.HTTPError(request.full_url, 503, "down", {}, BytesIO(b""))

    with pytest.raises(SignedUrlError):
        fetch_signed_url(
            _settings(CONSENT_LAB_MAX_ATTEMPTS="2"),
            opener=opener,
            sleep=lambda _s: None,
            rng=random.Random(0),
        )
    err = capsys.readouterr().err
    assert "test-key-not-real" not in err
    assert "agent-test" not in err
    assert "signed_url_retry" in err
