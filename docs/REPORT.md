# Customer service bot engineering report

Date: 2026-10-19. Python 3.11. This revision reports quota-limited evidence. There is **no valid post-fix live accuracy result**: T4 exceeded the preregistered infrastructure-failure limit and the user chose to finish without raising quota. T5 has a separate fallback-only result. No registered application/evaluation source, configuration, resources or prompts changed after the frozen evaluation began.

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
| T4 | Trusted ingest scans validity intervals and injection before computing vectors; cache key covers content/version/scope/dates and stores model name. Changed content/model reindexes. Query order is authorization, as-of applicability, untrusted safe-view projection, latest family/product/region version, hybrid scoring, rank/margin acceptance and top-k generation. Missing vectors/outages use lexical fallback. | Original ten scenarios retained plus 10 paraphrases per six scenarios and lookalikes. Only authorized surviving text is scored or sent to generation; query-time embedding uses query text, never excluded document text. General recall remains limited by measured results. |
| T5 | Provider JSON classification precedes multilingual resource patterns improved on the separately frozen development set only. Six-label enum, confidence, language and schema validation reject malformed outputs. Complete JSON fences are parsed without relaxing enum checks. Prompt-injected inputs bypass the classifier provider. Risk remains rule-based, independent of provider sentiment and provider failure. Tone changes presentation only. | Original 11 scenarios retained, plus provider/fallback/injection/schema/independent-risk tests. New labels were committed separately before classifier changes. Rules and prompts were not tuned to the frozen held-out set; development labels are separate. Confidence is not calibrated probability. |
| T6 | Original spans are protected before normalization. Provider translation protects names/IDs/dates/products/citations and numbers with opaque placeholders, rejects missing/duplicated/unknown tokens and new numeric values, then restores original bytes. Curated/source fallback retains actual answer_language; source_answer stays separate. Existing context corrections, superseded values, per-session locks/revision checks and Clock expiry/restore remain. | Original 14 named scenarios retained; byte-preservation, malformed translation, outage and source-separation tests added. Name extraction is bounded; structural validation does not independently prove semantic translation fidelity. |

The latest approved retrieval ordering supersedes historical T4 ordering without editing `docs/tasks/T4.md`. Flagged instruction spans are neutralized while surrounding text is retained for review; the flagged parent remains audited and independent safe sentences may be projected into a retrieval/embedding view. The neutralized instruction span is never evidence; pure instruction documents remain excluded. T1 still quarantines injection-flagged files with original evidence. Original FAQ CSV uses Windows-1252 where needed and is not rewritten. Troubleshooting guide fixtures are ingested through the same metadata schema.

## Independent development sets and diagnosis

T4 development data was committed separately in 49e77ee before diagnosis: 86 independently worded cases, 48 answerable and 38 refusal, with 111 documents including 100 unrelated distractors. It covers authorized restricted answers, denied access, expired/future/historical applicability, product/region conflicts and a safe answer beside an injected instruction. Case SHA: `8e527b58b5c6a30220041fad5f3de5704b0ee7c4ccc0c68c0ff17995d11beb74`. Frozen held-out text was not used to diagnose, build resources or tune.

The lexical/FakeLLM baseline produced 6/48 supported answers and 1/38 false answers; 79 cases stopped at threshold. The false answer returned depot opening facts for an absent payment attribute. The initial live diagnosis had incomplete embeddings in all 86 cases and provider quotas, so it could not establish retrieval quality. Warming the cache later recorded 197 actual gemini-embedding-001 vectors. Per-case lexical/embedding/fused scores, component checks, ranks, threshold decisions and refusal stages are retained in the development JSON traces.

Development-only sweeps considered component coverage and rank/margin, in addition to thresholds. Final settings: semantic weight 0.80, lexical weight 0.20, hybrid threshold 0.50, rank margin 0.08, strong score 0.85, top-k 3, candidate score gap 0.12 and lexical-only threshold 0.40. Query coverage was considered but disabled at 0.0 after its dev recall cost; requested-attribute checks reject absent money/warranty/condition facts. The source verifier still checks every retained claim against its own cited source. Low-scoring alternate policies cannot defeat explicit unresolved product/region ambiguity.

