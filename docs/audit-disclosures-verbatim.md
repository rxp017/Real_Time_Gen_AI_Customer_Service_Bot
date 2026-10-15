# Verbatim audit disclosures

Source snapshots captured before audit edits on 2026-10-15. No wording omitted or paraphrased.

## docs/known_gaps.md

SHA-256 of source bytes: `d3447ac7a9d3844d065c1d79be4e3592cb64c89e665f610d88eb4ecef4e9e2db`

````text
# Verified limits

## Task 3 limits

- Ticket collection is a structured API workflow. `/query` exposes `tickets` and `ticket_questions`; clients must display those questions and submit actual customer fields through `/tickets`. There is no new customer-facing frontend or unrestricted free-text field inference.
- Deduplication is conservative configured token similarity with negation/numeric guards, not a general semantic classifier. Issue-family/skill regexes and product mappings need real domain resources. Customer evidence references are preserved as supplied, not independently authenticated.
- The production agent roster is empty until real agents are configured. Queue, warning and escalation events are persisted locally; external helpdesk/notification delivery is not configured. The application Clock worker must run and SQLite must be writable.
- Business time uses one configured same-day calendar and timezone; agent-specific shifts, overnight schedules and distributed workforce integrations are outside this task. Runtime SLA/calendar changes recalculate open tickets from their original final creation time and retain prior escalation history.

## Task 2 limits

- The upload allowlist is PNG/JPEG and a conservative PDF subset. Encrypted/incremental/object-stream PDFs, scripts/actions/attachments/forms, unknown filters, animated/compressed-metadata PNGs and oversized files are rejected. Some legitimate files need export to a simple PDF or image. Preflight checks bounded structures; it is not proof of universal malware safety.
- English synthetic invoices were extracted using real Tesseract/PDFium. Language-pack availability is verified for eng/hin/tel/spa; arbitrary layouts, handwriting, multilingual field labels and adversarial OCR are not established. Source confidence is evidence confidence, not invoice or payment authenticity.
- The shared pattern injection detector and data isolation reject the tested visible/hidden/native/scanned attacks. They do not establish perfect recognition of every language, obfuscation or steganographic payload.
- Jobs run in a bounded application thread pool, with native process timeouts and checked pixel/stream/page limits. OS process/container isolation and production resource containment are not verified. One application worker owns recovery/purge for each database.
- Completion notifications/results use authenticated polling. No external push/email delivery is configured. Retention deletes stored file bytes and customer/result content, not minimal status tombstones; the tests prove actual unlinking, not forensic erasure. Store/disk failures can delay purge until recovery.
- Real Gemini image input succeeded once on a synthetic text-only product-label fixture. The model correctly said no physical product was depicted; general product identification, defect analysis and deployed vision accuracy remain unverified. Missing credentials or unsupported capability honestly return cannot analyse.


## Task 5 limits

- The authored 60-example labelled set scored 52/60 (86.67%), with eight missed implicit complaints/sarcasm expressions retained in the evidence. It is not independently blinded or production accuracy. The classifier and separate high-risk detector use resource patterns; unrepresented wording and complex negation can be missed. Confidence is an evidence score, not a calibrated probability.
- On-call and scheduled queues are persisted SQLite records. No external ticketing or notification provider is configured; a routed record does not prove a human received an alert.
- The Clock-driven worker must run and SQLite must remain writable to record escalation timers. The existing single-worker deployment requirement still applies.
- Tone adds a separate preface and leaves the policy answer unchanged. It does not improve Task 4's incomplete general semantic retrieval; long emotional questions may still safely refuse.

## Existing project limits

