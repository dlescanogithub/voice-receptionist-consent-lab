from __future__ import annotations

import json
import logging
import random

import pytest

from consent_lab.logging_setup import JsonFormatter, add_redaction, configure, log
from consent_lab.retry import retry_after_of, retry_delay_s, run_bounded


def test_json_line_and_redaction(capsys: pytest.CaptureFixture[str]) -> None:
    configure("INFO")
    add_redaction("test-key-not-real")
    add_redaction("short")
    logger = logging.getLogger("consent_lab.demo")
    log(
        logger,
        logging.INFO,
        "saw test-key-not-real",
        event="demo",
        note="test-key-not-real and short",
    )
    line = capsys.readouterr().err.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["level"] == "INFO"
    assert payload["event"] == "demo"
    assert payload["message"] == "saw [REDACTED]"
    assert payload["note"] == "[REDACTED] and short"
    assert "test-key-not-real" not in line
    assert "short" in payload["note"]


def test_debug_is_filtered(capsys: pytest.CaptureFixture[str]) -> None:
    configure("INFO")
    log(logging.getLogger("consent_lab"), logging.DEBUG, "hidden", event="nope")
    assert capsys.readouterr().err == ""


def test_configure_is_idempotent(capsys: pytest.CaptureFixture[str]) -> None:
    configure("INFO")
    configure("DEBUG")
    logger = logging.getLogger("consent_lab")
    ours = [handler for handler in logger.handlers if isinstance(handler.formatter, JsonFormatter)]
    assert len(ours) == 1
    assert logger.level == logging.DEBUG
    log(logger, logging.ERROR, "once", event="once")
    assert capsys.readouterr().err.strip().count("\n") == 0


def test_exception_text_is_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    configure("INFO")
    add_redaction("boom-secret")
    logger = logging.getLogger("consent_lab")
    try:
        raise RuntimeError("boom-secret")
    except RuntimeError:
        logger.exception("failed")
    line = capsys.readouterr().err.strip().splitlines()[-1]
    payload = json.loads(line)
    assert "boom-secret" not in line
    assert "[REDACTED]" in payload["exc"]


def test_formatter_leaves_non_strings() -> None:
    record = logging.LogRecord("consent_lab", logging.INFO, __file__, 1, "ok", (), None)
    record.extra_fields = {"n": 3, "flag": True}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["n"] == 3
    assert payload["flag"] is True


def test_retry_delay_honors_retry_after_and_cap() -> None:
    assert retry_delay_s(1, 2.0, cap_s=8.0) == 2.0
    assert retry_delay_s(1, 100.0, cap_s=8.0) == 8.0
    assert retry_delay_s(1, 0.0, cap_s=8.0) == 0.0
    negative = retry_delay_s(1, -1.0, rng=random.Random(1))
    missing = retry_delay_s(1, None, rng=random.Random(1))
    assert negative == missing


def test_retry_delay_is_bounded() -> None:
    delay = retry_delay_s(10, None, base_s=0.5, cap_s=8.0, rng=random.Random(2))
    assert 4.0 <= delay <= 8.0


def test_retry_after_of_ignores_bool_and_text() -> None:
    class Marker(Exception):
        retry_after_s: object

    assert retry_after_of(Exception("x")) is None
    err = Marker("x")
    err.retry_after_s = True
    assert retry_after_of(err) is None
    err.retry_after_s = "soon"
    assert retry_after_of(err) is None
    err.retry_after_s = 1
    assert retry_after_of(err) == 1.0


def test_run_bounded_succeeds_without_sleep() -> None:
    sleeps: list[float] = []
    assert (
        run_bounded(lambda: "ok", max_attempts=3, sleep=sleeps.append, classify=lambda _e: True)
        == "ok"
    )
    assert sleeps == []


def test_run_bounded_retries_then_succeeds() -> None:
    calls = {"n": 0}

    def fn() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("later")
        return "ok"

    sleeps: list[float] = []
    result = run_bounded(
        fn,
        max_attempts=3,
        sleep=sleeps.append,
        classify=lambda exc: isinstance(exc, TimeoutError),
        rng=random.Random(0),
    )
    assert result == "ok"
    assert len(sleeps) == 2


def test_run_bounded_stops_on_nonretryable() -> None:
    sleeps: list[float] = []

    def fn() -> str:
        raise ValueError("no")

    with pytest.raises(ValueError, match="no"):
        run_bounded(fn, max_attempts=3, sleep=sleeps.append, classify=lambda _e: False)
    assert sleeps == []


def test_run_bounded_exhausts() -> None:
    sleeps: list[float] = []
    with pytest.raises(TimeoutError):
        run_bounded(
            lambda: (_ for _ in ()).throw(TimeoutError("later")),
            max_attempts=2,
            sleep=sleeps.append,
            classify=lambda exc: isinstance(exc, TimeoutError),
            rng=random.Random(0),
        )
    assert len(sleeps) == 1


def test_run_bounded_rejects_zero_attempts() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        run_bounded(lambda: 1, max_attempts=0, sleep=lambda _s: None, classify=lambda _e: True)


def test_on_retry_callback() -> None:
    seen: list[int] = []

    def on_retry(attempt: int, exc: BaseException, delay: float) -> None:
        seen.append(attempt)
        assert isinstance(exc, TimeoutError)
        assert delay >= 0

    calls = {"n": 0}

    def fn() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("later")
        return "ok"

    run_bounded(
        fn,
        max_attempts=2,
        sleep=lambda _s: None,
        classify=lambda exc: isinstance(exc, TimeoutError),
        on_retry=on_retry,
        rng=random.Random(1),
    )
    assert seen == [1]
