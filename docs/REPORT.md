# Customer service bot engineering report

Date: 2026-10-17. Python 3.11. This report distinguishes implemented contracts, actual provider measurements, scripted tests and deployment limits. Original task documents T1–T6 remain unchanged. Every pre-existing test function remains; the only pre-existing assertion changed is OCR version-format validation, explicitly requested to accept both `tesseract v5.4` and `tesseract 5.3.4` while retaining language-pack checks.

## Architecture

The project extends the mentor's [customer_service_chatbot_LLM](https://github.com/aslin72/GEN---AI-course/tree/main/GEN---AI-course/customer_service_chatbot_LLM) workspace. Original FAQ CSV bytes and `src/` entry points are preserved. The supported API imports original FAQs into metadata-bearing documents and uses the shared policy engine. The old Streamlit/LangChain/GooglePalm path remains unverified; preserving it is not proof that the old chain runs.

```text
Customer UI -> origin / rate / size / RBAC -> FastAPI
    chat -> language + sessions -> sentiment + independent risk
         -> authorized, valid, latest-version hybrid RAG -> cited source answer
         -> protected provider translation / curated or source fallback
    upload -> structural gate -> Tesseract / PDFium -> fields / conflicts / jobs
    tickets -> mandatory drafts -> priority / routing / business-time SLA
Shared: Clock, hot configuration, masked audit, metrics, SQLite
SQLite: immutable snapshots, ACTIVE pointer, content/model-keyed vectors,
        owner-bound sessions, tickets, upload jobs and local alert records
```

The provider adapter performs real generation and batch embeddings. FakeClock, FakeLLM and scripted FakeEmbedder keep tests offline. A scripted vector test establishes cache/filter/citation contracts, not semantic accuracy. No provider or UI layer executes recognized refund/cancellation intents as payment operations.

## Per-task design decisions

| Task | Design and reuse | Tests and material limits |
| --- | --- | --- |
| T1 | Canonical JSON hashes, ACTIVE-relative dedupe, six quarantine reasons, immutable snapshots and atomic pointer swap. Candidate quality compares exact-answer accuracy and independently valid cited grounding against ACTIVE with configurable tolerance. Golden questions include paraphrases and use the same hybrid engine/cache. Three retries are absolute +15/+30/+60 minutes; approval precedes maintenance activation and health monitoring/rollback. | Original 13 named scenarios retained; hybrid golden test added. Relative equality can pass a low-scoring baseline. Alerts are durable local records; SQLite must remain writable. |
| T2 | Header/type/size/pixel/stream/active-PDF gates precede decoders. Actual Tesseract TSV and PDFium native/raster extraction yield explicit value/confidence/region or null. Message conflicts ask clarification. Jobs and retention use Clock; expiry unlinks real bytes. PATH OCR detection and platform language-resource discovery replace Windows-only defaults. | Original eight named scenarios retained; alternate version formats and runtime-over-env precedence added. OCR/layout/injection recognition is bounded. Native process/container safety is not universal malware proof. |
| T3 | Existing sentiment and summaries feed structured ticket collection. Missing mandatory values remain drafts. Configured weighted priority, skills/availability/workload routing, business-time warning/breach and runtime recalculation reuse one calendar/store. Related grouping and conservative dedupe keep unrelated issues separate. | Original 12 named scenarios retained. No agent roster or external helpdesk delivery is invented. No arbitrary free-text customer/contact inference. |
| T4 | Trusted ingest scans validity intervals and injection before computing vectors; cache key covers content/version/scope/dates and stores model name. Changed content/model reindexes. Query order is authorization, as-of applicability, flagged-doc exclusion, latest family/product/region version, hybrid scoring and threshold. Missing vectors/outages use lexical fallback. | Original ten scenarios retained plus 10 paraphrases per six scenarios and lookalikes. Only authorized surviving text is scored or sent to generation; query-time embedding uses query text, never excluded document text. General recall remains limited by measured results. |
| T5 | Provider JSON classification precedes unchanged resource patterns. Six-label enum, confidence, language and schema validation reject malformed outputs. Complete JSON fences are parsed without relaxing enum checks. Prompt-injected inputs bypass the classifier provider. Risk remains rule-based, independent of provider sentiment and provider failure. Tone changes presentation only. | Original 11 scenarios retained, plus provider/fallback/injection/schema/independent-risk tests. New labels were committed separately before classifier changes. Rules were not tuned to the new set. Confidence is not calibrated probability. |
| T6 | Original spans are protected before normalization. Provider translation protects names/IDs/dates/products/citations and numbers with opaque placeholders, rejects missing/duplicated/unknown tokens and new numeric values, then restores original bytes. Curated/source fallback retains actual answer_language; source_answer stays separate. Existing context corrections, superseded values, per-session locks/revision checks and Clock expiry/restore remain. | Original 14 named scenarios retained; byte-preservation, malformed translation, outage and source-separation tests added. Name extraction is bounded; structural validation does not independently prove semantic translation fidelity. |

