"""Environment-only settings. This module does not read a dotenv file."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass

from consent_lab.errors import ConfigError

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_DEFAULT_SIGNED_URL = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"
_MAX_ATTEMPTS_CEILING = 5


def _raw(env: Mapping[str, str], name: str) -> str:
    return env.get(name, "").strip()


def _int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = _raw(env, name)
    if raw == "":
        return default
    if not raw.isdigit():
        raise ConfigError(name)
    return int(raw)


def _float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = _raw(env, name)
    if raw == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(name) from exc
    if not math.isfinite(value):
        raise ConfigError(name)
    return value


def _at_least(name: str, value: float, low: float) -> float:
    if value < low:
        raise ConfigError(name)
    return value


def _positive(name: str, value: float) -> float:
    if value <= 0:
        raise ConfigError(name)
    return value


@dataclass(frozen=True, repr=False)
class Settings:
    live_enabled: bool
    api_key: str
    agent_id: str
    branch_id: str | None
    log_level: str
    max_attempts: int
    backoff_base_s: float
    backoff_cap_s: float
    seed: int
    evidence_root: str
    sample_rate: int
    min_samples: int
    poll_timeout_s: float
    quiet_after_s: float
    overall_timeout_s: float
    playback_pad_s: float
    feed_interval_s: float
    silence_bytes: int
    signed_url_base: str

    def __repr__(self) -> str:
        return (
            "Settings("
            f"live_enabled={self.live_enabled}, "
            f"log_level={self.log_level!r}, "
            f"max_attempts={self.max_attempts})"
        )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source: Mapping[str, str] = os.environ if env is None else env
        level = (_raw(source, "LOG_LEVEL") or "INFO").upper()
        if level not in _LOG_LEVELS:
            raise ConfigError("LOG_LEVEL")
        branch = _raw(source, "ELEVENLABS_BRANCH_ID")
        base = _raw(source, "CONSENT_LAB_SIGNED_URL_BASE") or _DEFAULT_SIGNED_URL
        if not base.startswith("https://"):
            raise ConfigError("CONSENT_LAB_SIGNED_URL_BASE")
        attempts = _int(source, "CONSENT_LAB_MAX_ATTEMPTS", 3)
        if attempts < 1 or attempts > _MAX_ATTEMPTS_CEILING:
            raise ConfigError("CONSENT_LAB_MAX_ATTEMPTS")
        backoff_base = _at_least(
            "CONSENT_LAB_BACKOFF_BASE_S",
            _float(source, "CONSENT_LAB_BACKOFF_BASE_S", 0.5),
            0.0,
        )
        backoff_cap = _at_least(
            "CONSENT_LAB_BACKOFF_CAP_S",
            _float(source, "CONSENT_LAB_BACKOFF_CAP_S", 8.0),
            backoff_base,
        )
        return cls(
            live_enabled=_raw(source, "LIVE_ENABLED") == "1",
            api_key=_raw(source, "ELEVENLABS_API_KEY"),
            agent_id=_raw(source, "ELEVENLABS_AGENT_ID"),
            branch_id=branch or None,
            log_level=level,
            max_attempts=attempts,
            backoff_base_s=backoff_base,
            backoff_cap_s=backoff_cap,
            seed=_int(source, "CONSENT_LAB_SEED", 42),
            evidence_root=_raw(source, "CONSENT_LAB_EVIDENCE_ROOT") or "evidence/ab",
            sample_rate=int(
                _positive(
                    "CONSENT_LAB_SAMPLE_RATE", float(_int(source, "CONSENT_LAB_SAMPLE_RATE", 16000))
                )
            ),
            min_samples=int(
                _positive(
                    "CONSENT_LAB_MIN_SAMPLES", float(_int(source, "CONSENT_LAB_MIN_SAMPLES", 1600))
                )
            ),
            poll_timeout_s=_positive(
                "CONSENT_LAB_POLL_TIMEOUT_S",
                _float(source, "CONSENT_LAB_POLL_TIMEOUT_S", 0.5),
            ),
            quiet_after_s=_at_least(
                "CONSENT_LAB_QUIET_AFTER_S",
                _float(source, "CONSENT_LAB_QUIET_AFTER_S", 1.0),
                0.0,
            ),
            overall_timeout_s=_positive(
                "CONSENT_LAB_OVERALL_TIMEOUT_S",
                _float(source, "CONSENT_LAB_OVERALL_TIMEOUT_S", 20.0),
            ),
            playback_pad_s=_at_least(
                "CONSENT_LAB_PLAYBACK_PAD_S",
                _float(source, "CONSENT_LAB_PLAYBACK_PAD_S", 0.4),
                0.0,
            ),
            feed_interval_s=_at_least(
                "CONSENT_LAB_FEED_INTERVAL_S",
                _float(source, "CONSENT_LAB_FEED_INTERVAL_S", 0.1),
                0.0,
            ),
            silence_bytes=int(
                _positive(
                    "CONSENT_LAB_SILENCE_BYTES",
                    float(_int(source, "CONSENT_LAB_SILENCE_BYTES", 3200)),
                )
            ),
            signed_url_base=base,
        )

    def refusal_message(self, out_dir: str | None) -> str | None:
        """Same refusal order as the original probe script."""

        if not self.live_enabled:
            return "refusing: this spends ElevenLabs credits. Set LIVE_ENABLED=1 to run."
        if not self.api_key or not self.agent_id or not out_dir:
            return "need ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID and an output dir"
        return None
