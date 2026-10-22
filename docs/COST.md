# Cost

Two different tables. Do not add them together.

## What the lab log recorded

These are credits on one account in October 2026, from `tests/RESULTS.md` and the README log. They are not a price list and they are not converted to currency here.

| Item | Amount | Label |
| --- | --- | --- |
| First five-test round (v2–v4) | 2,964 credits | MEASURED |
| Polish round (v5–v8), the three figures in the log | 4,431 + 1,705 + 392 credits | MEASURED |
| Suites v15, v16, v17 | 4,463 + 4,553 + 3,695 credits, about 12,700 | MEASURED |
| One full 10-test suite | about 3,700–4,600 credits | MEASURED |
| One simulation test | 160–750 credits, depending on turns | MEASURED |
| WebSocket A/B round | about 1,884 credits | MEASURED |
| v18 CD09 + CD10 attempt | 0 credits charged; the run stopped for insufficient credits | MEASURED |
| Phone number | not purchased | MEASURED |
| Monthly credit allowance that was used up | 30,000 credits | MEASURED as this account's plan observation, not a vendor quote |

The offline package tests add no credits. They do not call the API.

## Planning figures for a line this shape

Every number in this section is **[EST]**. None of it was measured on a desk. None of it is a quote. The sign of the ROI flips when containment or the loaded wage changes. Do not put these figures in a proposal without a local baseline.

Shared assumptions [EST]:

- 2,000 inbound calls a month.
- 40% are hours, price, coverage, or booking. That is 800 calls. The other 60% stay with a person.
- The agent answers all 800, at 3 minutes each, at USD 0.08 per minute.
- Platform cost = 800 × 3 × 0.08 = **USD 192 per month**.

Scenario A, conservative [EST]:

- 25% of the 800 are contained. That is 200 calls.
- 4 minutes of front-desk time avoided on each, at USD 0.15 per minute.
- Benefit = 200 × 4 × 0.15 = **USD 120 per month**.
- Net = 120 − 192 = **−USD 72**.
- ROI = (120 − 192) / 192 = **−37.5%**.

Scenario B, higher wage and higher containment [EST]:

- 60% of the 800 are contained. That is 480 calls.
- 5 minutes avoided, at USD 0.30 per minute (overtime or a scarce desk, not a normal wage).
- Benefit = 480 × 5 × 0.30 = **USD 720 per month**.
- Net = 720 − 192 = **USD 528**.
- ROI = 528 / 192 = **275%**.

A one-time build cost is not estimated. This repo has no timesheet. Counsel for the disclosure, a tool-side consent check, and a phone integration are separate work, and they are not in the USD 192.

Telephony per minute and per number are not priced here. No number was bought (MEASURED).
