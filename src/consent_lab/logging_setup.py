"""JSON logs on stderr. One object per line.

Call sites must not put API keys, signed URLs, or filesystem paths in the
message or in fields. ``add_redaction`` is a backstop for a value that was
loaded from the environment and must not be echoed.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import TextIO, cast

_CONFIGURED = False
_REDACTIONS: list[str] = []
_MIN_SECRET_LEN = 8


def add_redaction(value: str) -> None:
    if len(value) < _MIN_SECRET_LEN:
        return
    if value not in _REDACTIONS:
        _REDACTIONS.append(value)


def clear_redactions() -> None:
    _REDACTIONS.clear()


def redact(text: str) -> str:
    out = text
    for secret in _REDACTIONS:
        out = out.replace(secret, "[REDACTED]")
    return out


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                if isinstance(key, str):
                    payload[key] = _redact_value(cast(object, value))
        if record.exc_info:
            payload["exc"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, sort_keys=True, default=str)


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return redact(value)
    return value


def reset_logging() -> None:
    global _CONFIGURED
    logger = logging.getLogger("consent_lab")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True
    _CONFIGURED = False


def configure(level: str = "INFO", stream: TextIO | None = None) -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger("consent_lab")
    logger.setLevel(level.upper())
    if not _CONFIGURED:
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        _CONFIGURED = True
    return logger


def log(logger: logging.Logger, level: int, message: str, **fields: object) -> None:
    logger.log(level, message, extra={"extra_fields": fields})
