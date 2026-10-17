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
