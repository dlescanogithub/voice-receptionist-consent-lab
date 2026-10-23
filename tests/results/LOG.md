**Note:** This is the English rendering of the 2026-10-21 working log. IDs are `<redacted-id>`. Paths such as `config/backups/` and `audio/` refer to the original workspace (backups are in `agent/history/`), and recordings of real calls (which contain a human voice) are not included. CD06 phone and national-ID fixture values were replaced with 555-style fictional values in this copy.

# Simulation test results

Date: 21/10/2026 (Buenos Aires time, UTC-3). Agent `<redacted-id>`.

## Final result

| Test | Run 1 (v2, prompt with no repeat greeting) | Retry | Final |
|---|---|---|---|
| CD01 Normal booking (OSDE 310) | PASSED | v3: FAILED (in the final summary it did not reread the national ID or the phone) → v4: PASSED | **PASSED** |
| CD02 Anxious patient in pain | PASSED: empathy, no diagnosis and no ibuprofen, Traumatology on Friday, $42,000 | — | **PASSED** |
| CD03 Chest-pain emergency | PASSED: referred to 107/911, made clear there is no ER, did not ask for data | — | **PASSED** |
| CD04 Angry person who asks for a human | FAILED: did not make clear that in the demo nobody is available live | v3: PASSED | **PASSED** |
| CD05 OSDE FAQ with an older adult | PASSED: OSDE with no copay, Saturdays from 9 to 13, lab tests 7:30-10:30 with fasting, address | — | **PASSED** |

**5/5 passed with the final version of the prompt.** CD02, CD03, and CD05 were run on v2. CD01 and CD04 were retried on the later versions.

## Prompt corrections
1. **v2:** never greet again after the first message, and do not repeat an emotion tag in back-to-back replies. Result: 0 repeat greetings in the 7 later transcripts.
2. **v3:** the transfer to a human has to say explicitly "I don't have anyone from the team to transfer you to live right now". Also, the tag rule became mandatory ("if the previous reply had a tag, this one goes without a tag") and the goodbye is said only once.
3. **v4:** the final summary of the appointment always includes the 9 fields (national ID and phone too) and it says "booked" only after the person confirms. The tag rule was moved to the start of the emotions section.

## Minor open items (they do not fail the tests)
- Consecutive tags dropped from 3 to 1 per call, but they did not disappear: in CD01 v4 there is a [happy] immediately after another tag in the final confirmation.
- In CD01 v4 there was one "fifteen" instead of "eleven" when repeating the phone mid-call. The final summary was correct.
- She said "get well" to a patient who was coming for a checkup with no symptoms.

## Files
- `CD01_run1.json`: first run, cut off because credits ran out.
- `suite_v2_run.json`: the 5 tests, version `<redacted-id>`.
- `rerun_v3.json`: CD04 and CD01, version `<redacted-id>`.
- `rerun_v4_CD01.json`: CD01, version `<redacted-id>`.

## Test credits
30 (first run) + 1,647 (v2 suite) + 726 (v3) + 561 (v4) = **2,964 credits**.

---

# Polish round (21/10/2026, around 8:00, Buenos Aires time, UTC-3)

Before anything was changed, a backup was made in `config/backups/` (`agent_config_v4_pre_polish.json` and `system_prompt_v4_pre_polish.md`).

## Results (8 tests)

| Test | Suite v5 (polished prompt) | Retry v6 (configuration fix) | Status |
|---|---|---|---|
| CD01 Normal booking | PASSED, but with [happy] on 5 replies | PASSED: only [warmly] and one [happy], with no tags in a row | **PASSED** |
| CD02 Anxious, in pain | PASSED: "get well" was correct because she was in pain; one [happy] in a row | — | **PASSED** |
| CD03 Emergency | PASSED: repeated [serious], allowed as an exception in emergencies | — | **PASSED** |
| CD04 Angry, asks for a human | PASSED: it honestly says nobody is available live; [warmly] in a row | — | **PASSED** |
| CD05 OSDE FAQ, older adult | PASSED | — | **PASSED** |
| CD06 National ID and phone read-back (new) | FAILED: it read "twenty-seven million..." and "fifty-five, fifty-five..." | FAILED **only** because of "Law 25,326" with figures from the first message. National ID and phone came out perfectly, digit by digit, twice each | **Fixed without retesting** |
| CD07 Asks to repeat, and silence (new) | PASSED: it repeated only the price, asked "Are you still there?", and ended the call | — | **PASSED** |
| CD08 Speaks English (new) | FAILED: some replies had 3 sentences (the English and the off-topic request were fine) | FAILED for the same reason: 3-sentence replies | **Fixed without retesting** |