With the recorded actual embeddings and deterministic source-quotation FakeLLM, the tuned dev regression measured correct-cited answers 48/48 = 100.00% (Wilson 95% 92.59–100.00%); false answers 0/38 = 0.00% (Wilson 95% 0.00–9.18%), with all 100 distractors present. This is a **tuned development regression**, not live generation accuracy or an independent generalization result. Its lexical-only fallback measured 37/48 supported answers and 0/38 false answers. The final live development generation attempt remained quota-blocked (0/48 supported answers); that failure is retained.

T5 development labels were committed separately in 3e6add5: 60 cases, 15 per en/hi/te/es, including sarcasm/history and calm high-risk reports. SHA: `e6160ce443eb9fad9f0043d9a241ce71685d3d756973a1bb525ce81525ce288b`. Pattern-only development accuracy moved from 40/60 to 59/60. A real provider development attempt accepted 6 decisions (6 correct; Wilson 95% 60.97–100%); 54 quota fallbacks were 54/54 correct (93.36–100%). Those six accepted cases do not establish multilingual model quality. The pipeline's 60/60 is development evidence confounded by fallback, not pure model accuracy. The final prompt subsequently replaced its language literal with the same configured language list before registration; no fresh live prompt accuracy is inferred.

The older pre-fix 6/48 accepted provider outputs lacked per-case rejection reasons, so their other 42 reasons cannot be reconstructed. Current diagnostics distinguish quota/transport, confidence gate, schema/enum/language and injection bypass. The new dev live run observed accepted=6, quota=54; it did not establish that every old rejection was quota. Tests exercise the other rejection paths. High-risk detection remains independent and rule-based.

Evidence: [development baseline](verification/revision-t4-dev-baseline-offline.json), [initial live diagnosis](verification/revision-t4-dev-baseline-live.json), [final dev replay](verification/revision-t4-dev-final-replay.json), [weight/rank sweep](verification/revision-t4-dev-final-tuning.json), [component sweep](verification/revision-t4-dev-component-tuning.json), [published actual-vector manifest](verification/revision-dev-vector-manifest.json), [sentiment dev patterns](verification/revision-t5-dev-after-patterns.json), [sentiment dev live](verification/revision-t5-dev-live.json).

## Preregistered post-fix re-evaluation and all runs

The frozen sets had **already been run pre-fix**: T4 3/20 = 15.00% correct-cited answers, 0/52 false answers; T5 assisted pipeline 22/48 = 45.83%, with six accepted provider decisions (earlier pattern-only baseline 17/48). An earlier T5 JSON-fence diagnostic run is also retained. These are re-evaluations of exposed sets, never claimed as unseen validation. The prior [T4 result](verification/release-t4-heldout-live.json), [T5 result](verification/release-t5-live.json) and [initial T5 protocol-format result](verification/release-t5-before-protocol-fix.json) remain unchanged except local path redaction.

Before step 7, [the protocol](evaluation-preregistration.json) froze source/config hash `980e44338656f551dbfe44b6babfe55972e109539920890619c8b6a8a15ae0c4`. More than 10% terminal provider infrastructure failures invalidates a run. Cases, not retries, form the denominator; every case must finish. At most one rerun is allowed and only with the identical config hash. Successful immutable model/content-keyed vectors may be reused. Classification sessions are unique per case/run. A superseded registration, replaced before any run to make prompt languages config-driven, is retained separately.

| Run | Measured result | Validity / interpretation |
| --- | --- | --- |
| T4 post-fix live run 1, all 72 cases | Answer rate 12/20 = 60.00% (Wilson 95% 38.66–78.12%); correct-cited rate 12/20 = 60.00% (Wilson 95% 38.66–78.12%); false-answer rate 0/52 = 0.00% (Wilson 95% 0.00–6.88%); wrong answers on supported cases 0 | **INVALID**: 10/72 = 13.89% infrastructure failures. These are descriptive observed counts, not a valid improved accuracy claim. |
| T4 optional run 2 | Not started | User selected quota-limited completion. No rerun or additional tuning. |
| T5 registered post-fix live run | Not started | Provider daily quota was exhausted; no post-fix model-assisted accuracy is available. |
| T5 separate post-fix fallback-only re-evaluation | 20/48 = 41.67% (Wilson 95% 28.85–55.72%) | All 48 used patterns; zero provider calls. Model-assisted denominator is 0. This is the revised fallback's result on previously exposed labels, not a valid live-provider run. |

