# Current audit - 2026-10-15

The latest audit found requirements that remain partial despite passing named tests. See [the fresh public-clone recheck and raw outputs](audit-recheck.md), [earlier fixes and findings](audit.md), [every sentence and RTM row](audit-rtm.md), and [verbatim gaps/assumptions](audit-disclosures-verbatim.md).

Rechecked original checkout: 282 passed, 1 warning in 63.88s (0:01:03). Anonymous public clone installed using README only: 282 passed, 1 warning in 61.39s (0:01:01). Ruff and dependency checks pass. Live generation remains unconfigured in the fresh example environment.

The historical task reports below retain their original dates and outputs.

---

# Task 3 current verification - 2026-10-15

Task 3 extends the existing chatbot with owner-bound ticket drafts and explicit customer questions, configurable weighted priority, routing by skills/availability/workload, business-calendar SLA warnings and escalation, runtime SLA recalculation, duplicate merging, related groups and masked handoff summaries. It reuses shared Clock, config, SQLite, security, audit, metrics, session summaries and the history-aware sentiment classifier.

[Ticket API and operational setup](task3.md) · [Priority formula](priority.md) · [RTM](RTM.md) · [Known limits](known_gaps.md).

The production agent roster is intentionally empty; configure actual agents under `tickets.agents`. Missing customer fields remain drafts. Escalation queues/events are local durable records, without an external helpdesk/notification transport.

## Actual full pytest output

```powershell
.\.runtime\python311\python.exe -X utf8 -m pytest -q
```

```text
........................................................................ [ 26%]
........................................................................ [ 52%]
........................................................................ [ 78%]
..........................................................               [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
274 passed, 1 warning in 62.04s (0:01:02)
```

Task 3 defines 26 tests, including all 12 required named scenarios. The full suite above includes earlier tasks. The existing Starlette/httpx deprecation warning is retained.

## Lint and dependency checks

```powershell
.\.runtime\python311\python.exe -m ruff check .
.\.runtime\python311\python.exe -m pip check
```

```text
All checks passed!
No broken requirements found.
```

## Actual offline demo output

```powershell
.\.runtime\python311\python.exe -X utf8 scripts/demo_t3.py
```

```text
Draft: DRAFT Please provide: customer, order, product, evidence, contact.
Ticket: QUEUED no_eligible_agent
Handoff contact masked: True
SLA due: 2026-10-20T12:30:00+05:30
Duplicate merged: True requests: 2
After weekend + Monday holiday: 180.0 business minutes
Warning: True
Configured demo agent: ASSIGNED demo-agent
Breach: True escalated: True
Events: duplicate_merged, sla_warning, queue_escalation, assigned, sla_breach
```

This demo uses FakeClock and synthetic customer/agent data in temporary in-memory storage. It establishes local workflow behavior, not human notification delivery or general classifier accuracy. Raw evidence is saved under `docs/verification/*-task3.txt`.

---

# Task 2 prior verification - 2026-10-15

Task 2 is implemented in the existing FastAPI application with shared Clock, SQLite, RBAC, masked audit, metrics, injection detection and LLMClient. Uploads pass structural safety checks before content decoding. Actual Tesseract/PDFium produce explicit fields with confidence and regions; mismatches ask clarification, missing fields remain null, and poor quality requests a replacement. Background job notifications/results are retrieved by the same authenticated owner. Expiry purges original bytes and stored content, including results from in-flight jobs.

[Task 2 design, API and installation](task2.md) · [Requirements trace matrix](RTM.md) · [Known limits](known_gaps.md).

## Actual full pytest output

Command:

```powershell
.\.runtime\python311\python.exe -X utf8 -m pytest -q
```

```text
........................................................................ [ 29%]
........................................................................ [ 58%]
........................................................................ [ 87%]
................................                                         [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
248 passed, 1 warning in 53.07s
```

Raw evidence: [pytest-task2.txt](verification/pytest-task2.txt). All eight required Task 2 test names exist. The complete suite includes Tasks 1, 4, 5, 6 and provider fallback. The existing Starlette TestClient warning is preserved. On this host, execution outside the sandbox was required because asyncio's local socketpair was blocked; pytest itself used no external network and its provider credentials were cleared.