The latest approved retrieval ordering supersedes historical T4 ordering without editing `docs/tasks/T4.md`. Flagged instruction spans are neutralized while surrounding text is retained for review; flagged chunks remain excluded from retrieval/embedding. T1 still quarantines injection-flagged files with original evidence. Original FAQ CSV uses Windows-1252 where needed and is not rewritten. Troubleshooting guide fixtures are ingested through the same metadata schema.

## Frozen evaluations and real provider results

The T4 set was committed as `74643de` before retrieval changes: 60 paraphrases (at least ten each for conflicting, restricted, expired, future-dated, historical and injected) plus 12 unanswerable lookalikes. SHA-256: `413e80254b0d25da7269fbcac4dfb2ec8ca86420407301f3ad44eb38001bade9`. Its 20 answerable and 52 refusal cases were not used to tune thresholds or synonym rules. Command: `python scripts/evaluate_t4.py --live`.

| Metric | Actual result |
| --- | --- |
| Answer rate on supported questions | 15.00% (3/20) |
| Correct cited-answer rate | 15.00% (3/20) |
| False-answer rate on refusal cases | 0.00% (0/52) |
| Embedding failures / terminal evaluation errors | 2 / 0 |
| Models used | gemini-embedding-001 and gemini-2.5-flash |

[Full T4 outcomes](verification/release-t4-heldout-live.json). Conservative refusal is common; zero false answers on this small set is not universal safety. Tests with scripted vectors are reported separately from this actual provider run.

The new T5 set was committed as `9ecebee` before classifier changes. It contains 48 newly labelled examples across en/hi/te/es, including history-dependent sarcasm and calm compromise/duplicate-payment/legal reports. SHA-256: `bf58e610a821461b56d38d0d68a3370333b7db5d6ca63cd3f42d0d76dbbd76af`. Commands: `python scripts/evaluate_sentiment_holdout.py` and the same command with `--live`.

| Metric | Actual result |
| --- | --- |
| Pattern-only baseline on new set | 17/48 = 35.42% |
| Assisted pipeline on new set | 22/48 = 45.83% |
| Accepted provider classifications | 6/48; other decisions used pattern fallback |

An initial evaluation accepted zero provider results because the provider returned a complete JSON code fence. An independent synthetic probe reproduced that transport-format issue; the parser was corrected, enum/security tests added, and evaluation repeated with unchanged labels/rules. [Initial result](verification/release-t5-before-protocol-fix.json), [probe](verification/provider-structured-probe.json), [final outcomes](verification/release-t5-live.json). This is diagnostic pipeline accuracy, not independently blinded or pure-LLM accuracy. Calm high-risk rule coverage is recorded separately and can miss unrepresented wording.

Live translation requests encountered HTTP 429. Source fallback retained the tested original entity bytes; no successful live translation is claimed. [Actual fallback output](verification/release-translation-live.json) and [provider status](verification/provider-translation-status.json). Unit tests exercise successful scripted-provider translation, invalid JSON/tokens/numbers, outage and separate canonical source answers.

## Customer UI, security and deployment

