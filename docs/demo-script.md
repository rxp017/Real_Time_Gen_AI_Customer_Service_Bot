# Demo video: 3–4 minutes

Use synthetic customers, the fixture invoice and a private customer role key. Hide credentials in the recording. Record the exact commit and whether the provider is live, rate-limited or intentionally offline. Do not present scripted demo output as live generation.

| Time | Action | What to explain |
| --- | --- | --- |
| 0:00–0:25 | Show README architecture and mentor attribution | Original FAQs are preserved and imported with metadata; six tasks share Clock/config/security/store. |
| 0:25–1:00 | Send a supported FAQ and an unsupported question in `/` | Show an actual citation if produced. If quota/evidence blocks it, show the refusal. Point out actual answer language and source answer when translated. |
| 1:00–1:40 | Upload `clean.png`, then `mismatched.png` from `tests/fixtures/task2/` with original order/date/amount | OCR extracts visible fields; conflicts ask clarification. Optionally show `blurred.png` requesting replacement. |
| 1:40–2:15 | Request a ticket, supply synthetic mandatory fields, submit and refresh | A draft asks for missing fields. A completed ticket queues when no agent is eligible. No external notification delivery is implied. |
| 2:15–2:50 | Run `scripts/demo_t1.py` | Explicitly label FakeClock/FakeLLM. Show measured golden results, maintenance-window activation and health rollback. |
| 2:50–3:25 | Show frozen corpus hashes, report metrics and CI jobs | Retrieval 3/20 correct cited answers and 0/52 false answers; sentiment 22/48 with six provider decisions. Explain pattern fallback and live translation HTTP 429. |
| 3:25–3:50 | Show Render guide and limits | One worker and persistent storage are needed. Free hosting sleep stops timers; ephemeral files can disappear. Show a live URL only after deploying and checking it. |

Keep the recording between two and five minutes. The delivered artifact is this recording script; no video or public deployment is claimed.
