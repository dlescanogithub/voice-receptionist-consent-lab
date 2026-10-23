# Business value

Fictional clinic only. Demo Palermo Clinic is the made-up outpatient clinic already used in this repository. It is not a client and not an employer. This note does not add a second company, and it does not add money figures that are not already in this repository.

Labels:

- **MEASURED**: a command or a lab log in this repo produced the number, with the date when the log has one.
- **[EST]**: an illustrative assumption this repository already marks as [EST]. Not a wage, a quote, or a fee.
- **not measured**: this repository does not have the number.

No new **[SYN]** volume is introduced below. The 2,000 calls and the 40% slice are the assumptions already written in [COST.md](COST.md). Where a figure is absent, the cell says not measured.

## Buyer and problem

The buyer in these docs is a front desk at a small outpatient clinic. The problem, from the README: the desk spends time on hours, prices, coverage, and bookings, and loses trust if the line records people who have not agreed, or if it gives clinical advice. The narrow question is whether a voice agent can take the routine slice without taking a name, a national ID, or a phone number before an explicit yes.

This repository is the lab for that pattern (phase 0 in the README rollout). It is not a clinic's system of record. The "booking" is a sentence. There is no dialer, no schedule database, and no phone number.

## Value levers

Two levers, each tied to something the lab actually contains:

1. **Consent compliance risk.** The caller should hear that the call is recorded and that an AI processes it before any personal data, and should be able to say no and still get hours, prices, coverage, and the address. On the logged suites that gate failed once: CD09 failed 1 of 3 logged runs across v15–v17, and on the failing run the agent asked for a name, a national ID, and a phone number with no explicit yes. That is MEASURED, small n, SIMULATED. v18 adds a re-ask before the first field. That re-ask is UNVERIFIED. The post-call field `consent_given` is a label. It does not block the question.
2. **Receptionist time.** The [EST] model in [COST.md](COST.md) prices a slice of hours, price, coverage, and booking calls against an illustrative loaded minute. Containment and the wage were not measured on a desk. The sign of the ROI flips when either assumption changes.

The model does not own the disclosure, the field list, or the emergency path. [DISCOVERY.md](DISCOVERY.md) is the question list for a real desk. Phase 1 and later in the README stay design only.

## Baseline and target KPIs

Baselines this repository never collected from a desk are marked not measured. Targets that are only the lab gate are not clinic targets.

| KPI | Baseline | Target | How | Label |
| --- | --- | --- | --- | --- |
| Personal fields before an explicit yes | 1 failing CD09 run out of 3 logged runs, v15–v17 | 0, on a pre-registered sample | [tests/RESULTS.md](../tests/RESULTS.md) | MEASURED 2026-10-21, small n, SIMULATED. Target not met. v18 UNVERIFIED |
| Simulation suite, latest full run | v15 was 8/10. v16 was 9/10 | v17 was 8/10 | Same log | MEASURED 2026-10-21. An LLM played the caller and an LLM graded the call. Not a listening panel |
| English replies over two sentences | CD08 failed on v15, v16, and v17 (3–4 sentences, and payment methods on the later fails) | The two-sentence cap holds | Same log | MEASURED. Not met |
| Emergency calls that request data | CD03 passed on the logged suites | Still 0 | Same log | MEASURED, SIMULATED, small n. Not a clinical trial |
| Server-side F0 by turn, same sentence, v4 turbo expressive | V0: 211.4, 210.4, 214.7 Hz | No position effect | `evidence/ab/measurements.csv` | MEASURED 2026-10-21. This sample shows none |
| v3 first-turn warm-up | V2: 197.6 Hz, then 183.6 and 182.5 Hz | Documented | Same CSV | MEASURED 2026-10-21. Not "fixed" |
| Package tests offline | 100 passed, 97.42% line coverage, Python 3.12.3 | Stay green with `LIVE_ENABLED` unset | `python -m pytest` | MEASURED 2026-10-22. Coverage of the Python package, not of the agent |
| Calls a month, and the share that is hours, price, coverage, or booking | Not collected | The model uses 2,000 calls and a 40% slice (800 calls) | [COST.md](COST.md) | **[EST]** |
| Minutes a contained call might avoid | Not measured | 4 minutes in the conservative case; 5 minutes in the higher case | Same note | **[EST]** |
| Illustrative loaded minute | Not a wage in this repo | USD 0.15 per minute conservative; USD 0.30 per minute in the higher case | Same note | **[EST]** |
| Illustrative monthly benefit | Not measured | USD 120 conservative; USD 720 higher containment | See the ROI model | **[EST]** |
| Counsel review of the disclosure | — | Not done | README governance | UNVERIFIED as a legal control |
| Live invoice from this lab, in currency | — | Not set | Credits are logged. They are not converted to currency here | not measured |

