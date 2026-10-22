"""Fetch a Conversational AI signed URL. Retries are bounded and the URL is not logged."""

from __future__ import annotations

import json
import logging
import random
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Protocol

from consent_lab.config import Settings
from consent_lab.errors import SignedUrlError
from consent_lab.logging_setup import log
from consent_lab.retry import run_bounded

_LOGGER = logging.getLogger("consent_lab.signed_url")


class _Body(Protocol):
    def read(self) -> bytes: ...

    def __enter__(self) -> _Body: ...

    def __exit__(self, *args: object) -> None: ...


Opener = Callable[[urllib.request.Request], _Body]


def build_signed_url_request(settings: Settings) -> urllib.request.Request:
    query: dict[str, str] = {"agent_id": settings.agent_id}
    if settings.branch_id:
        query["branch_id"] = settings.branch_id
    url = settings.signed_url_base + "?" + urllib.parse.urlencode(query)
    return urllib.request.Request(url, headers={"xi-api-key": settings.api_key})


def parse_retry_after(header: str | None) -> float | None:
    if header is None:
        return None
    try:
        value = float(header.strip())
    except ValueError:
        return None
    if value < 0:
        return None
    return value


def _from_http(exc: urllib.error.HTTPError) -> SignedUrlError:
    header = exc.headers.get("Retry-After") if exc.headers is not None else None
    retry_after = parse_retry_after(header if isinstance(header, str) else None)
    retryable = exc.code == 429 or 500 <= exc.code <= 599
    return SignedUrlError(f"http {exc.code}", retryable=retryable, retry_after_s=retry_after)


def _read_signed_url(response: _Body) -> str:
    try:
        payload = json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SignedUrlError("bad body", retryable=False) from exc
    if not isinstance(payload, dict):
        raise SignedUrlError("bad body", retryable=False)
    signed = payload.get("signed_url")
    if not isinstance(signed, str) or not signed.startswith("wss://"):
        raise SignedUrlError("missing signed_url", retryable=False)
    return signed


def fetch_signed_url(
    settings: Settings,
    *,
    opener: Opener | None = None,
    sleep: Callable[[float], None] | None = None,
    rng: random.Random | None = None,
) -> str:
    """Return the signed WebSocket URL. Raises ``SignedUrlError`` when retries are exhausted."""

    open_fn: Opener = opener if opener is not None else urllib.request.urlopen

    def once() -> str:
        request = build_signed_url_request(settings)
        try:
            with open_fn(request) as response:
                return _read_signed_url(response)
        except urllib.error.HTTPError as exc:
            raise _from_http(exc) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise SignedUrlError("transport", retryable=True) from exc

    def on_retry(attempt: int, exc: BaseException, delay: float) -> None:
        log(
            _LOGGER,
            logging.WARNING,
            "signed url retry",
            event="signed_url_retry",
            attempt=attempt,
            error=str(exc),
            delay_s=round(delay, 3),
        )

    return run_bounded(
        once,
        max_attempts=settings.max_attempts,
        sleep=sleep if sleep is not None else _sleep,
        classify=lambda exc: isinstance(exc, SignedUrlError) and exc.retryable,
        rng=rng if rng is not None else random.Random(settings.seed),
        base_s=settings.backoff_base_s,
        cap_s=settings.backoff_cap_s,
        on_retry=on_retry,
    )


def _sleep(seconds: float) -> None:
    import time

    time.sleep(seconds)