T4 final decision counts: `{"ambiguity": 4, "answer": 12, "grounding_verifier": 2, "provider_failure": 10, "rank_margin": 14, "threshold": 30}`. No embedding batch errors occurred in this run; 10 terminal generation-provider failures blocked evidence answers. Other refusals came from threshold, rank/margin, ambiguity and the grounding verifier. All outcomes and component traces are recorded, with no changes based on those outcomes.

The provider returned quota ID `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, value 20. The user chose to finish with quota-limited evidence. The orchestration was stopped after complete T4 run 1 and before its optional rerun; later planned live classification was skipped. A separate real translation probe recorded 0/3 successful live translations. All three fell back after HTTP 429 and preserved the synthetic entity bytes. **Successful live translation remains unverified**; scripted provider tests are not live success, and structural byte checks do not certify meaning.

Evidence: [T4 complete post-fix run](verification/revision-t4-postfix-run1.json), [T5 fallback-only result](verification/revision-t5-postfix-fallback-only.json), [quota-limited completion decision](verification/revision-quota-limited-decision.json), [translation probe](verification/revision-translation-live.json), [sequence stdout](verification/revision-postfix-sequence.txt).

## Provider reliability, isolation and data integrity

Generation, embeddings and translation use bounded HTTP 429 retries, Retry-After/Google RetryInfo and Clock backoff. Waits/attempts stay within the original request deadline; a longer hint fails without sleeping past it. Evaluation scripts pace requests and wait cooldowns before starting the next request deadline. Customer requests do not impose global evaluation spacing. Quota failures produce an explicit status; retries cannot manufacture daily quota.

The classifier cache is bounded to 256 entries with 120-second Clock TTL, scoped by hashed session, masked text and masked history hash plus model/config/resource identity. It stores successful validated classifications, not raw PII or failure successes. Changed history/session/config and expired entries do not reuse decisions. Injection bypass and strict six-label enum/confidence/language checks precede acceptance. High-risk rules remain separate even when the provider is unavailable or predicts positive.

CI verifies frozen corpus hashes and scans implementation, prompts, resources, synonyms and golden examples for complete normalized held-out questions/messages, including AST string literals. Adversarial tests prove these guards fail on planted contamination. This catches full-text leakage, not every possible partial semantic contamination. The original task documents, FAQ dataset bytes and all original test functions remain. The only historical assertion generalization was the approved Tesseract version-format check; no test was weakened in this revision.

Tracked documentation and verification files have local workstation/runner paths and usernames replaced by neutral tokens. [The manifest](verification/revision-path-redactions.json) maps original to redacted file hashes. Archive metrics, verdicts, timestamps and historical hash fields are preserved; a historical hash may identify pre-redaction bytes. Public repository identities, legitimate container paths and API routes retain meaning. This is a current-file redaction, not Git history rewriting.

## Customer UI and deployment

The FastAPI customer page at `/` provides chat, uploads and owner-bound tickets. Rendering uses textContent and DOM element creation; keys are not persisted in the browser. Restricted origins, CSP, request/upload-size gates and Clock rate budgets protect entry points. No admin approval/activation controls appear in the customer UI. Docker includes eng/hin/tel/spa Tesseract packs, uses UID 1000 and one worker. [Render guide](deploy-render.md) documents sleep stopping scheduler/SLA/retention work and ephemeral disk losing local state. Live URL: **not deployed**. [Recording script](demo-script.md) is delivered; no completed video is claimed.

## Test evidence and reproduction

Every approved step ran the full pytest suite and Ruff before its commit. Local final command output, copied from the actual run:

```text
python -X utf8 -m pytest -q --basetemp .verification/pytest-step8
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 81%]
...................................................................      [100%]
============================== warnings summary ===============================
.runtime\python311\Lib\site-packages\fastapi\testclient.py:1
  WORKSPACE\.runtime\python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