- Task 4 search uses local cosine term frequency and keyword overlap. It has no learned embeddings or IDF weighting. Filtering and the named fixture scenarios pass, but general semantic retrieval is incomplete.
- Grounding is conservative extractive matching. Unsupported paraphrases are refused. It is not a general natural-language entailment model.
- The preserved upstream Streamlit/LangChain/GooglePalm source is not a verified runnable baseline. Its original manifest includes the invalid `sentence-transformer` package name, stale dependencies, and a CSV path mismatch. The original manifest is archived in `docs/requirements-baseline.txt`. The supported FastAPI runtime uses the shared RAG engine. The legacy fallback calls the original chain and returns 503 if unavailable; it never fakes success.
- Updated 2026-10-14: the supplied key authenticated with models.list, a gemini-2.5-flash synthetic generation succeeded, and four explicit refund-policy questions passed the real-provider Task 6 smoke check. This is synthetic fixture evidence, not production/customer-policy quality. Earlier offline quality/demo numbers remain FakeLLM results.
- Golden results describe four fixture questions, not broad production accuracy. Expected-answer accuracy uses normalized exact matching; grounding independently checks the actual retrieved/cited sources and verified sentences. Expected refusals count as grounded only when verified and citation-free.
- The scheduler is an in-process worker. Jobs, snapshots, approval states, and ACTIVE survive restart. Deployment must run one scheduler instance per database. SQLite pointer compare-and-swap protects concurrent activations; distributed scheduler coordination is not implemented.
- Alerts are durable `update_alert` audit records plus structured Python logging. No email, Slack, or external notification destination is configured.
- Automatic rollback needs the SQLite store to remain writable. A total database outage prevents any pointer mutation until the store recovers; the worker records dependency failures where possible.
- Quarantine contains original invalid-file evidence. It is excluded from version control and must remain accessible only to local operators.
- The current Starlette TestClient emits a deprecation warning for httpx. Tests pass; the warning is preserved in verification output.

No intentional placeholder implementations were added. Abstract interfaces contain only their documented contracts.

## Task 6 limits

- Detection is resource-based customer-support language/intent recognition. Confidence is an evidence score, not a calibrated probability. Known romanized/misspelled variants are supported; unsupported expressions ask clarification. The authored corpus and disjoint wording set are local evaluation evidence only. Disjoint wording was exercised during development; it is not an independently blinded holdout benchmark.
- Name extraction covers configured name cues and patterns, not every unlabeled proper noun. Additional entity/date/product conventions must be supplied as resource patterns.
- Translation uses curated phrases and answer sentences. A factual answer without a curated target-language translation is returned in its original source language with explicit answer_language metadata. There is no unrestricted machine-translation claim.
- Conversation content and summaries are stored locally in owner-bound SQLite records. No encryption-at-rest feature was requested or implemented. Anonymous session IDs are bearer tokens; authenticated sessions are additionally bound to their API key.
- General semantic retrieval and legacy-bot validation remain the earlier Task 4 limitations. Live Gemini connectivity and four supported policy questions are now verified; general language/customer-policy accuracy is not established.

## Provider fallback limits

- The configured free-tier-eligible catalog is based on official Google pricing and the key's model inventory, checked 2026-10-14. Project billing tier cannot be read from this API key, and no paid billing switch was made. Free-tier eligibility is not a promise of zero charges on a billing-enabled project.
- Primary gemini-2.5-flash returned HTTP 200. Initial probes of newer model backups encountered timeouts/503; their successful generation has not been established for this project. gemini-2.5-flash-lite returned 404 and was removed from the active chain. Model listing alone does not establish quota or successful generation.
- Switching models uses the same Google key and project; it cannot increase project-wide quotas. Failed models cool down, total attempts are bounded, and exhaustion returns a real failure.
- HTTP timeout limits phases of a request; the Clock budget prevents further model dispatch after its deadline, not a guaranteed hard wall-clock cutoff on an already-running HTTP operation.

````

## docs/assumptions.md

SHA-256 of source bytes: `f2cd914d2144b50eff0722ebf35d376a70ad1dddbfc67cb14ddf6d901a15f474`

````text
# Project Assumptions

## Environment & Runtime
- Python Runtime: system/.venv is Python 3.14.7. Current validation uses official portable Python 3.11.9 in `.runtime/python311/`; no system installation or PATH changes were made.
- Hermetic Testing: Per RULES.md, tests run hermetically (`FakeClock`, `FakeLLM`, no external network calls). Any external LLM or embedding provider is swappable with deterministic local implementations for unit and integration testing.

