# Project assumptions - current release 2026-10-17

The approved 2026-10-17 request governs the following changes. Earlier notes below are retained as historical design context; the source snapshot is archived separately.

- Original task documents remain unchanged. The new approved ordering resolves latest applicable family/product/region versions before either embedding or lexical similarity, superseding the historical T4 sequence.
- Document vectors are computed at trusted ingestion after validity-interval and injection scans. Historical/future documents may be embedded for later authorized as-of queries. Query-time scoring reads only authorized/applicable/latest survivors; flagged chunks are excluded. Provider outages or absent vectors fall back to lexical retrieval. Model/content-keyed cache rows do not mutate snapshot documents. Unchanged source ingestion refreshes a missing vector after a model change; explicit reindex is also available.
- Flagged instruction spans are neutralized while retaining surrounding text for review; the flagged document remains ineligible for retrieval/embedding. T1's quarantine behavior is retained.
- The training CSV's original bytes and Windows-1252 punctuation are preserved. Metadata identifies source FAQ rows separately. A configured new empty store imports FAQs; an existing ACTIVE snapshot or an unconfigured offline empty store is not silently changed.
- The T4 corpus was frozen in 74643de and the new T5 labels in 9ecebee, before their implementation changes. No synonym/threshold/sentiment/risk rule tuning against these sets is performed. Measured pipeline fallback is part of the reported results; scripted vectors do not establish semantic accuracy.
- Classification accepts only the six stated enum labels with bounded confidence and configured language. Complete JSON code fences are transport formatting, not instructions. Risk decisions remain rule-based and separate from provider sentiment.
- Translation operates on protected original spans and numeric/citation tokens; malformed/missing/duplicated tokens fail to curated or source fallback. The canonical source_answer is separate from translated presentation. Name detection remains bounded, and structural translation checks are not semantic certification.
- OCR precedence is runtime override, environment, then config/PATH, with a standard Windows fallback. System tessdata or tagged local resources are detected without Linux environment changes.
- Customer UI controls are limited to chat, uploads and own-ticket workflow. Access keys are not persisted in the browser; origins, rate buckets and request bodies are bounded server-side. One worker/instance is required. Default persistent state paths share data/.
- The public example has no fallback models beyond the proven primary because no other model has successful generation evidence. Existing private environment values are not published. Live translation requests encountered rate limits and fall back honestly.
- Render Free is demonstration hosting: sleep suspends timers and ephemeral storage can lose state. No live URL or completed video is claimed. A deployment guide, PDF report and 2–5 minute recording script are delivered.

## Historical notes (through 2026-10-15)

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