355 passed, 1 warning in 86.75s (0:01:26)
```

Ruff command: `python -m ruff check .` -> `All checks passed!`. The existing Starlette/httpx deprecation warning is retained. [Final pytest stdout](verification/revision-step8-pytest.txt), [final Ruff stdout](verification/revision-step8-ruff.txt), [step 7 pytest](verification/revision-step7-pytest.txt). [CI](https://github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot/actions/workflows/ci.yml) installs dependencies/OCR on fresh Ubuntu and Windows checkouts, runs frozen-hash/contamination checks, Ruff and pytest, and builds Docker/checks OCR. Its final commit result is verified in the release handoff.

A fresh local application clone of step 7 commit 5905d7b followed the README Windows bootstrap: official Python 3.11.9, pinned dependencies, tagged language resources and OCR checks. Existing host Tesseract was reused; this was not a fresh operating system. All 48 runtime application/config/resource/dependency/workflow/Docker files compared equal at documentation snapshot daaaf98. The later CI-only repair below changes the workflow, leaving the other 47 files unchanged. The final three additional tests concern documentation redaction; report/export maintenance files are separate. [Install stdout](verification/revision-fresh-install.txt), [runtime source parity before CI repair](verification/revision-fresh-source.json).

```text
python -X utf8 -m pytest -q --basetemp .verification/pytest-fresh
352 passed, 1 warning in 81.04s (0:01:21)
python -m ruff check .
All checks passed!
```

[Complete fresh-clone pytest stdout](verification/revision-fresh-pytest.txt), [fresh Ruff stdout](verification/revision-fresh-ruff.txt), [preserved tests/archive checks](verification/revision-preservation.json), [secret/task/dataset/link checks](verification/revision-integrity.json). Earlier release install logs retain their original dates and are not substituted for this check.

## Hosted CI prerequisite repair

The eight approved commits ended at daaaf98. Ubuntu pytest/Ruff and Docker passed, but Windows failed before tests: Chocolatey's package feed returned HTTP 503 and installed zero packages, leaving no Tesseract executable. A same-commit failed-job rerun had the same cause. Both [initial Windows log](verification/revision-ci-windows-attempt1.txt) and [retry log](verification/revision-ci-windows-attempt2.txt) are retained with local paths redacted. These CI retries are separate from the preregistered provider evaluation; no additional provider evaluation was run.

A focused follow-up changes only CI prerequisites and associated documentation/evidence. Windows downloads the pinned vendor Tesseract 5.4.0.20240606 installer and verifies SHA-256 against [Microsoft's winget manifest](https://raw.githubusercontent.com/microsoft/winget-pkgs/master/manifests/u/UB-Mannheim/TesseractOCR/5.4.0.20240606/UB-Mannheim.TesseractOCR.installer.yaml) before silent installation. It checks installer exit status and executable presence, then adds the install directory to the runner PATH. Application code, registered source/config hash, all tests and provider measurements remain unchanged. The full suite/Ruff are rerun before this corrective commit; [pytest stdout](verification/revision-ci-install-repair-pytest.txt), [Ruff stdout](verification/revision-ci-install-repair-ruff.txt), [installer checksum/source parity evidence](verification/revision-ci-install-repair.json). The final hosted result is linked in the release handoff.

Development reproduction: `python scripts/evaluate_development.py --help`; `python scripts/tune_retrieval_dev.py --help`; `python scripts/evaluate_sentiment_development.py --help`. Offline regressions use the published real-vector artifact and deterministic quotation, with no API calls. `python scripts/check_holdouts.py` validates the frozen data and text-leakage guard. `python scripts/redact_document_paths.py --check` verifies current documentation path redaction. Do not rerun a registered run index or overwrite its evidence. The optional live rerun remains unconsumed but was declined for quota-limited completion.

## Remaining limits

No valid post-fix live retrieval/classification quality claim is available. The fallback-only sentiment score is 20/48; dev success does not establish generalization. Zero false answers on these small sets is not universal safety. Rule-based risk, entity extraction, requested-attribute gates and injection detection miss unrepresented wording. Source-grounding verification rejects unsupported paraphrases; translated wording is not independent policy evidence. OCR is tested on synthetic fixtures, not authenticity or arbitrary layouts. The old training chain remains unverified although its source and FAQ content are preserved. External helpdesk/paging delivery, real agent availability, distributed scheduling, encrypted storage, forensic erasure and production reliability are unverified. SQLite and timers require one running worker with persistent writable storage. Only gemini-2.5-flash has proven generation among the documented candidates; the example fallback list remains empty.