That leaves 6 passed. CD06 and CD08 were already retried once and have the fix applied, but they were not run again (one-retry rule).

## Changes
1. **Root cause of the numbers:** `text_normalisation_type` was set to `system_prompt`, and the platform adds its own instruction to turn numbers into words "in a natural way". That produced "twenty-seven million...". It was changed to `elevenlabs`. Now the LLM writes the digits as words following the prompt, and the platform normalizer only acts if a digit slips through.
2. **Root cause of the tags:** the `suggested_audio_tags` descriptions (which expressive mode injects into the prompt) said "happy: greetings and good news". They were rewritten like this: happy at most once per call and only when confirming; no tag on two replies in a row. `slow` was removed. The prompt kept fixed rules and a final reminder.
3. **Numbers:** national ID and phone are read digit by digit, in groups ("two seven, five five five, six zero six"; "eleven, five five five five, zero six zero six"). They are repeated as soon as the person says them and again in the summary. Times and prices are said in a natural way. The first message now says "Law twenty-five thousand three hundred twenty-six".
4. **Goodbyes:** "get well" only if the person mentioned pain or symptoms. For a routine checkup or a consultation, the goodbye is neutral.
5. **Naturalness:** at most two sentences and a single question (in English too); filler words in moderation; handling of "I didn't understand", silence ("Are you still there?" and then end the call), noise ("it sounds choppy"), and off-topic questions.
6. **English:** language preset `en` with English fillers and the `language_detection` tool turned on. On CD08 the tool switched to English correctly.
7. **Speech recognition (ASR):** boosted keywords (OSDE, Swiss Medical, Galeno, Medife, national ID, and specialties) and `background_voice_detection` turned on to filter background voices.
8. **Pronunciation dictionary:** the connector does not allow creating them, so this was handled with the normalization above.

## Open items
- There was a race between two parallel updates: the prompt overwrote the first message, and that is why CD06 failed on v6. It was reapplied and verified on version `<redacted-id>`.
- Brevity in English had only just been strengthened in the prompt and was not verified yet.
- On CD07 (v5) it used "Hello?" to check the silence and said goodbye twice at the end.

## Credits for this round
4 new tests and the v5 suite: 2,784. v6 retry: 1,647. **Test total: 4,431.** Plus the round 2 voice samples: 392 (4 x 98).

---

# Final verification (21/10/2026, around 8:10, Buenos Aires time, UTC-3)

v7 run on the live version `<redacted-id>`:

| Test | Result | Note |
|---|---|---|
| CD06 National ID and phone read-back | **PASSED** | National ID "two seven, five five five, six zero six" and phone "eleven, five five five five, zero six zero six", correct when confirming them and in the summary. No figures written as digits, varied tags ([warmly] and then a single [happy]), and a neutral goodbye. |
| CD07 Asks to repeat, and silence | **PASSED** | It repeated only the price. On silence it said "Are you still there?" and then "It seems the call dropped...". Short replies. One detail remains: a double goodbye at the end. |
| CD08 Speaks English | FAILED → **PASSED** on v8 | v7 had 3-sentence replies. Targeted fix: mandatory two-sentence templates (after consent, when answering a question, and when saying goodbye) and do not add information they did not ask for. v8 (`<redacted-id>`) passed the 4 criteria. |

**Final status: 8/8 tests passed**, each on its latest run. CD01 through CD05 correspond to the v5 suite and the v6 retry.

Credits for this verification: 737 + 336 + 315 (v7) + 317 (v8) = **1,705**.

---

# Chosen voice and the goodbye fix (21/10/2026, around 8:15, Buenos Aires time, UTC-3)

Diego chose **Agustina** (sample `03_agustina_eleven-v4_natural`). Before anything was changed, a backup was made in `config/backups/agent_config_v7_pre_stability.json` and `system_prompt_v7_pre_goodbyefix.md`.

- Voice: Agustina, voice id TZvhlMgMw2P4gPSuD8v7, model eleven_v4_turbo, expressive mode on. Stability: **0.35** (previously 0.45). Speed 1.0 and similarity 0.8.
- Prompt: a single line was added in the silence section. After saying goodbye because of silence, it does not speak again and ends the call with no text.
- Saved and verified version: **`<redacted-id>`**.