Command: `.\.runtime\python311\python.exe -m ruff check .`

```text
All checks passed!
```

Command: `.\.runtime\python311\python.exe -m pip check`

```text
No broken requirements found.
```

## Actual installed OCR evidence

Command: `.\.runtime\python311\python.exe -X utf8 scripts/check_ocr.py`

```json
{
  "executable": "C:/Program Files/Tesseract-OCR/tesseract.exe",
  "version": "tesseract v5.4.0.20240606",
  "available_languages": [
    "eng",
    "hin",
    "spa",
    "tel"
  ],
  "required_languages": [
    "eng",
    "hin",
    "tel",
    "spa"
  ],
  "missing_languages": []
}
```

Raw evidence: [task2-ocr-installation.json](verification/task2-ocr-installation.json). Installer verification, language-pack hashes and reproducible install commands are documented in [task2.md](task2.md). OCR/PDF fixtures are actual files under tests/fixtures/task2; no extracted fields in these tests are fabricated by FakeLLM. Native-operation libraries are verified and pinned. Windows application control blocked PyMuPDF; it was removed and the working PDFium adapter used instead.

## Actual file outcomes

Command: `.\.runtime\python311\python.exe -X utf8 scripts/demo_t2.py`

Outcome fields copied from the executed offline demo:

```json
[
  {
    "fixture": "clean.png",
    "status": "extracted"
  },
  {
    "fixture": "clean.jpg",
    "status": "extracted"
  },
  {
    "fixture": "clean.pdf",
    "status": "extracted"
  },
  {
    "fixture": "scanned.pdf",
    "status": "extracted"
  },
  {
    "fixture": "blurred.png",
    "status": "request_new_file"
  },
  {
    "fixture": "mismatched.png",
    "status": "clarification_required"
  },
  {
    "fixture": "missing.png",
    "status": "extracted"
  },
  {
    "fixture": "injected.png",
    "status": "rejected"
  },
  {
    "fixture": "injected.pdf",
    "status": "rejected"
  },
  {
    "fixture": "injected-scan.pdf",
    "status": "rejected"
  },
  {
    "fixture": "hidden-injected.pdf",
    "status": "rejected"
  },
  {
    "fixture": "active.pdf",
    "status": "rejected"
  },
  {
    "fixture": "malformed.png",
    "status": "rejected"
  },
  {
    "fixture": "product.png",
    "status": "cannot analyse"
  },
  {
    "fixture": "product-no-text.png",
    "status": "cannot analyse"
  }
]
```

The [full output](verification/task2-demo.json) contains actual confidence, regions, quality evidence, missing nulls, and document/customer conflict values. This demo explicitly disables vision to exercise its unavailable branch. No general OCR accuracy percentage is claimed.

## Separate real image-provider smoke check

Command: `.\.runtime\python311\python.exe -X utf8 scripts/check_live_task2_vision.py`

Actual configured model: `gemini-2.5-flash`. Actual result status: `analysed`. Observed total duration including OCR: `8300.09519999976` ms. The actual provider description is retained in [task2-live-vision.json](verification/task2-live-vision.json); it correctly says the text-only fixture depicts no physical product. Missing order/date/amount/error fields stay null. This establishes one real image request/response, not broad product recognition, invoice authenticity, performance guarantees, or deployment.

Product uploads reuse the existing Gemini key/model by default. With no configured/usable capability the API returns cannot analyse; image fallback only selects configured vision-capable models. Provider credentials were never printed or changed. Completion notification delivery uses the job polling endpoint; no external push/email service is configured.

Earlier task verification below is historical. Existing general semantic retrieval and legacy-baseline limits remain documented.

# Task 5 verification - 2026-10-14 (historical)

