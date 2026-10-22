# Risks

| Risk | What was seen | What this repo does | What is still open |
| --- | --- | --- | --- |
| The consent rule fails open | CD09 failed 1 of 3 logged runs across v15–v17. On the failing run the agent asked for a name, a national id, and a phone number with no explicit yes. MEASURED, small n. | The rule is in the prompt. v18 adds a re-ask before the first field. | v18 is UNVERIFIED. There is no tool that refuses the field. |
| A longer prompt is treated as a fix | CD08 still answers in 3–4 sentences and adds payment methods. MEASURED on v15, v16, and v17. | The two-sentence cap and a one-sentence English template are in the prompt. | The failure remains. Moving payment methods out of the default context is not done. |
| A playback bug is "fixed" by editing the voice | Four rounds of prompt and stability changes did not change what the tester heard in the web page. Server-side F0 on `eleven_v4_turbo` with expressive mode did not depend on turn position (V0: 211.4, 210.4, 214.7 Hz). MEASURED. | The package recomputes that table offline. | The pitched-up start was heard only in the web client. Linking it to a specific SDK issue is UNVERIFIED. |
| Credits run out in the middle of a check | The v18 CD09/CD10 run stopped with insufficient credits. 0 credits charged. MEASURED. | The probe and the docs say the live path spends credits and is off by default. | A failed run from an empty balance is not a pass and not a fail of the behavior. |
| Emergency or diagnosis rules are only words | CD02 and CD03 passed on the logged suites. MEASURED, small n, SIMULATED caller and grader. | Prompt text plus post-call criteria. | No blocking guard. A paraphrase can still get through. Not a clinical trial. |
| The agent id is the credential | Platform authentication was off in the exported config. | Ids are not in the repo. The probe reads them from the environment and does not log them. | A real deployment would turn authentication and an origin allowlist on. Not done here. |
| Logs or a CSV copy a secret | The signed URL is a bearer for one session. | Logs record `signed_url_fetched`, not the URL. The CSV keeps the agent text and the acoustic numbers. `secretscan` flags key shapes. | A future edit can regress this. The scan is a test, not a guarantee. |
| The disclosure is treated as legal clearance | The prompt cites a personal-data statute and speaks the notice. | The notice is in the first message, with interruptions off. | No counsel reviewed the wording. UNVERIFIED as a legal control. |
| Vendor or model change | The logged suites used one model, one temperature, and a few runs. | The results table says so. | A new model is a new sample. These pass rates do not transfer. |
| Cost model used as a quote | The [EST] ROI changes sign when containment or the loaded wage changes. | Both scenarios are in `docs/COST.md`, with the arithmetic. | No local baseline was measured. |

The honest summary: the failure mode that matters is a prompt that asks for a personal field without a yes, and this lab has already seen it once. The package does not close that hole.
