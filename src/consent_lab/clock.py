"""Clocks for the live probe.

``WallClock.advance`` is a no-op: ``asyncio.wait_for`` already consumed the
poll interval, so ``now()`` has moved. Tests pass a clock whose ``advance``
moves time without sleeping.
"""

from __future__ import annotations

import asyncio
import time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float: ...

    def advance(self, seconds: float) -> None: ...

    async def sleep(self, seconds: float) -> None: ...


class WallClock:
    def now(self) -> float:
        return time.monotonic()

    def advance(self, seconds: float) -> None:
        del seconds

    async def sleep(self, seconds: float) -> None:
        if seconds > 0:
            await asyncio.sleep(seconds)