Task 5 reuses the shared language layer, Clock, RAG orchestrator, config, SQLite, masked audit and metrics. It adds history-aware six-label sentiment with confidence, a separate high-risk detector, a separate tone preface, durable trigger evidence and masked summaries, Clock-driven unresolved timers, business/on-call/next-working-day routing, and authorized issue resolution. See [implementation and API](task5.md), [requirements trace matrix](RTM.md), and [limits](known_gaps.md).

Calm high-risk reports, concurrent duplicate prevention, persistence across restart/expiration, provider failures, strict >15-minute timers, weekends/holidays, and unchanged policy facts with tone on/off are tested. An existing spaced-card masking bug and English emotion/name ambiguity were repaired without adding dependencies.

## Actual pytest output

Command:

```powershell
.\.runtime\python311\python.exe -X utf8 -m pytest -q
```

```text
........................................................................ [ 35%]
........................................................................ [ 71%]
.........................................................                [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
201 passed, 1 warning in 38.01s
```

Raw output: [pytest-task5.txt](verification/pytest-task5.txt). All eleven required named Task 5 tests exist. The full suite also exercises Tasks 1, 4, 6 and provider fallback. The one existing TestClient deprecation warning is preserved.

Command:

```powershell
.\.runtime\python311\python.exe -m ruff check .
```

```text
All checks passed!
```

Dependency check: `.\.runtime\python311\python.exe -m pip check` returned `No broken requirements found.`

## Actual authored classifier evaluation

Command: `.\.runtime\python311\python.exe -X utf8 scripts/evaluate_t5.py`.

Actual output excerpt copied from the executed evaluator:

```json
{
  "correct": 52,
  "total": 60,
  "accuracy": 0.8666666666666667,
  "languages": {
    "en": {
      "correct": 13,
      "total": 15
    },
    "hi": {
      "correct": 13,
      "total": 15
    },
    "te": {
      "correct": 13,
      "total": 15
    },
    "es": {
      "correct": 13,
      "total": 15
    }
  }
}
```

The full [evaluation output](verification/t5-classifier-evaluation.json) includes the confusion matrix, dataset hash and eight missed implicit negative/sarcastic expressions. These labels were retained. This is an authored 60-example diagnostic set, not independently blinded or production accuracy. Runtime code never loads the labelled corpus.

The [labelled set](../tests/fixtures/task5/labelled_sentiment.json) and [provenance](../tests/fixtures/task5/README.md) are committed locally as `681aedc2761e861458e43e72a1d81c47928bffee`. Only those two files are in the commit; `.env` is ignored and untracked. No remote publication was requested.

Offline demonstration command: `.\.runtime\python311\python.exe -X utf8 scripts/demo_t5.py`; [actual output](verification/task5-demo.json). Queues are durable local records, not proof that an external agent was notified. FakeClock/FakeLLM demo metrics are not real provider latency measurements.

Earlier evidence below remains historical. Existing Task 4 general semantic retrieval and legacy-baseline limits remain unchanged.

# Previous provider verification - 2026-10-14

The supplied Google key was preserved, authenticated through models.list, and used successfully for a synthetic gemini-2.5-flash generation. Six blank app-role keys were filled locally. No secrets were printed and no billing setting was changed.

Configured model order: gemini-2.5-flash -> gemini-3.5-flash-lite -> gemini-3.1-flash-lite -> gemini-3.8-flash -> gemini-3.6-flash. All are free-tier eligible according to Google's official pricing and present in this key's model inventory; billing tier still requires your check in AI Studio. Backup successful generation remains unverified. The model that returned 404 is excluded from the active chain.

Fallback is implemented in core/llm.py with ordered single-key model selection, status/transport handling, Clock cooldowns, Retry-After, attempt and dispatch caps, safe error reporting, and refusal/auth/client-error termination. There is no FakeLLM fallback. Provider policy lives in config/default.yaml; model order in .env. [Full design, sources and evidence](provider_fallback.md).

The live Task 6 smoke check passed four explicit synthetic policy questions in English/Hindi/Telugu/Spanish, all with correct detection, localized answers, verified citations and one continuing isolated session. It uses a fixed Clock and in-memory SQLite with the real Gemini provider, not a deployed production integration. Unsupported earlier action requests and initial provider failures are retained in the [smoke history](verification/task6-live-provider-runs.jsonl) and [initial provider report](verification/provider-generation.json).

