"""Errors raised by the lab package. Messages stay free of keys and paths."""

from __future__ import annotations


class ConsentLabError(Exception):
    """Base error. ``str(exc)`` is safe to print."""


class ConfigError(ConsentLabError):
    """An environment value is missing or not usable. The message is the variable name."""


class SignedUrlError(ConsentLabError):
    """The signed-URL request failed. The message is a status class, not the URL."""

    def __init__(
        self, message: str, *, retryable: bool, retry_after_s: float | None = None
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.retry_after_s = retry_after_s


class ProbeError(ConsentLabError):
    """A live-probe frame was not usable. The message is a short code."""


class MeasurementError(ConsentLabError):
    """An evidence directory could not be measured. The message names the run, not a path."""