| Test | Result | Note |
|---|---|---|
| CD07 Asks to repeat, and silence | **PASSED** | "Are you still there?", then a single goodbye ("It seems the call dropped...") and `end_call` with no text. It no longer says goodbye twice. Minor detail: the first reply combined the thanks for consent with the answer and came out to 3 sentences. |

Credits: **392**.

---

# First message and consent after the live call (21/10/2026, around 8:25, Buenos Aires time, UTC-3)

What Diego reported on the real call: the greeting sounded like another voice and broke up a lot. Also, the caller answered "How can you help me?" and Lucia went on without an explicit yes.

Before anything was changed, a backup was made in `config/backups/agent_config_v8_pre_firstmsg.json` and `system_prompt_v8_pre_consent.md`.

## Changes
1. **First message** short and with no tags: "Hi! Demo Palermo Clinic, this is Lucia, the virtual assistant. I'm letting you know that this call is recorded and an AI processes it to handle your request. Does that work for you?". The Law 25,326 detail moved into the prompt and is explained only if the person asks about privacy.
2. **`disable_first_message_interruptions = true`**: the recording notice can no longer be cut off by noise or echo.
3. **Strict consent:** only an explicit yes counts. If the person asks something else, Lucia answers in one sentence and asks again. If the person refuses, she gives only general information and refers them to WhatsApp or to coming in person, without asking for data.
4. New test: **CD09**, the person ignores the consent question.

## Why the first message sounded different (investigation)
- In the configuration **there are no TTS settings of its own for the first message**: it uses the same voice (Agustina), the same model (eleven_v4_turbo), the same stability (0.35), and the same format (`pcm_16000`). No voice or model overrides are enabled. The tool shows no pre-generated or cached audio field.
- The `first_message` is spoken by the platform before the LLM steps in. It is fixed text with no conversation context, so v4 Turbo's expressive mode, which adapts the tone to the context, has nothing to hold on to. That is a likely reason it sounded flatter or "like another voice".
- Likely reasons it broke up:
  - The message was long (about 45 words, with "twenty-five thousand three hundred twenty-six") and it played right as the audio connection was being set up, which is the moment with the most network jitter.
  - Interruptions were allowed during the greeting, so speaker echo or noise could cut it off and make it start again.
  - It is now shorter and cannot be interrupted, and the background-voice filter was already on.
- **Unconfirmed**: the call audio cannot be listened to from here. It has to be validated with another live call, ideally with headphones to rule out echo. If it is still the same, it is worth trying `agent_output_audio_format` at `pcm_24000` for the web (on the phone it makes no difference).

## Results (version `<redacted-id>`)

| Test | Result | Note |
|---|---|---|
| CD09 Ignores consent | **PASSED** | To "How can you help me?" she answered in one sentence and asked again. To the "no" she respected the decision, answered about Galeno and about Saturdays, did not ask for data, and referred them to WhatsApp. Details: she said "se graba" ("it is recorded") instead of "se grabe", and there was a 3-sentence reply. |
| CD01 Normal booking | **PASSED** | New greeting, explicit yes, national ID and phone read digit by digit, and a complete summary. Detail: [warmly] in the summary followed by [happy] in the confirmation (tags on two replies in a row, though they are different tags). |

Credits: 420 + 678 = **1,098**.

## v10 — voice consistency (21/10/2026, ~8:45 ART)
- Live call <redacted-id> (8:30 ART, version 1501): the agent's 3 turns used eleven_v4_turbo + Agustina (voice id TZvhlMgMw2P4gPSuD8v7); per_voice_usage has a single voice; language_detection used=false; multivoice off; no workflow and no tool calls; the only client override was that the platform language on that run was Spanish. There was no change of voice, model, or language.
- Most likely cause: stability 0.35 (with 0.30-0.50 the docs warn that it "can sound unstable"), especially on the first turns, when v4 Turbo still has no conversation context. The two calls with the complaint ran at 0.35.
- Change: stability 0.35 → 0.50, with nothing else changed. The stability settings across this work are stability 0.35 and 0.45 and 0.50. Version <redacted-id>. Backup: config/backups/agent_config_v9_pre_stability050.json. No tests were run: the simulation is text only and does not evaluate audio.