The live checks exposed and repaired request-filler dilution in multilingual retrieval, missing authorized document scope in the provider context, and citation punctuation spacing in curated translation. Entities and negation remain protected, and the claim verifier was not weakened.

## Current pytest output

Command:

```powershell
.\.runtime\python311\python.exe -X utf8 -m pytest -q
```

```text
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
145 passed, 1 warning in 25.86s
```

Raw evidence: [pytest-provider.txt](verification/pytest-provider.txt). All 14 required Task 6 test names remain present. HTTP fallback tests are hermetic; separate manual smoke scripts contain the live requests.

Command:

```powershell
.\.runtime\python311\python.exe -m ruff check .
```

```text
All checks passed!
```

Dependency verification (`.\.runtime\python311\python.exe -m pip check`) returned `No broken requirements found.` No new dependency was added.

Current local corpus command: `.\.runtime\python311\python.exe -X utf8 scripts/evaluate_t6.py`. Its [actual output](verification/t6-evaluation-provider.json) records 35 conversations / 105 messages per language, plus 20 disjoint-wording cases, without detection/intent failures. This is authored resource-domain evidence, not an independent language benchmark.

Next actions requiring you: [next_steps.md](next_steps.md). Current limits: [known_gaps.md](known_gaps.md). Current RTM: [RTM.md](RTM.md). Task 4 general semantic search and the legacy baseline remain incomplete/unverified; neither is hidden by provider smoke success.

The earlier counts and command output below are preserved as historical evidence and are superseded by the current suite above.

## Historical Task 6 implementation and verification (2026-10-13)

Task 6 is implemented in core/entities.py, language.py, sessions.py, conversation.py, and the existing core/store.py and app/chatbot.py. It reuses Clock, config, the LLM interface, RBAC, masked audit, metrics and the policy engine. The runtime has no branches for individual language codes.

Per-message language/intent evidence and configurable thresholds govern clarification. Original entity spans are protected before normalization and restored without changing their UTF-8 bytes. Context keeps at least ten user/assistant messages, latest values, and superseded values. Requests have separate entity bindings. Session state is copied from owner-bound SQLite rows; synchronization locks are the only shared per-session objects. Eight concurrent sessions and eight concurrent writes to one session are tested, including persistent audit/metrics writes.

The API returns language/confidence, detected_languages/mixed_language, requests with confidence/context, entities, summary, session_transition/generation, and the actual answer_language. Keep the same returned session_id and API key across messages. The default 30-minute inactivity and 24-hour restoration boundaries use Clock and can be changed at runtime. Provider failures do not partially commit turns.

User actions: [next_steps.md](next_steps.md). Scope and limits: [known_gaps.md](known_gaps.md), [assumptions.md](assumptions.md). RTM: [RTM.md](RTM.md).

## Task 6 and regression suite - captured output

Command:

```powershell
.\.runtime\python311\python.exe -X utf8 -m pytest -q
```

```text
........................................................................ [ 60%]
...............................................                          [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
119 passed, 1 warning in 25.46s
```

Raw output: [pytest-t6.txt](verification/pytest-t6.txt). All 14 required named Task 6 tests exist. There are 47 Task 6 parameterized cases, covering native/decomposed names, dates/leading-zero orders, mixed languages, switches, romanization/misspellings, corrections, multiple requests, isolation, timer boundaries, restart, threshold changes, additional resources, placeholder tampering and provider failure.

## Lint and dependency checks

```powershell
.\.runtime\python311\python.exe -m ruff check .
.\.runtime\python311\python.exe -m pip check
```

Captured results:

```text
All checks passed!
No broken requirements found.
```

No new third-party library was required for Task 6; the verified Python 3.11 dependency pins remain in requirements.txt.

## Measured local conversation corpus

Command:

```powershell
.\.runtime\python311\python.exe -X utf8 scripts/evaluate_t6.py
```

