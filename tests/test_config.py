from __future__ import annotations

import pytest

from consent_lab.config import Settings
from consent_lab.errors import ConfigError


def test_defaults_are_offline() -> None:
    settings = Settings.from_env({})
    assert settings.live_enabled is False
    assert settings.api_key == ""
    assert settings.agent_id == ""
    assert settings.branch_id is None
    assert settings.log_level == "INFO"
    assert settings.max_attempts == 3
    assert settings.backoff_base_s == 0.5
    assert settings.backoff_cap_s == 8.0
    assert settings.seed == 42
    assert settings.evidence_root == "evidence/ab"
    assert settings.sample_rate == 16000
    assert settings.min_samples == 1600
    assert settings.poll_timeout_s == 0.5
    assert settings.quiet_after_s == 1.0
    assert settings.overall_timeout_s == 20.0
    assert settings.playback_pad_s == 0.4
    assert settings.feed_interval_s == 0.1
    assert settings.silence_bytes == 3200
    assert settings.signed_url_base.startswith("https://")


def test_live_flag_is_exact() -> None:
    assert Settings.from_env({"LIVE_ENABLED": "1"}).live_enabled is True
    assert Settings.from_env({"LIVE_ENABLED": "true"}).live_enabled is False
    assert Settings.from_env({"LIVE_ENABLED": " 1 "}).live_enabled is True


def test_branch_and_stripping() -> None:
    settings = Settings.from_env(
        {
            "ELEVENLABS_API_KEY": "  test-key-not-real  ",
            "ELEVENLABS_AGENT_ID": " agent ",
            "ELEVENLABS_BRANCH_ID": " branch ",
            "LOG_LEVEL": "debug",
        }
    )
    assert settings.api_key == "test-key-not-real"
    assert settings.agent_id == "agent"
    assert settings.branch_id == "branch"
    assert settings.log_level == "DEBUG"


def test_empty_branch_is_absent() -> None:
    assert Settings.from_env({"ELEVENLABS_BRANCH_ID": "   "}).branch_id is None


def test_repr_hides_secrets() -> None:
    settings = Settings.from_env(
        {"ELEVENLABS_API_KEY": "test-key-not-real", "ELEVENLABS_AGENT_ID": "agent-42"}
    )
    text = repr(settings)
    assert "test-key-not-real" not in text
    assert "agent-42" not in text
    assert "live_enabled=False" in text


def test_from_env_mapping_ignores_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVE_ENABLED", "1")
    assert Settings.from_env({}).live_enabled is False


def test_from_env_reads_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVE_ENABLED", "1")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    settings = Settings.from_env()
    assert settings.live_enabled is True
    assert settings.log_level == "ERROR"


@pytest.mark.parametrize(
    ("env", "name"),
    [
        ({"CONSENT_LAB_MAX_ATTEMPTS": "0"}, "CONSENT_LAB_MAX_ATTEMPTS"),
        ({"CONSENT_LAB_MAX_ATTEMPTS": "6"}, "CONSENT_LAB_MAX_ATTEMPTS"),
        ({"CONSENT_LAB_MAX_ATTEMPTS": "nope"}, "CONSENT_LAB_MAX_ATTEMPTS"),
        ({"LOG_LEVEL": "LOUD"}, "LOG_LEVEL"),
        ({"CONSENT_LAB_BACKOFF_BASE_S": "-1"}, "CONSENT_LAB_BACKOFF_BASE_S"),
        ({"CONSENT_LAB_BACKOFF_CAP_S": "0.1"}, "CONSENT_LAB_BACKOFF_CAP_S"),
        ({"CONSENT_LAB_BACKOFF_BASE_S": "inf"}, "CONSENT_LAB_BACKOFF_BASE_S"),
        ({"CONSENT_LAB_SAMPLE_RATE": "0"}, "CONSENT_LAB_SAMPLE_RATE"),
        ({"CONSENT_LAB_MIN_SAMPLES": "-3"}, "CONSENT_LAB_MIN_SAMPLES"),
        ({"CONSENT_LAB_POLL_TIMEOUT_S": "0"}, "CONSENT_LAB_POLL_TIMEOUT_S"),
        ({"CONSENT_LAB_OVERALL_TIMEOUT_S": "-2"}, "CONSENT_LAB_OVERALL_TIMEOUT_S"),
        ({"CONSENT_LAB_QUIET_AFTER_S": "-0.1"}, "CONSENT_LAB_QUIET_AFTER_S"),
        ({"CONSENT_LAB_PLAYBACK_PAD_S": "-1"}, "CONSENT_LAB_PLAYBACK_PAD_S"),
        ({"CONSENT_LAB_FEED_INTERVAL_S": "-1"}, "CONSENT_LAB_FEED_INTERVAL_S"),
        ({"CONSENT_LAB_SILENCE_BYTES": "0"}, "CONSENT_LAB_SILENCE_BYTES"),
        ({"CONSENT_LAB_SIGNED_URL_BASE": "http://example.test"}, "CONSENT_LAB_SIGNED_URL_BASE"),
        ({"CONSENT_LAB_SEED": "x"}, "CONSENT_LAB_SEED"),
    ],
)
def test_rejects_bad_values(env: dict[str, str], name: str) -> None:
    with pytest.raises(ConfigError, match=name):
        Settings.from_env(env)


def test_attempt_ceiling_accepts_five() -> None:
    assert Settings.from_env({"CONSENT_LAB_MAX_ATTEMPTS": "5"}).max_attempts == 5


def test_seed_zero_is_allowed() -> None:
    assert Settings.from_env({"CONSENT_LAB_SEED": "0"}).seed == 0


def test_refusal_order() -> None:
    off = Settings.from_env({})
    assert off.refusal_message(None) == (
        "refusing: this spends ElevenLabs credits. Set LIVE_ENABLED=1 to run."
    )
    assert off.refusal_message("out") == off.refusal_message(None)
    on = Settings.from_env({"LIVE_ENABLED": "1"})
    assert on.refusal_message("out") == (
        "need ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID and an output dir"
    )
    ready = Settings.from_env(
        {"LIVE_ENABLED": "1", "ELEVENLABS_API_KEY": "k", "ELEVENLABS_AGENT_ID": "a"}
    )
    assert ready.refusal_message(None) is not None
    assert ready.refusal_message("out") is None


def test_custom_evidence_root() -> None:
    settings = Settings.from_env({"CONSENT_LAB_EVIDENCE_ROOT": "var/evidence"})
    assert settings.evidence_root == "var/evidence"
