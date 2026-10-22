# Runbook and handoff

## Offline, every time

From a checkout, with `libsndfile1` installed so WAV reads work:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python -m pytest
.venv/bin/python -m consent_lab secretscan .
.venv/bin/python -m consent_lab measure --root evidence/ab
```

`make ci` is the same lint, types, tests, and scan. None of these set `LIVE_ENABLED`. None of them need a key.

`python -m consent_lab about` prints the version and `live_enabled=false` when the flag is unset.

The Docker image runs `about` and does not install the audio extra. It is a smoke image, not a measurement image.

## Live probe

This spends credits. Do not run it to "see if CI works".

```bash
export LIVE_ENABLED=1
export ELEVENLABS_API_KEY=...
export ELEVENLABS_AGENT_ID=...
# optional: a test branch, not the default branch
export ELEVENLABS_BRANCH_ID=...
.venv/bin/python -m consent_lab probe evidence/ab/MYRUN
.venv/bin/python -m consent_lab measure --root evidence/ab
```

Unset `LIVE_ENABLED` when you are done. A value of `true` or `yes` does not enable the probe. Only `1` does.

If the signed-URL call returns 401, the probe does not retry. If it returns 429 or a 5xx, it retries at most five times and then exits 1. The log line says `signed_url_retry` or `socket_retry` and does not include the key or the URL.

## If a transcript shows a personal field before an explicit yes

1. Stop the test page. Do not place a phone call.
2. Do not copy that audio into this repo.
3. Restore the previous prompt and config from `agent/history/`. There is no database to roll back. Bookings were never stored.
4. Write the failure in `tests/RESULTS.md` as a fail. Do not describe a prompt edit as checked until the same case has been rerun.
5. v18 is the example: the edit is in the prompt, the rerun did not happen, the status is UNVERIFIED.

## Handoff packet

Give the next person:

- `agent/system_prompt.md`, `agent/knowledge_base.md`, `agent/agent_config.sanitized.json`
- `agent/history/` and `agent/VERSIONS.md`
- `tests/cases/` and `tests/RESULTS.md`
- `evidence/ab/measurements.csv` and `docs/HOW_IT_WORKS.md`
- This runbook, `docs/RISKS.md`, and `docs/COST.md`
- The note that CD08 still fails and that the v18 consent re-ask is UNVERIFIED

Do not give them:

- An API key, an agent id, a branch id, a signed URL, or a dashboard link
- A `.env` file
- A claim that the package tests prove the prompt

## Proposed CI

`docs/ci/ci.yml` runs ruff, mypy, pytest with coverage, and the secret scan on Python 3.11 and 3.12. It is not installed. Copy it to `.github/workflows/ci.yml` with a token that can write that path. Until that copy exists, a green local pytest is the check you have.