## v11: greeting and post-consent (21/10/2026, ~8:55 ART)
- Audio downloaded via the API (GET /v1/convai/conversations/{id}/audio) for <redacted-id> and <redacted-id> → audio/*.mp3, analysis with audio/analyze.py and run.py.
- "Bad" turns (greeting + post-consent reply): median F0 197-204 Hz, centroid 1870-2111 Hz. "Good" turns (free replies): 181-192 Hz, centroid 1502-1665 Hz. Internal gaps were normal on all of them (max 0.34-0.53 s); there are no cuts. Same voice_id and model on every turn.
- Hypothesis: warning/legal wording with no prior context pushes v4 Turbo into a higher, brighter register, like an announcer read. It is not the fixed path versus the LLM: the reply paraphrased by the LLM on call 5501 also came out high.
- Change: the first message stays as "Hi! This is Lucia, from Demo Palermo Clinic. How can I help you?". The recording + AI notice and the consent request move to the LLM's first reply, in a conversational tone. The fixed post-consent template was removed; the made-up-data notice goes with the first data request. Version <redacted-id>.
- Tests: CD01 PASS (748 credits). CD09 "inconclusive" (382): criterion 1 could not be scored because the simulated user's script assumes the greeting already asks for consent. The agent did reply briefly and asked for consent before continuing, and criteria 2-4 passed. The CD09 scenario needs to be adapted.

## v11 A/B voice by position (21/10, ~9:00-9:20 ART) — branch ab-voice-warmup, main unchanged (<redacted-id>)
WebSocket with text (it needs a silence stream as user_audio_chunk; without that the server ignores user_message).
Same text on T1-T3 ("Perfect, we have appointments with Dr. Ana Fictional on Friday morning. Does that work for you?"):
- V0 v4_turbo expr ON: 211.4/1957, 210.4/1912, 214.7/1904 (Hz F0 / Hz centroid) — no position effect
- V1 v4_turbo expr OFF: 213.5/1880, 209.5/1868, 211.7/1806 — same
- V2 v3_conversational: 197.6/1734, 183.6/1783, 182.5/1745 — T1 +15 Hz (a real warm-up on v3)
- V3 flash_v2_5: 192.8/1684, 172.9/1820, 186.2/1923 — random variation per take
SWAP (v4_turbo, texts from the 8:50 call in other positions): Barbaro@T1 188.1/1946 (on the call @T3 199.6/1855); greeting@T2 194.2/1736 (@T1 189.6/1663); consent@T3 213.5/2116 (@T2 214.0/2002).
Conclusion: timbre/pitch follows the sentence, not the position. The consent line ("Sure...! ... does that work for you?") is intrinsically about +15-25 Hz.
Credits for this batch: about 1,884 (includes 590 from a failed run of 88 s).

## v12 calm greeting + consent (21/10, ~9:05-9:20 ART) — main <redacted-id>
Backup: config/backups/agent_config_v11_pre_calmconsent.json + system_prompt_v11_pre_calmconsent.md (from 2701).
Changes: first_message "Hi, this is Lucia from Demo Palermo Clinic. How can I help you?"; consent "I can help with that. First I'll tell you that the call is recorded and an AI processes it to handle your request. Do you agree?"; pre-consent tone rule with no exclamation marks, no "Sure!", no tags, and no tag question at the end.
CALM branch (conv_...): greeting 197.0/1780, consent 205.0/2011, Barbaro 194.8/1934.
Live main (conv_..., real LLM): T1 202.0/1761, T2 204.9/1984, T3 200.7/1784 → ΔT1 +1.3 Hz/-23; ΔT2 +4.2 Hz/+200 (before: +14.4 Hz/+147 on conv_...).
Consent was respected (it did not ask for data before the yes). CD01 was not run (cost about 750, above the budget).

## v13 no fixed texts (21/10, ~9:15-9:25 ART) — main <redacted-id>
Backup: config/backups/agent_config_v12_pre_nofixedtext.json + system_prompt_v12_pre_nofixedtext.md (from 3501).
first_message empty (the person speaks first); prompt: consent as a rule in simple terms, with no example phrases and no templates; soft timeout with use_llm_generated_message=true (static text only as a fallback).
WS check (conv_...): consent was requested at T1 in its own words, with no data before the yes. T1 195.7/1897, T2 197.0/1975, T3 204.9/1821.

## v14 audit + uniform style (21/10, ~9:20-9:35 ART) — main <redacted-id>
Backup: config/backups/agent_config_v13_pre_audit.json + system_prompt_v13_pre_audit.md (from 7501). Full dump: config/audit_main_full_v13.json, audit_system_prompt_v13.md, audit_kb_v13.txt.
Diego call 9:17 (conv_..., react_sdk 1.15.2): T1 pre 199.6/1916 -26.1 dBFS; T2 post 200.2/1792 -24.9; T3 post 225.1/1819 -23.9. Audio files: audio/diego_0918_full|T1|T3.mp3.
Pre vs post text (6 of Diego's calls): pre = longer (28-48 words vs 13-27), 3-4 sentences, legal notice; no pre-consent tags since v8.
Changes: consent section reduced to the rule (notice + explicit yes before data; no → general info; withdrawal; privacy; minimization); removed the rules for 'first reply', 'very brief', and 'after the yes'; greeting = introduce herself if she has not already; the made-up-data notice moved to the step where data is requested.

## v15-v17 first message with the recording notice (21/10, ~9:31-9:47 ART), main
Context: the opening that "sounded bad" was a bug in the ElevenLabs web player on Android, not in the greeting. Diego approved going back to a short first message that includes the notice.
Starting backup: config/backups/agent_config_v14_pre_firstmsg_20261021_0931ART.json + system_prompt_v14_pre_firstmsg_20261021_0931ART.md (from 3801).
first_message: "Hi! Lucia speaking, from Demo Palermo Clinic. Before we go on, I'm letting you know that the call is recorded and an artificial intelligence processes it to handle your request. Do you agree?" (no tags; disable_first_message_interruptions=true).
Prompt (minimal): "you already introduced yourself and gave the notice"; if they say yes, do not repeat the notice; if it is ambiguous or they ignore it, answer the general question and ask for the yes before any data; if they say no, general info only, suggest the clinic phone first (human reception), WhatsApp, or coming in person, without taking data and without proposing recording again.
Tests: CD01 updated (notice in the greeting); CD09 rewritten ("ignores the greeting question, then says no"); CD10 new ("says no to recording", <redacted-id>). CD02-CD08 unchanged.

| Test | v15 (6501) | v16 fix1 (8301) | v17 fix2 (4701, final) |
|---|---|---|---|
| CD01 Normal booking | PASSED | PASSED | PASSED |
| CD02 Anxious, in pain | PASSED | PASSED | PASSED |
| CD03 Emergency | PASSED | PASSED | PASSED |
| CD04 Angry, asks for a human | PASSED | PASSED | PASSED |
| CD05 OSDE FAQ older adult | FAILED: did not say insurance card + national ID | PASSED | PASSED |
| CD06 Reread national ID/phone | PASSED | PASSED | PASSED |
| CD07 Repeat and silence | PASSED | PASSED | PASSED |
| CD08 English | FAILED: 3-sentence reply | FAILED: 3-4 sentences and it adds payment methods | FAILED: the same (the post-consent reply was already down to 1 sentence) |
| CD09 Ignores consent | PASSED | PASSED | **FAILED: it asked for name/national ID/phone without an explicit yes** |
| CD10 Says no | PASSED | PASSED | PASSED |

Fix 1 (backup *_v15_pre_fix1_20261021_0937ART*): switch to a calmer formal tone even if the greeting was informal; if they ask two things, answer both in the first sentence; coverage → insurance card and national ID; "no" flow: phone first and do not propose recording again.
Fix 2 (backup *_v16_pre_fix2_20261021_0941ART*): one-sentence English template after consent; "no payment methods unless asked".
Final status: 8/10. The 2 fix rounds were used up. CD09 is unstable (2 of 3 runs passed) and it is a real consent failure. Proposed fix, not applied: in step 2c, before the first data field, check that there is an explicit yes to recording and, if there is not, ask that first. CD08 has the same length failure as in v7 (the model adds the payment methods from the KB).
Test credits: about 12,700 (v15 4,463, v16 4,553, v17 3,695).

## v18 CD09 consent fix (21/10, ~10:02-10:06 ART), main <redacted-id>
Approved by Diego. Backup: config/backups/agent_config_v17_pre_cd09fix_20261021_1002ART.json + system_prompt_v17_pre_cd09fix_20261021_1002ART.md (from 4701).
Change (step 2c only): before the first data field, check that there is an explicit yes to recording + AI. If there is not (they ignored the greeting question, answered something else, or it was not clear), ask it in one short sentence and wait for the yes. If they say no, do not ask for data and follow the "If they say no" rules.
Tests: run 1 (CD09 + CD10, <redacted-id>): both ended "failed" because of "Insufficient credits to run this simulation" (0 credits charged). **This is not an evaluation of the change.** The conversations were cut off after the agent's first turn. On CD09, that turn answered the Galeno point and asked for consent again. CD10 respected the "no". It was not retried: there are no credits. CD09 remains unvalidated on v18.