| Language | Fixture conversations | Messages | Correct language | Correct intents |
| --- | --- | --- | --- | --- |
| en | 35 | 105 | 105 | 105 |
| es | 35 | 105 | 105 | 105 |
| hi | 35 | 105 | 105 | 105 |
| te | 35 | 105 | 105 | 105 |

The separate wording set contains 20 conversations and 20 messages. Actual counts: language correct 20, intents correct 20, fixture-wording overlap 0. These examples were used during development, so this is disjoint wording rather than an independently blinded benchmark.

Actual JSON output: [t6-evaluation.json](verification/t6-evaluation.json). Full fixtures: tests/fixtures/en.json, hi.json, te.json, es.json, unseen.json. Runtime detection does not read fixtures. scripts/create_t6_fixtures.py reproduces their authored content.

Detection and normalization use bounded support-domain resources; confidence is rule evidence, not a calibrated probability. Curated answer translations preserve sources/entities. Unknown factual sentences remain in the source language with explicit answer_language. Unsupported wording asks clarification. General translation, general named-entity recognition, broad-language accuracy, and live-provider success are not claimed.

The earlier Task 4 general-semantic-retrieval and legacy-bot gaps remain documented. The historical Task 1 evidence below is preserved, with its original 72-test output; the current full suite above supersedes that count.

## Earlier Task 1 verification

Verified on Python 3.11.9, 2026-10-13. Source-first audit findings are in [verification.md](verification.md); remaining limits are in [known_gaps.md](known_gaps.md).

Task 1 reuses core/clock.py, config.py, llm.py, security.py, store.py, audit.py, metrics.py, and retrieval.py. New core/ingestion.py handles normalized hashes/validation/quarantine; core/updates.py handles golden evaluation, approval, maintenance activation, retries, and rollback. Snapshots are immutable SQLite records. ACTIVE is a singleton compare-and-swap pointer. app/chatbot.py initializes the persistent store and provides the update/query APIs and clock-driven worker.

All 13 requested named Task 1 tests are present, including both store/LLM outages, all six quarantine reasons, and five unauthorized operations. Additional tests cover restart persistence, stale candidates, immediate and boundary health failures, overnight windows, role separation, late retries, daily file discovery, API integration, lifespan initialization, credential masking, and disk config reload.

Task 4's named fixture tests pass after the repairs. Its general semantic-search requirement remains PARTIAL because the searcher is lexical. Extractive grounding refuses uncertain paraphrases. The legacy GooglePalm training bot and live Gemini integration remain unverified.

## Pytest - captured output

Command:

```powershell
.\.runtime\python311\python.exe -m pytest -q
```

```text
........................................................................ [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
72 passed, 1 warning in 17.76s
```

Raw evidence: [pytest.txt](verification/pytest.txt).

## Lint and dependencies

```powershell
.\.runtime\python311\python.exe -m ruff check .
```

```text
All checks passed!
```

```powershell
.\.runtime\python311\python.exe -m pip check
```

```text
No broken requirements found.
```

Installed package versions are copied into requirements.txt and [dependencies.txt](verification/dependencies.txt). The original upstream manifest is preserved in [requirements-baseline.txt](requirements-baseline.txt).

## Task 1 - actual maintenance-day output

Command:

```powershell
.\.runtime\python311\python.exe scripts/demo_t1.py
```

These are actual local script outputs from real SQLite and explicitly scripted FakeClock/FakeLLM. Four golden questions measured 1.0 accuracy and 1.0 grounding for ACTIVE and the accepted candidate. This is fixture performance, not general accuracy. Zero latency in the demo is expected because FakeClock was not advanced inside measured operations.