FastAPI serves one customer page at `/`, with chat, invoice/product upload and owner-bound ticket details/status. No knowledge approval/activation, escalation resolution or other admin controls appear there. DOM rendering uses textContent and element creation; no HTML interpretation or browser key persistence is used. API origin restrictions, CSP, request-size gates and Clock-driven rate budgets apply before application parsing/processing. Rate limits are per IP and hashed credential with bounded storage; distributed enforcement is not implemented.

The browser smoke test used an isolated localhost database and synthetic customer key with live generation disabled. It verified chat refusal, literal HTML text with zero image elements, mandatory-field ticket completion to QUEUED, and actual invoice OCR (ORD-1001, 2026-10-15, INR 1299.00, Blue Widget PRD-X100, E-PAY-042). [Browser evidence](verification/release-ui-smoke.json), [screenshot](assets/customer-ui.jpg).

Docker installs Tesseract plus eng/hin/tel/spa and runs UID 1000 with one worker. Default state is under `/app/data`. [Render guide](deploy-render.md) explains that Free services stop after inactivity, stopping scheduler/retention/SLA work while asleep, and ephemeral files can disappear; a suitable persistent disk and one continuously running worker are required for durable operation. Sources: [Render Free](https://render.com/docs/free), [disks](https://render.com/docs/disks).

Live URL: not deployed; no hosting credentials or completed deployment were supplied. The repository/CI URLs are not a live chatbot. The delivered demo artifact is the [2–5 minute recording script](demo-script.md), not a fabricated video.

## Test evidence

All 68 original required names remain. Stage results were 287 (CI/portability), 301 (T4), 314 (T5), 324 (T6) and 329 (UI/deploy), each with the preserved single Starlette TestClient deprecation warning and clean Ruff. Each implementation step has its own commit; the two evaluation sets have separate freeze commits. Ubuntu, Windows and Docker verification use fresh GitHub Actions checkouts; [workflow](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/workflows/ci.yml).

Last implementation full-suite command: `.runtime/python311/python.exe -X utf8 -m pytest -q`.

```text
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 65%]
........................................................................ [ 87%]
.........................................                                [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\rajashekar\Desktop\Projects_Backup\Real_Time_Gen_AI_Customer_Service_Bot\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
329 passed, 1 warning in 63.78s (0:01:03)
```

Ruff command: `.runtime/python311/python.exe -m ruff check .`.

```text
All checks passed!
```

Fresh-clone validation for the documentation/dependency revision is not yet recorded in this working report.

Completed hosted implementation-step verification:

| Commit | Result | Workflow |
| --- | --- | --- |
| 72b7db0 | success | [Ubuntu, Windows and Docker](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/runs/39041574893) |
| 059dfb2 | success | [Ubuntu, Windows and Docker](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/runs/39042065722) |
| 6313df5 | success | [Ubuntu, Windows and Docker](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/runs/39042406475) |
| 7109f16 | success | [Ubuntu, Windows and Docker](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/runs/39042766477) |
| 2f6620f | success | [Ubuntu, Windows and Docker](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/runs/39043371035) |

[Actual Ubuntu job log](verification/release-ci-ubuntu.txt), [Windows job log](verification/release-ci-windows.txt), [Docker build/OCR log](verification/release-ci-docker.txt). These are captured outputs for implementation commit 2f6620f. The workflow also runs on the final documentation commit; its current result is linked from the repository Actions page.

## Remaining limits

Held-out recall/classifier accuracy is modest and provider quota failures are real. Rules cannot recognize every attack/risk/name/layout; unknown names may not receive entity protection. Extractive source checks deliberately reject unsupported paraphrases, and translated wording is not independent policy evidence. The old legacy-chain execution remains unverified even though its FAQ content is ingested. Agent availability and external alert/helpdesk delivery require real configuration. No high-availability, distributed scheduling, encrypted storage, forensic deletion or production security certification is claimed. Render Free is demonstration hosting only.

Only gemini-2.5-flash has successful generation evidence among the documented model candidates. `.env.example` therefore has an empty fallback list. Existing private environment values are not published. The original FAQ dataset and task documents are unchanged; historical audit output is preserved under `docs/archive/` and current evidence remains under `docs/verification/`.