## Time & Localization
- Timezone: `Asia/Kolkata` is used for all timestamp parsing, active policy validity checking, and business date logic.
- Time interface: All time-dependent modules exclusively query `Clock` (`clock.now()`).

## Document Metadata & Retrieval Pipeline
- Dates: Dates are stored as ISO-8601 strings or timezone-aware `datetime` objects in `Asia/Kolkata`.
- Document metadata schema:
  - `doc_id`: Unique identifier
  - `doc_family`: Identifier for grouping versions/superseded revisions of a document
  - `version`: Positive integer, comparable within a document family
  - `product`: Target product line (or `all`)
  - `region`: Geographic region (or `all`)
  - `access_level`: Required minimum role/permission (e.g. `public`, `customer`, `support_agent`, `admin`)
  - `effective_date`: Start of validity window (inclusive)
  - `expiry_date`: Exclusive end of validity window; null if indefinite
- Retrieval Pipeline stages:
  1. Authorise by caller role (filter out access_level > caller permission)
  2. Validity filter by as_of date (default clock.now(), or parsed date from query)
  3. Semantic search over survivors
  4. Conflict resolution: latest applicable version wins within (doc_family, product, region)
  5. Similarity score threshold
- Post-Generation Verifier: Inspects generated claim sentences against cited chunk content. If any factual sentence lacks direct citation or citation ground support, it is pruned or flagged as refusal.

## Task 1 decisions

- No docs/tasks/T1.md was present. It was created from the user's exact design and named-test list, with provenance recorded in that file. The user authorized implementation after verification; the earlier Step 0 approval gate does not restart.
- JSON is the supported ingestion format because it carries the existing Document schema. Every other file type is quarantined with `unsupported type`; PDFs/OCR/CSV ingestion is not implied by T1.
- Normalize UTF-8 BOM, Unicode NFC, CRLF/CR, trailing whitespace, and JSON key order/formatting before SHA-256. Filename is excluded. All required policy metadata is included; server-only fields are not accepted from uploads.
- An upload is one policy chunk. A changed existing doc_id increments the stored document version even if the source forgot to increment it. Snapshot revision numbers are separate from document versions.
- Compare ingestion against ACTIVE, not rejected candidates. Rejected/outage candidates never poison deduplication. Input files remain in place so scheduled retries can revalidate them; quarantine preserves a byte-for-byte evidence copy and a reason manifest.
- Candidate snapshots merge new/changed documents into ACTIVE. Missing input files do not imply deletion; no deletion workflow was requested.
- Initial legacy document contents become immutable revision 1. Empty initial stores are permitted, and the golden gate measures that baseline rather than inventing an accuracy floor.
- Retry +15/+30/+60 are absolute offsets from the first actual failure, not cumulative waits. There are four attempts total. Subsequent daily runs are new jobs. Scheduled runs require a separate human approval; the worker can activate only an APPROVED candidate.
- Maintenance windows are local Asia/Kolkata, start-inclusive/end-exclusive. Overnight windows belong to the configured starting day. The health window includes the exactly-five-minute boundary; after it expires there is no automatic rollback.
- The application polls health using Clock at the configured interval. Immediate activation health checks and golden regressions trigger rollback. Failure reasons and restored versions are persisted in snapshot reports and masked audit records.
- A configurable tolerance is an absolute difference in scores on [0,1], separately applied to accuracy and grounding; default is zero.
- Unknown management keys/roles fail closed. Dedicated ingestor, approver, and operator keys come from environment/.env; management-only keys do not grant query permissions. View returns status/reports and no document content.
- A `update_alert` event in the durable audit store is the configured local alert mechanism. No outbound messaging was authorized.

## Task 6 decisions

