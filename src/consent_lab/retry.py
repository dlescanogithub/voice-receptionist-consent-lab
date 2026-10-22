"""Bounded retries with jitter.

The ceiling is small on purpose. A signed-URL fetch or a socket connect may
try again. A turn that already started is never retried, because that would
spend a second conversation.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import TypeVar

BASE_S = 0.5
CAP_S = 8.0

T = TypeVar("T")


def retry_delay_s(
    attempt: int,
    retry_after_s: float | None,
    *,
    base_s: float = BASE_S,
    cap_s: float = CAP_S,
    rng: random.Random | None = None,
) -> float:
    """Seconds to wait after failure number ``attempt`` (1 on the first failure)."""

    if retry_after_s is not None and retry_after_s >= 0:
        return min(cap_s, retry_after_s)
    exponent = max(1, attempt) - 1
    slot = min(cap_s, base_s * float(2**exponent))
    source = rng if rng is not None else random.Random()
    return float(slot) * float(source.uniform(0.5, 1.0))


def retry_after_of(exc: BaseException) -> float | None:
    value = getattr(exc, "retry_after_s", None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def run_bounded(
    fn: Callable[[], T],
    *,
    max_attempts: int,
    sleep: Callable[[float], None],
    classify: Callable[[BaseException], bool],
    rng: random.Random | None = None,
    base_s: float = BASE_S,
    cap_s: float = CAP_S,
    on_retry: Callable[[int, BaseException, float], None] | None = None,
) -> T:
    """Call ``fn`` up to ``max_attempts`` times. Non-retryable errors propagate immediately."""

    if max_attempts < 1:
        raise ValueError("max_attempts")
    attempt = 1
    while True:
        try:
            return fn()
        except Exception as exc:
            if attempt >= max_attempts or not classify(exc):
                raise
            delay = retry_delay_s(attempt, retry_after_of(exc), base_s=base_s, cap_s=cap_s, rng=rng)
            if on_retry is not None:
                on_retry(attempt, exc, delay)
            sleep(delay)
            attempt += 1