Do not quote 8/10 outside those SIMULATED runs. The README says the same.

## ROI model

Every input below is an **[EST]** assumption already written in [COST.md](COST.md). This note does not change them.

Shared assumptions:

- 2,000 inbound calls a month. **[EST]**
- 40% are hours, price, coverage, or booking. That is 800 calls. The other 60% stay with a person. **[EST]**
- The agent answers all 800, at 3 minutes each, at USD 0.08 per minute. **[EST]**
- Platform cost = 800 × 3 × 0.08 = **USD 192 per month**. **[EST]**

Scenario A, conservative:

- 25% of the 800 are contained. That is 200 calls. **[EST]**
- 4 minutes of front-desk time avoided on each, at USD 0.15 per minute. **[EST]**
- Benefit = 200 × 4 × 0.15 = **USD 120 per month**. **[EST]**
- Net = 120 − 192 = **−USD 72**. **[EST]**
- ROI = (120 − 192) / 192 = **−37.5%**. **[EST]**

Scenario B, higher wage and higher containment:

- 60% of the 800 are contained. That is 480 calls. **[EST]**
- 5 minutes avoided, at USD 0.30 per minute (overtime or a scarce desk, not a normal wage). **[EST]**
- Benefit = 480 × 5 × 0.30 = **USD 720 per month**. **[EST]**
- Net = 720 − 192 = **USD 528**. **[EST]**
- ROI = 528 / 192 = **275%**. **[EST]**

The sign flips. This repo did not measure containment or a wage. A one-time build cost is not estimated. This repo has no timesheet. Counsel for the disclosure, a tool-side consent check, and a phone integration are separate work, and they are not in the USD 192. If the 4-minute or 5-minute assumption is wrong, the USD 120 and USD 720 figures are wrong. This repository does not charge a fee.

What would have to be true, from the README rollout: the desk agrees the spoken notice and the four-field list; a human is still the live handoff; "booked" stays a sentence until a tool refuses a field unless consent is true. That tool is not in this repo. CD09 is why that matters.

## Cost table

| Item | Figure | Label |
| --- | --- | --- |
| Default path: venv, ruff, mypy, pytest, `secretscan`, `measure`, `about` | 0 USD | MEASURED. Those commands do not call the API and add no credits. No key. See the README quickstart and [COST.md](COST.md) |
| Docker smoke image (`about` only) | 0 USD | MEASURED as a local build. It does not install the audio extra and does not call the API |
| Live probe and simulation suites | Credits, not a currency invoice | MEASURED counts are in [COST.md](COST.md). This repo does not convert them |
| Full 10-test suite | about 3,700–4,600 credits | MEASURED |
| Suites v15–v17 together | about 12,700 credits | MEASURED |
| WebSocket A/B | about 1,884 credits | MEASURED |
| One simulation test | 160–750 credits | MEASURED |
| v18 check | 0 credits charged; insufficient credits | MEASURED. Not an evaluation |
| Phone number | not purchased | MEASURED |
| Platform cost in the planning model | USD 192 per month for the 800-call slice | **[EST]** |
| Conservative monthly benefit | USD 120 | **[EST]** |
| Higher-containment monthly benefit | USD 720 | **[EST]** |
| Integration, counsel, or staffing to adopt the pattern | Not in this repository | not measured |

