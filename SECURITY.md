# Security

This repository is a portfolio lab. It is not a hosted clinic line, and it does not hold a phone number.

## Reporting

Use GitHub private vulnerability reporting (Security tab, Report a vulnerability). Do not open a public issue that contains an API key, an agent id, a signed URL, or a recording of a real person. This lab should not contain those, and a report should not add them. There is no bounty.

## What is in scope

- The live probe refuses to run unless `LIVE_ENABLED=1`, and it reads the key only from the environment.
- Bounded retries on the signed-URL fetch and the socket connect. A turn that has already started is not retried.
- JSON logs do not include the API key, the agent id, or the signed URL. `Settings` repr omits them.
- `python -m consent_lab secretscan` flags common key shapes and local absolute paths.
- Evidence metadata in this tree is already redacted. New runs of the probe do not write a conversation id.

## What is not in scope

- A real identity provider, an origin allowlist, or multi-tenant auth. The sanitized config records that platform authentication was off. A deployment would turn it on. This repo does not.
- Recording consent for a real caller. The disclosure in the prompt is a script. It is not a legal opinion and it is not enforced by code.
- Hosting, telephony, or a booking database.
- The proposed workflow in `docs/ci/ci.yml` is not installed. It has to be copied to `.github/workflows/ci.yml` by someone whose token can write that path. Until then, GitHub Actions does not run it.

## Secrets

Configuration is environment variables only. The process does not read a `.env` file. `.env.example` has empty placeholders. Do not commit a key. Do not paste a key into the README, a test, or a log.

CI, when the workflow is installed, does not set `LIVE_ENABLED`. Pytest does not open a socket. The default Docker command is `python -m consent_lab about`.

## Data

The clinic, the doctors, the prices, and every test caller are synthetic. The audio under `evidence/ab/` and `samples/` is agent TTS from stock library voices, not a recording of a caller.
