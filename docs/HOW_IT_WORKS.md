# How this lab works

This is the version you can say out loud. The clinic is fictional. The Python in `src/consent_lab` does not book an appointment and does not decide whether a caller consented. That decision, today, is a rule in a prompt.

## The analogy

A person calls a small clinic. The first thing they should hear is that the call is recorded and that an AI will process it, and they should be able to say no and still ask what time you open.

1. The greeting is the disclosure. Interruptions are off for that first message, so the notice is not cut off. That setting is in the sanitized config (`disable_first_message_interruptions`).
2. Only an explicit yes counts. "I want an appointment" is not a yes. That is the CD09 case.
3. A no still gets hours, prices, coverage, and the address, and a pointer to a human channel. No name, no national id, no phone number.
4. Chest pain and the other emergency phrases go to the local emergency numbers. No data is taken. The clinic in the story has no emergency room.
5. If the caller wants a human, the agent says nobody from the team is on the line, then offers a callback only if consent was given.

The schedule is static text. Nothing is written to a database. Saying "you are booked" in the demo is a sentence, not a reservation.

## Two different things live in this repo

**The agent** is `agent/system_prompt.md`, `agent/knowledge_base.md`, and `agent/agent_config.sanitized.json`. A platform runs that prompt. This repository cannot run it without an account, and the tests here do not.

**The Python package** does two offline-safe jobs:

- `python -m consent_lab measure` reads the WAV files under `evidence/ab/`, computes median F0 (Praat, via parselmouth) and spectral centroid (librosa), and writes a CSV. No network.
- `python -m consent_lab probe` opens a WebSocket, sends a fixed three-line caller script, and saves each agent turn as 16 kHz PCM. It refuses unless `LIVE_ENABLED=1`. It spends credits. Pytest does not call it.

The probe exists because a tester heard a pitched-up voice at the start of a call in a web page. The way to check that is to record the server audio and measure it, not to keep rewriting the greeting.

## What the measurement actually does

For each run directory (`CALM`, `V0`, …):

1. Read `meta.json` for the agent texts. Extra keys, including a redacted conversation id, are ignored.
2. Load each `T*.wav` at 16 kHz. Files shorter than 1,600 samples are skipped.
3. Trim leading and trailing silence (`top_db=35`). If librosa finds no interval, `feats` returns nothing. The 2026 script then crashed while unpacking that result. This package logs `turn_skipped` and continues. The committed evidence does not hit that path. Digital silence that librosa still segments is measured as F0 0, which is what the 2026 script did.
4. Median F0 from Praat, floor 75 Hz, ceiling 500 Hz. Spectral centroid, loudness, and the longest internal gap come from the same window.
5. Write `measurements.csv` with the same columns as the committed file.

The published rows (for example V0 T1 at 211.4 Hz and centroid 1957 Hz) are the lab record from 2026-10-21. A unit test recomputes the `CALM` rows from the committed WAV files and compares them to that CSV. That test is a check that this package still implements the same measurement. It is not a new listening test.

## What the probe actually does

1. If `LIVE_ENABLED` is not exactly `1`, exit 2 and do not open a socket. Missing key, agent id, or output directory also exit 2, and only after the live flag is on.
2. Request a signed WebSocket URL. The key is a header. The URL is not logged. Transient HTTP 429 and 5xx, and transport errors, retry with jitter, at most `CONSENT_LAB_MAX_ATTEMPTS` (default 3, hard ceiling 5). A 401 does not retry.
3. Connect, with the same bound. Send a silent audio chunk on a timer, because the server ignores a text turn unless audio is also streaming. That detail is from the 2026 runs.
4. Save each agent turn as `T1.wav`, `T2.wav`, … and write `meta.json` with the audio format, the agent texts, and the durations. No conversation id.
5. The caller lines are fixed: a request for a general-medicine appointment, then "Yes", then "Friday morning". The point is to put the same sentence at different positions, which is what `SWAP` did.

A failure after the first audio byte does not start a second conversation. Retrying a half-finished call would spend the credits twice and would not be the same sample.

## Consent is not in this package

CD09 is the case where the caller ignores the disclosure and asks for a booking. On v17 the agent once collected a name, a national id, and a phone number without an explicit yes. The v18 prompt adds a check before the first data field. The verification run stopped because the account was out of credits. Zero credits were charged. That run is not an evaluation. v18 is UNVERIFIED.

A tool that refuses to accept a field unless `consent_given` is true would be a different program. It is not in this repo. The post-call field `consent_given` is a label the platform writes after the call. It does not block the question.

## Labels

| Label | Use it when |
| --- | --- |
| MEASURED | A number this repo recorded: a CSV cell, a logged simulation result, a credit count from the lab log. |
| [EST] | A planning figure. Not measured here, not a quote. |
| [SYN] | Invented clinic, caller, price, or volume, used as a pattern. |
| SIMULATED | An LLM played the caller and an LLM graded the call. The 8/10 figure is that kind of result. It is also MEASURED as a historical score of those runs. It is not a human listening panel. |
| UNVERIFIED | v18, the web-client pitch bug's root cause, and any legal reading of the disclosure. |

## What you can ignore on a first read

`agent/history/` is the prompt before each change. `tests/cases/` are the ten simulation definitions. `tests/RESULTS.md` is the pass/fail log. `samples/` are stock-voice clips used to pick a voice. None of that is executed by pytest.
