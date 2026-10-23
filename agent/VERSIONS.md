# Versions

Each file in `history/` is the state **before** the change named in its suffix. IDs, account data and the inline prompt text are stripped from the configs. The prompt for each version is the `.md` file next to it. Those files are the English text of the prompts. The 2026-10-21 suites ran the Spanish wording. The scores were not recomputed.

| File prefix | Change that followed |
|---|---|
| v01 | Initial prompt. v2 then added "never greet again" and "no repeated emotion tag". |
| v04 `pre_polish` | Polish round: number normalization fix, audio-tag descriptions, two-sentence cap, English preset, ASR keywords |
| v06 `pre_cd08fix` | English two-sentence templates |
| v07 `pre_stability` / `pre_goodbyefix` | Voice set to Agustina, stability 0.35; one goodbye after silence |
| v08 `pre_firstmsg` / `pre_consent` | Short first message with notice, interruptions disabled, strict explicit-yes consent, CD09 added |
| v09 `pre_stability050` | Stability 0.35 → 0.50 (start-of-call voice complaint) |
| v10 `pre_greetingfix` | Notice moved from the first message to the first LLM reply |
| v11 `pre_calmconsent` | Calmer greeting and consent wording |
| v12 `pre_nofixedtext` | Empty first message, consent as a plain rule, LLM-generated filler |
| v13 `pre_audit` | Consent section reduced to the rule; uniform style |
| v14 `pre_firstmsg` | Recording notice back in a short first message (the audio issue was traced to the web client) |
| v15 `pre_fix1`, v16 `pre_fix2` | Fix rounds 1 and 2 (see tests/RESULTS.md) |
| v17 `pre_cd09fix` | Explicit-yes check before the first data field (v18, current) |