```text
OFFLINE MAINTENANCE DAY: FakeClock/FakeLLM; real SQLite and measured golden results
00:00 ACTIVE=1, golden={'accuracy': 1.0, 'grounding': 1.0, 'total': 4, 'cases': [{'id': 'refund-current', 'accuracy': 1, 'grounding': 1}, {'id': 'public-no-internal-sop', 'accuracy': 1, 'grounding': 1}, {'id': 'support-internal-sop', 'accuracy': 1, 'grounding': 1}, {'id': 'historical-laptop', 'accuracy': 1, 'grounding': 1}]}
00:05 quarantine reason=missing metadata
01:00 job=AWAITING_APPROVAL, candidate=2, duplicate_count=1
01:00 quality={"accepted": true, "active": {"accuracy": 1.0, "cases": [{"accuracy": 1, "grounding": 1, "id": "refund-current"}, {"accuracy": 1, "grounding": 1, "id": "public-no-internal-sop"}, {"accuracy": 1, "grounding": 1, "id": "support-internal-sop"}, {"accuracy": 1, "grounding": 1, "id": "historical-laptop"}], "grounding": 1.0, "total": 4}, "base_version": 1, "candidate": {"accuracy": 1.0, "cases": [{"accuracy": 1, "grounding": 1, "id": "refund-current"}, {"accuracy": 1, "grounding": 1, "id": "public-no-internal-sop"}, {"accuracy": 1, "grounding": 1, "id": "support-internal-sop"}, {"accuracy": 1, "grounding": 1, "id": "historical-laptop"}], "grounding": 1.0, "total": 4}, "tolerance": 0.0}
01:30 Activation blocked outside maintenance window; ACTIVE=1
02:00 approved candidate activated; ACTIVE=2
02:03 scripted health failure; auto-rollback ACTIVE=1
02:10 corrected update activated; ACTIVE=3
02:15:01 health window expired; ACTIVE=3; no automatic rollback
04:00 unchanged file skipped=1
10:00 manual rollback; ACTIVE=1
23:59 audit events=document_quarantined,ingestion_complete,update_scheduled,document_duplicate,ingestion_complete,quality_gate,update_approved,activation_held,update_activated,auto_rollback,update_alert,ingestion_complete,quality_gate,update_approved,update_activated,document_unchanged,ingestion_complete,manual_rollback
23:59 metrics={"counters": {"update_duplicates": 1, "update_escalations": 12, "update_failures": 1, "update_validation_failures": 1}, "latencies": {"update_activation_latency": {"avg_ms": 0.0, "count": 3, "histogram": {"le_1000ms": 3, "le_100ms": 3, "le_10ms": 3, "le_2500ms": 3, "le_250ms": 3, "le_5000ms": 3, "le_500ms": 3, "le_50ms": 3, "le_inf": 3}, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}, "update_ingest_latency": {"avg_ms": 0.0, "count": 3, "histogram": {"le_1000ms": 3, "le_100ms": 3, "le_10ms": 3, "le_2500ms": 3, "le_250ms": 3, "le_5000ms": 3, "le_500ms": 3, "le_50ms": 3, "le_inf": 3}, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}, "update_quality_latency": {"avg_ms": 0.0, "count": 2, "histogram": {"le_1000ms": 2, "le_100ms": 2, "le_10ms": 2, "le_2500ms": 2, "le_250ms": 2, "le_5000ms": 2, "le_500ms": 2, "le_50ms": 2, "le_inf": 2}, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}, "update_scheduled_latency": {"avg_ms": 0.0, "count": 1, "histogram": {"le_1000ms": 1, "le_100ms": 1, "le_10ms": 1, "le_2500ms": 1, "le_250ms": 1, "le_5000ms": 1, "le_500ms": 1, "le_50ms": 1, "le_inf": 1}, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}}, "values": {"update_confidence": {"count": 2, "latest": 1.0, "mean": 1.0}}}
DAY COMPLETE: assertions passed; provider behavior is scripted, not a live-provider validation
```

Full Task 4 command output: [demo-t4.txt](verification/demo-t4.txt), generated with `.\.runtime\python311\python.exe scripts/demo_t4.py`.

## Traceability and local usage

[RTM.md](RTM.md) maps each Task 1 design sentence to implementation and named tests. [The root README](../README.md) contains local run commands, API workflow, role keys, and scheduler configuration. No git repository is present in this workspace; no commit or publication was performed.