- T6.md was absent and was created from the current user prompt, preserving its design and required test names. Implementation was already authorized.
- Default languages are en plus hi, te, es. JSON language resources contain script ranges, lexical/romanized markers, entity spans, normalization rules, intent evidence, conjunctions, follow-up expressions, and localized UI/curated answer translations. Config enables languages and sets thresholds/weights/timings. Missing resources fail visibly; enabling a language never requires a Python branch.
- Language confidence measures coverage and language evidence, not a statistically calibrated probability. Borrowed business terms receive resource weights. Intent confidence is rule evidence compared with a separate config threshold. Unknown/ambiguous intent always asks clarification, even if someone configures threshold zero.
- Known phrases and documented misspellings are normalized using resources. Unseen wording is evaluated separately from fixture wording. Unsupported vocabulary/transliteration asks clarification; no arbitrary machine translation or broad-language accuracy is claimed.
- Entity matching reads original input before normalization. Regex spans use original names after explicit name cues, labeled/bare numeric orders, named/ISO dates, and prefixed product codes. Unicode decomposed accents, original case, punctuation, leading zeros, and UTF-8 bytes are preserved through opaque per-message placeholders. Unknown/unlabeled proper names need additional resource patterns; no general NER model is claimed.
- Curated full-sentence answer translations preserve citations and entities. Factual answers without a curated translation remain in the source language, reported by answer_language. Multiple source languages are comma-separated in that field. The system never marks an unverified generated translation as factual evidence.
- The context window counts user and assistant messages, with a minimum of 10. Latest entity values and superseded records persist separately from the bounded raw-message window. Per-request entity bindings keep different orders/products apart. An ambiguous follow-up to multiple prior intents asks clarification instead of choosing a request.
- Session IDs are generated when omitted. Authenticated sessions are bound to a hash of the API key; a different key cannot read/update them. Anonymous IDs act as bearer conversation tokens and must not be shared. Payloads are independently decoded from SQLite; only synchronization locks are shared.
- Expiry occurs at inactivity >= configured 30 minutes, using Clock. Restoration is allowed at a gap <= configured 24 hours measured from last activity; a longer gap starts a new generation with empty context. Restoration brings back a deterministic structured summary, not the expired raw transcript. Both boundaries are tested.
- Background polls expire idle sessions, and inspection/next-message access also evaluates expiry. There are per-session locks and SQLite revision checks; provider failure rolls back the whole uncommitted turn. Supported deployment remains one application worker, as documented for the scheduler.
- Intent handling recognizes and routes requests to the existing policy engine. Recognizing cancel/refund/payment requests does not execute order changes or payment operations.

## Provider fallback decisions - 2026-10-14

- The current user authorized editing .env and adding model fallback. The Google key was preserved byte-for-byte through all local config edits. Formerly blank private application role keys were generated locally and never printed.
- Models are a free-tier-eligible text catalog verified against official pricing and models.list. The primary is the successfully probed gemini-2.5-flash. Four backup models are configured in GOOGLE_FALLBACK_MODELS. The model returning 404 was excluded from this key's active chain.
- Fallback uses one key, without rotation. Retryable model errors are 404/408/429/500/502/503/504 and transport failures. Authentication/client-input errors and provider safety blocks stop the chain. Successful responses identify the actual serving model and observed attempts.
- Per-model cooldowns, timeouts, maximum attempts, token cap and dispatch budget come from config/default.yaml. Cooldowns use Clock and Retry-After, without sleeping inside generation. All failed/cooled models cause ProviderUnavailableError, never a fabricated answer.
- Task 6 normalization now removes configured request filler from the retrieval query while preserving protected entities and negation. Curated translations allow ordinary citation punctuation spacing. Authorized document product/region/validity metadata is isolated as untrusted data in the LLM prompt; it establishes the selected policy's scope without weakening claim verification.
- Only synthetic fixture policy content was sent in live smoke checks. The later explicit-policy check passed all four languages. Earlier generic action requests could correctly refuse because refund processing instructions were absent; previous smoke results are retained in the live-run history.

## Task 5
See docs/task5_assumptions.md for the missing-task provenance and Task 5 decisions.

## Task 2
See docs/task2_assumptions.md for Task 2 provenance and scope decisions.

## Task 3
See docs/task3_assumptions.md for missing-task provenance, draft collection, safe deduplication, business SLA and local queue decisions.

````
