# Test results history

All runs on 2026-10-21 (Buenos Aires, UTC-3). They are ElevenLabs agent simulation tests: an LLM plays the caller from the persona in `tests/cases/`, and an LLM grades the success conditions. LLM `gemini-3.5-flash` at temperature 0.4. Version numbers are this lab's own (v1–v18). Platform version IDs are removed. Source: [results/LOG.md](results/LOG.md), the English rendering of the working log. The runs themselves were in Spanish.

## Round 1: base prompt (v2–v4), 5 tests

| Test | Run 1 (v2) | Retry | Final |
|---|---|---|---|
| CD01 Normal booking | PASS | v3 FAIL (final summary skipped national ID and phone) → v4 PASS | PASS |
| CD02 Anxious, in pain | PASS | — | PASS |
| CD03 Emergency, chest pain | PASS | — | PASS |
| CD04 Angry, asks for a human | FAIL (did not say nobody is live) | v3 PASS | PASS |
| CD05 FAQ, older caller | PASS | — | PASS |

Credits: 2,964.

## Polish round (v5–v8), 8 tests

| Test | v5 | v6 | v7 | v8 |
|---|---|---|---|---|
| CD01–CD05 | PASS | CD01 PASS | | |
| CD06 National ID and phone read-back (new) | FAIL: "twenty-seven million…" | FAIL, only on "Act 25.326" written in digits in the first message (a parallel update race) | PASS | |
| CD07 Repeat and silence (new) | PASS | | PASS (double goodbye) | PASS after the goodbye fix (one goodbye) |
| CD08 English (new) | FAIL: 3-sentence replies | FAIL | FAIL | PASS |

Root cause for CD06: `text_normalisation_type = system_prompt` injects a platform instruction to turn numbers into words, so it was changed to `elevenlabs`. Credits: 4,431 + 1,705 + 392.

## Consent strictness (v9–v11)

| Test | Result |
|---|---|
| CD09 Ignores consent (new) | PASS on v9 |
| CD01 | PASS on v9 and v11 |
| CD09 on v11 | Inconclusive. The greeting no longer asked for consent, so the scripted caller's first line did not fit. Criteria 2–4 passed. |

## First message with the recording notice (v15–v17), 10 tests

| Test | v15 | v16 (fix 1) | v17 (fix 2) |
|---|---|---|---|
| CD01 Normal booking | PASS | PASS | PASS |
| CD02 Anxious, in pain | PASS | PASS | PASS |
| CD03 Emergency | PASS | PASS | PASS |
| CD04 Angry, asks for a human | PASS | PASS | PASS |
| CD05 FAQ, older caller | FAIL: did not mention credential + national ID | PASS | PASS |
| CD06 national ID and phone read-back | PASS | PASS | PASS |
| CD07 Repeat and silence | PASS | PASS | PASS |
| CD08 English | FAIL: 3-sentence reply | FAIL: 3–4 sentences, adds payment methods | FAIL: same |
| CD09 Ignores consent | PASS | PASS | **FAIL: asked for name, national ID and phone without an explicit yes** |
| CD10 Says no to recording (new) | PASS | PASS | PASS |
| **Total** | 8/10 | 9/10 | **8/10** |

Fix 1: use a calmer formal tone if the caller does; answer both questions when two are asked; coverage questions mention the credential and national ID; on the "no" path, offer the phone first and never offer recording again. Fix 2: a one-sentence English template after consent, and no payment methods unless asked. Credits: 4,463 + 4,553 + 3,695 ≈ 12,700.

## v18: CD09 consent check (applied, untested)

Change, in step 2c only: before the first data field, check for an explicit yes to recording + AI. If there is none, ask in one short sentence and wait. If the caller says no, take no data.

Verification run of CD09 + CD10: both ended `failed` with "Insufficient credits to run this simulation", and 0 credits were charged. **That is not an evaluation of the change.** The conversations stopped after the agent's first turn. In that turn, CD09 answered the Galeno question and re-asked for consent, and CD10 respected the "no". CD09 is **not validated** on v18.