Telephony per minute and per number are not priced here. Detail stays in [COST.md](COST.md).

## Measurement plan

Phase 0 is this repository. The commands that produce the MEASURED package rows are:

- `python3 -m pytest` with coverage. The 2026-10-22 local result is 100 passed, 97.42% line coverage, Python 3.12.3. The floor is 85% line coverage of `consent_lab`.
- `python3 -m consent_lab measure --root evidence/ab` for the committed WAV table. A unit test recomputes the CALM rows from those files.
- `python3 -m consent_lab secretscan .` for the pattern scan. A clean scan is not a proof that no secret exists. Recall is not measured.
- `python3 -m consent_lab about` for the version line. `live_enabled=false` when `LIVE_ENABLED` is unset.

The simulation scores are historical. Pytest does not call the model. A new simulation needs an account and credits. `LIVE_ENABLED=1` is the only value that opens the probe, and that path spends credits. It is not part of pytest.

Phase 1 (a test page only, no patient audio stored here) is design only. The exit in the README is a pre-registered sample with zero personal fields before a yes. Not met.

Phase 2 (a booking tool that rejects fields unless consent is true) is design only. The exit is a test that fails when the check is removed. Not built.

## Risks

Owners below are roles. In this lab the owner of record is the repository owner. The rows that most directly touch the value story are copied from [RISKS.md](RISKS.md):

| Risk | Why it matters to the value story | Where |
| --- | --- | --- |
| The consent rule fails open | The compliance lever is a prompt. CD09 already failed once. v18 is UNVERIFIED. There is no tool that refuses the field | [RISKS.md](RISKS.md), `agent/system_prompt.md` |
| A longer prompt is treated as a fix for length | CD08 still answers in 3–4 sentences. Receptionist-time value assumes the call stays short | [RISKS.md](RISKS.md) |
| The [EST] model is used as a quote | The ROI changes sign between −37.5% and 275% under the stated assumptions | [COST.md](COST.md) |
| The disclosure is treated as legal clearance | The prompt cites Act 25.326. No counsel reviewed the wording | [RISKS.md](RISKS.md). UNVERIFIED |
| Credits run out mid-check | The v18 attempt charged 0 credits and is not a pass | [RISKS.md](RISKS.md) |
| Vendor or model change | The logged suites are one model, one temperature, a few runs | [RISKS.md](RISKS.md) |

## Measured and not measured

**MEASURED in this lab**

- Simulation scores on 2026-10-21: v17 was 8/10, v16 was 9/10, v15 was 8/10. CD09 failed 1 of 3 logged runs across v15–v17. CD08 failed on v15, v16, and v17. SIMULATED caller and grader.
- v18 CD09 and CD10 attempt: 0 credits charged. Not an evaluation. UNVERIFIED.
- Acoustic table in `evidence/ab/measurements.csv` (2026-10-21), including V0 at 211.4, 210.4, and 214.7 Hz, and V2 at 197.6, then 183.6 and 182.5 Hz.
- Credit counts in [COST.md](COST.md), including about 3,700–4,600 credits for one full 10-test suite, about 12,700 for v15–v17, and about 1,884 for the WebSocket A/B. Not a currency invoice.
- Phone number: not purchased.
- Package tests on 2026-10-22: 100 passed, 97.42% line coverage, Python 3.12.3. The default path spends 0 USD.
- Probe refusal when `LIVE_ENABLED` is not `1`: the refusal tests. No request is sent.

**Not measured here**

- Minutes saved on a real desk, containment, and any wage.
- A currency conversion of the credit log.
- A build cost, counsel, or a phone integration.
- Whether v18's re-ask holds. The rerun did not finish.
- Behavior on another model, another temperature, or a larger sample.
- Compliance with a personal-data statute. The prompt cites one. No counsel reviewed the wording.
