# Task 5 implementation

`core/sentiment.py` classifies current text with recent history into the six required labels and reports an evidence confidence. It shares the existing LanguageProcessor, original entity protection, normalization, and dynamically enabled language resources. Sentiment, context patterns, independent risk rules, and tone prefaces live in `resources/languages/*.json`; thresholds, history size, repeated-negative count/window, queue names, and business calendar live in config. English emotion phrases after "I am" are no longer mistaken for personal names.

`core/risk.py:HighRiskDetector` never consumes the sentiment decision. Calm account compromise, duplicate payment, and legal-threat reports escalate even when language or intent confidence causes the chatbot to ask clarification. Injection-blocked turns still pass through this detector in the supported RAG orchestrator. Classification/escalation requires no network or LLM call.

`core/escalation.py` and `core/store.py:EscalationRepository` persist issue state and escalation records in SQLite before RAG generation. An atomic transaction stores masked recent conversation messages, trigger evidence, reason, episode, queue, schedule, timestamps, and status. Duplicate trigger records are suppressed within one unresolved episode, including concurrent callers and restarts. A later urgency upgrade moves open records to on-call routing without replacing their original trigger evidence.

Negative events are counted in the configured sliding window. The first unresolved negative event starts a Clock timer. The existing application worker polls escalation timers before maintenance jobs and session expiration. At exactly 15 minutes no timeout record is created; strictly after it, the timer creates one record even without another message, after session expiry, or after process restart. A policy reply or positive message never closes an issue. Support agents explicitly resolve issues with a recorded reason; new issues can escalate in later episodes.

Routing uses the configured timezone, start-inclusive/end-exclusive business hours, workdays, and holidays. Triggered urgent/high-risk issues outside hours go to the on_call queue immediately. Normal triggered complaints outside hours are scheduled at opening on the next working date, skipping weekends and holidays. The records are local queue entries; no external human notification is claimed.

`core/tone.py` implements presentation only: the API's existing `answer` and citations remain the verified policy body. New `tone_prefix` and `display_answer` fields offer localized empathy without modifying that body. Tests diff actual RAG-generated, localized policy answers with tone enabled and disabled in all four configured languages. The existing conservative lexical RAG sometimes refuses long emotional wording; this task does not weaken its similarity or grounding thresholds to force an answer.

## API

- `POST /query`: existing payload and role/session ownership; adds sentiment (label/confidence/evidence/language), high_risk, escalations, tone_prefix, display_answer.
- `GET /escalations`: requires a valid key with ticket:manage; returns persisted queue records and masked summaries.
- `POST /escalations/{session_id}/resolve`: requires ticket:manage; body contains generation and a nonempty reason. Resolves records and stops the episode's timer. Unauthorized requests are rejected and audited.

## Authored evaluation

Command: `.\.runtime\python311\python.exe -X utf8 scripts/evaluate_t5.py`.

Actual result: 52 correct / 60 examples, accuracy 0.8666666666666667. Each of en, hi, te, es scored 13/15. Eight implicit complaints or sarcastic expressions were predicted neutral; their unchanged labels and failed predictions remain in `docs/verification/t5-classifier-evaluation.json`. This is a diagnostic authored set, not independently blinded or production accuracy. Scores are evidence confidence, not calibrated probabilities.

Dataset: `tests/fixtures/task5/labelled_sentiment.json`. SHA-256: `4b01d4253747dfd0530c46220cb758d63e1c7b52ac92ea8080ef21e8974454e9`. Local commit: `681aedc2761e861458e43e72a1d81c47928bffee`, containing only the labelled dataset and its provenance README. No remote or secret is included.

Offline demonstration command: `.\.runtime\python311\python.exe -X utf8 scripts/demo_t5.py`. Actual output is in `docs/verification/task5-demo.json`: neutral account compromise routed on-call, repeated negatives and history sarcasm, unchanged cited refund facts with a separate preface, and timers at 901 elapsed seconds. Friday after-hours normal complaints skip the weekend and configured Monday holiday to Tuesday 2026-10-20 09:00 +05:30. FakeClock latency samples are zero because simulated time does not advance while code executes; they are not real performance measurements.

Scope assumptions: `docs/task5_assumptions.md`. Requirement coverage and captured full-suite output: `docs/RTM.md`, `docs/verification/pytest-task5.txt`.
