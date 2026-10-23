# Discovery

Start here, not with a model name. The ten questions below are the Deployment Strategist pass for a clinic line that looks like this lab. The answers in this repo are the fictional clinic's, marked [SYN], or "not collected".

| # | Question | Why it matters | What this lab assumed |
| --- | --- | --- | --- |
| 1 | How many calls a week, and what share is hours, price, coverage, or booking rather than a clinical question? | Containment and the [EST] ROI both depend on this share. | Not collected. The [EST] model uses 2,000 calls a month and a 40% slice. |
| 2 | Which language and which variety? | A two-sentence cap failed on the English path (CD08, MEASURED). Formal versus informal address is a prompt rule that failed once (CD05 on v15) and then passed. | Clear English in this tree. The 2026-10-21 suites ran in Spanish. [SYN] clinic in Buenos Aires. |
| 3 | Is the call recorded today, and what does the current notice say? | The disclosure has to match the real practice. A prompt that says "we record" while the line does not, or the reverse, is a different problem. | The story says the call is recorded and an AI processes it. [SYN] |
| 4 | What counts as a yes? Is silence a yes? Is "I want an appointment" a yes? | CD09 exists because the second one was treated as a yes once. | Only an explicit yes. Silence and a change of subject are not a yes. |
| 5 | Where would a booking be written, and who owns that system? | This lab writes nothing. A retry cannot double-book because there is no book. | No system of record. Design only. |
| 6 | What is the emergency path, and is there an emergency room on site? | The prompt sends chest pain to 107 or 911 and takes no data. A clinic with an on-site emergency room needs a different sentence. | No emergency room. [SYN] |
| 7 | Is a human available live, or only a callback? | The prompt is required to say nobody is live before it asks for a callback. | Nobody is live. [SYN] |
| 8 | How long are audio and transcripts kept, and who can delete them? | The prompt mentions an access and deletion request. There is no store here to delete from. | Not collected. Design only. |
| 9 | Who may hear the recording: the clinic, a QA reviewer, the model vendor? | The spoken notice has to name that, in words a caller understands. | The notice says the call is recorded and processed by an AI to handle the request. It does not name a vendor retention period. |
| 10 | What is the rollback if a field is collected without a yes? | A prompt edit is not a rollback of data you already stored. | Stop the test page, do not keep the audio, restore the previous prompt from `agent/history/`. There is no database. See `docs/RUNBOOK.md`. |

Do not treat a finished discovery questionnaire as evidence that a clinic agreed to this design. No clinic was asked.
