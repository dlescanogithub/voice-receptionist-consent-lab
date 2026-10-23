# voice-receptionist-consent-lab

**TL;DR**

- An English voice receptionist for a fictional clinic. The rule under test is consent to recording and to AI processing before any personal data, plus emergency routing, no diagnosis, and an honest human handoff. The 2026-10-21 simulation suites ran the Spanish wording of this design. The scores below are the scores of those runs.
- The last full simulation suite (v17, 2026-10-21) passed 8 of 10. CD08 (English) still fails. The v18 re-ask for the case where the caller ignores the consent question is UNVERIFIED.
- The Python package measures saved agent audio offline and can open a credit-gated WebSocket probe. Pytest does not call the probe. Start at [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

> **Honest limits.** The 8/10 figure is a SIMULATED suite: an LLM played the caller and an LLM graded the call, a few runs, one model. It is MEASURED as the score of those runs. It is not a listening panel and it does not transfer to another model. The consent gate is a prompt rule. On v17 it failed once. Package tests do not replay that call. They check the measurement code and the probe's refusal path.

The clinic (Demo Palermo Clinic), its doctors, address, phone numbers, prices, and patients are [SYN]. Every test caller uses invented data. The repo has no agent id, no branch id, no dashboard link, and no API key. Nothing here comes from an employer or a client.

## Problem and what it does

A clinic voice line records the call and an AI processes it. The caller should hear that before they give a name, a national id, or a phone number, and should be able to say no and still get hours, prices, coverage, and the address. A demo that books an appointment smoothly does not show that. A caller who ignores the question and asks for an appointment does. That case is CD09.

The agent speaks the notice in the first message, with interruptions off for that message. Only an explicit yes counts. A "no" gets general information and a human channel (the clinic phone, a messaging app, or a visit) and no data is taken. Emergencies go to 107 or 911, or to 135 for self-harm risk, and no data is requested. The clinic in the story has no emergency room. If the caller wants a person, the agent says nobody from the team is on the line before it takes a callback, and only if consent was given.

| Area | Behavior | Where |
| --- | --- | --- |
| Consent | First message names recording and AI, and asks for agreement. Only an explicit yes counts. Ignoring the question gets a general answer, then one short re-ask before the first data field (v18). | `agent/system_prompt.md` |
| "No" path | General information only. No data. The recording offer is not repeated. Withdrawing consent mid-call stops collection. | same |
| Data minimization | Name, national id, phone, and coverage only. Id and phone are read back digit by digit. | same |
| No diagnosis | No condition, medication, dose, or "this is serious". It offers a specialty. | same |
| Emergencies | Chest pain, trouble breathing, and the other listed signs go to 107 or 911. Self-harm risk also mentions 135. No data. | same |
| Human handoff | Says nobody is available live, then a callback (name and phone) only with consent. | same |
| Languages | Clear, short English in this tree. The two-sentence cap is in the prompt and is not met (CD08). The 2026-10-21 suites ran in Spanish, with a switch to English under the same rules. | same |
| Post-call | Five evaluation criteria and nine data fields, including `consent_given`. The field is a label after the call. It does not block a question. | `agent/agent_config.sanitized.json` |

Voice stack in the sanitized config: TTS `eleven_v4_turbo`, expressive mode, stock library voice, stability 0.5, speed 1.0, similarity 0.8. Turn-taking is `turn_v3`. The knowledge base is passed in prompt mode, without retrieval, to keep latency down.

The Python package does not implement that policy. It measures audio and, only when you opt in, records a scripted probe. See [Architecture](#architecture).

## Quickstart

Offline. No key. No credits. On Linux, `libsndfile1` is needed to read WAV files.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
