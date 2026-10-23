# Changelog

## Unreleased

- Add narrated English demo video (`voice_receptionist_consent_lab_demo_en.mp4`) with subtitles and evidence pack under `docs/demo/`.
- English throughout. Prompts, the knowledge base, simulation cases, evidence transcripts, history, and the working log are English renderings. Acoustic numbers, simulation scores, credit counts, and the labels MEASURED, [EST], [SYN], SIMULATED, and UNVERIFIED are unchanged. The 2026-10-21 suites ran the Spanish wording; those scores were not recomputed.
- Business value: a `## Business value` section in the README and `docs/BUSINESS_VALUE.md`. The buyer is the fictional Demo Palermo Clinic, not a client. The ROI sketch is the existing [EST] arithmetic in `docs/COST.md`. The default path is 0 USD.
- Dependabot: `.github/dependabot.yml` opens weekly updates for pip and for GitHub Actions, both at `/`.
- Profile status: CI is active and package 0.1.0 is the released version. The README states both. No "CI pending" line was in the tree.
- CI is active. `.github/workflows/ci.yml` runs on Python 3.11 and 3.12: ruff check, ruff format --check, mypy, pytest with coverage (fail under 85%), and `python -m consent_lab secretscan`. It uses `actions/checkout@v7` and `actions/setup-python@v7`. `docs/ci/ci.yml` points at that workflow.

## 0.1.0 - 2026-10-22

- Package the offline acoustic measurement and the credit-gated WebSocket probe under `src/consent_lab`. The old `tools/` commands delegate to it. The prompt, the sanitized config, the case files, and the saved audio are unchanged.
- Environment-only settings. The process does not read a dotenv file. `LIVE_ENABLED` must be the string `1`. Anything else leaves the probe off.
- JSON logs. Bounded retries (at most 5) on the signed-URL fetch and on the socket connect, with jitter and a cap. A turn that has started is not retried. A turn with no non-silent interval is skipped instead of aborting the CSV.
- Tooling: ruff, mypy (strict), pytest with coverage, pre-commit, a small Dockerfile, and a secret scan. CI for Python 3.11 and 3.12 is `.github/workflows/ci.yml`.
- Docs in English: README, `docs/HOW_IT_WORKS.md`, discovery, risks, runbook, and cost. Labels used below and in the README are MEASURED, [EST], [SYN], SIMULATED, and UNVERIFIED.
- Local pytest result: 100 passed, 97.42% line coverage, Python 3.12.3. MEASURED.

The v17 simulation score (8 of 10) and the untested v18 consent re-ask are historical lab records. This package does not re-run them.
