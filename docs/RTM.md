# Requirements Traceability Matrix (RTM) - Task 4

## Requirements Traceability

| Requirement Text | File:Function | Test Name | Status |
| :--- | :--- | :--- | :--- |
| Document metadata: version, product, region, access_level, effective_date, expiry_date, doc_family (for conflict grouping). | `core/store.py:Document` & `core/retrieval.py:PolicyRetrievalEngine.ingest_document` | `tests/test_foundation.py:test_sqlite_repositories` | PASS |
| Retrieval order is fixed: (1) authorise by caller role | `core/retrieval.py:PolicyRetrievalEngine.retrieve` | `tests/test_task4.py:test_restricted_doc_not_retrieved` | PASS |
| (2) validity filter by as_of date (default clock.now(); if the question names a past date, parse it and use it; ignore future-dated and expired for current questions) | `core/retrieval.py:PolicyRetrievalEngine._parse_query_as_of_date`, `retrieve` | `tests/test_task4.py:test_expired_policy_ignored_for_current`, `tests/test_task4.py:test_future_dated_ignored_for_current`, `tests/test_task4.py:test_historical_question_uses_policy_active_on_date` | PASS |
| (3) semantic search over only the survivors | `core/retrieval.py:PolicyRetrievalEngine.retrieve`, `SemanticSearcher` | `test_restricted_and_injected_text_never_reaches_search_or_prompt` proves filtering; search is lexical, not general semantic retrieval | PARTIAL |
| (4) conflict resolution: within a doc_family+product+region keep the latest applicable version | `core/retrieval.py:PolicyRetrievalEngine.retrieve` | `tests/test_task4.py:test_conflicting_policies_latest_wins` | PASS |
| (5) similarity threshold | `core/retrieval.py:PolicyRetrievalEngine.retrieve` | `tests/test_task4.py:test_refuses_when_no_evidence` | PASS |
| Filtering happens BEFORE search, not after. Restricted text must never reach the LLM prompt. | `core/retrieval.py:PolicyRetrievalEngine.retrieve` | `tests/test_task4.py:test_restricted_doc_not_retrieved` | PASS |
| Answer generation: factual claims only from retrieved chunks; each answer cites source (doc id, version, section). | `core/retrieval.py:PolicyRetrievalEngine.query` | `tests/test_task4.py:test_citation_present_on_every_factual_answer` | PASS |
| Post-generation verifier checks every claim sentence is supported by a cited chunk; unsupported claims are removed or the answer becomes a refusal. | `core/retrieval.py:PolicyRetrievalEngine.verify_claim`, `query` | `tests/test_task4.py:test_unsupported_claim_detected` | PASS |
| No evidence or ambiguous evidence -> refuse or ask a clarifying question (never guess). | `core/retrieval.py:PolicyRetrievalEngine.query` | `tests/test_task4.py:test_refuses_when_no_evidence`, `tests/test_task4.py:test_ambiguous_asks_clarification` | PASS |
| Documents are untrusted: run the injection detector on chunks at ingest and at retrieval; flagged instructions are neutralised and never obeyed. | `core/retrieval.py:PolicyRetrievalEngine.ingest_document`, `query` & `core/security.py:detect_prompt_injection` | `tests/test_task4.py:test_prompt_injected_doc_ignored` | PASS |
| Fixture corpus in data/sample_docs/ covering every case above. | `data/sample_docs/*.json` | All 10 named Task 4 tests load and exercise the fixture corpus | PASS |
| Requirements Trace Matrix (docs/RTM.md) for T4. | `docs/RTM.md` and `docs/audit-rtm.md` | Sentence/row audit and existing Task 4 trace table | PASS |
| pytest output pasted. | `docs/verification/audit-final-pytest.txt`, `docs/audit.md` | Actual full-suite command output | PASS |
| Demo script that prints real outputs. | `scripts/demo_t4.py` | Existing executable fixture demo; historical captured output `docs/verification/demo-t4.txt` | PASS |

## Test Execution Evidence

The 21-test output below is historical Antigravity evidence. Current Python 3.11 results and Task 1 evidence are in `docs/verification/pytest.txt` and `docs/README.md`. PASS rows denote tested local scenarios, not production certification.

Command:
```bash
.\.venv\Scripts\pytest -q
```

Output:
```
.....................                                                    [100%]
21 passed in 0.42s
```

## Task 1 - controlled knowledge updates

Status applies to the named offline tests on Python 3.11, with real SQLite and FakeClock/FakeLLM. Full command output is saved in `docs/verification/pytest.txt`.

| Requirement text from T1.md | File:function | Test name | Status |
| --- | --- | --- | --- |
| Reuse core/* and the RAG store from P1; do not duplicate. | `core/store.py:SnapshotRepository`, `core/updates.py:UpdateService`, `app/chatbot.py:set_update_service` | `test_management_api_shares_active_rag_store` | PASS |
| Ingestion: normalise then sha256 each file. | `core/ingestion.py:normalize, read_policy` | `test_duplicate_documents_detected`, `test_only_new_or_modified_processed` | PASS |
| Unchanged -> skip. | `core/updates.py:UpdateService._ingest` | `test_only_new_or_modified_processed` | PASS |
| Same content under a different name -> duplicate, logged and skipped. | `core/updates.py:UpdateService._ingest` | `test_duplicate_documents_detected` | PASS |
| Changed -> new version. | `core/updates.py:UpdateService._ingest` | `test_only_new_or_modified_processed` | PASS |
| Validation -> quarantine/ with a reason code (empty, corrupt, unsupported type, missing metadata, oversize, injection-flagged). | `core/ingestion.py:read_policy, quarantine` | `test_invalid_file_quarantined` (all six reason codes) | PASS |
| Never silently dropped. | `core/updates.py:UpdateService._ingest` | `test_invalid_file_quarantined` verifies preserved bytes, manifest, result and audit | PASS |
| Versioning: immutable snapshots; one ACTIVE pointer; rollback(version) swaps the pointer atomically. | `core/store.py:SnapshotRepository.create_snapshot, swap_active`, immutable SQL triggers | `test_manual_rollback`, `test_atomic_pointer_compare_and_swap`, `test_snapshot_and_schedule_survive_restart` | PASS |
| Quality gate on a candidate snapshot: run a golden Q&A set (data/golden/) and measure accuracy and grounding (cited-source validity). | `core/updates.py:UpdateService.evaluate, _quality_gate` | `test_quality_gate_rejects_accuracy_drop`, `test_quality_gate_rejects_grounding_drop` | PASS |
| Reject if either is lower than the active version (tolerance configurable, default 0). | `core/updates.py:UpdateService._quality_gate`, `config/default.yaml:updates` | `test_quality_gate_rejects_accuracy_drop`, `test_quality_gate_rejects_grounding_drop`, `test_quality_tolerance_hot_reload` | PASS |
| Report real numbers. | `core/updates.py:UpdateService._quality_gate`, `scripts/demo_t1.py:run_demo` | Quality tests assert measured active/candidate fractions; saved `demo-t1.txt` | PASS |
| Scheduler: configurable run time, driven by Clock. | `core/updates.py:UpdateService.schedule, tick`, `app/chatbot.py:maintenance_worker` | `test_retry_15_30_60`, `test_daily_scheduler_discovers_files_added_after_schedule` | PASS |
| On failure retry at +15, +30, +60 minutes, then mark FAILED and alert. | `core/updates.py:UpdateService.tick` | `test_retry_15_30_60`, `test_late_failure_retry_offsets_start_at_failure` | PASS |
| Exactly these three retries. | `core/updates.py:UpdateService.tick` | `test_retry_15_30_60` verifies four attempts and one durable alert | PASS |
| Activation: approved updates are held until the configured maintenance window; activate only inside it. | `core/updates.py:UpdateService.approve, inside_window, _activate, tick` | `test_activation_blocked_outside_window`, `test_activation_inside_window`, `test_overnight_maintenance_window` | PASS |
| After activation run health checks; if they fail within 5 minutes, auto-rollback and record why. | `core/updates.py:UpdateService.check_health` | `test_auto_rollback_on_health_failure_within_5min`, `test_failing_health_check_immediately_after_activation` | PASS |
| Access control: roles for ingest / approve / activate / rollback / view. | `core/updates.py:UpdateService.authorize`, `core/config.py:AppConfig.api_keys`, `config/default.yaml:roles` | `test_separate_management_roles`, `test_management_key_does_not_grant_query_permission` | PASS |
| Unauthorised calls rejected and audited. | `core/updates.py:UpdateService.authorize`, `app/chatbot.py:management_call` | `test_unauthorised_access_rejected` (five operations), `test_management_api_shares_active_rag_store` | PASS |
| Prompt-injection protection on ingested docs; sensitive-data masking in logs; metrics: latency, failures, confidence, escalations. | `core/ingestion.py:read_policy`, `core/audit.py:AuditLogger`, `core/metrics.py:MetricsCollector`, `core/updates.py:UpdateService` | `test_invalid_file_quarantined`, `test_audit_masks_secret_fields_and_values`, `test_retry_15_30_60`, `test_sqlite_repositories` | PASS |
| test_no_rollback_after_5min_window | `core/updates.py:UpdateService.check_health` | `test_no_rollback_after_5min_window` | PASS |
| test_service_outage_during_update (vector store down, LLM down) | `core/updates.py:UpdateService.tick, _quality_gate` | `test_service_outage_during_update` (both dependencies) | PASS |
| test_manual_rollback | `core/updates.py:UpdateService.rollback` | `test_manual_rollback` | PASS |
| Finish with RTM for T1, pytest output, and a demo script that simulates a full maintenance-window day. | `docs/RTM.md`, `docs/verification/pytest.txt`, `scripts/demo_t1.py:run_demo` | Current suite output and actual `demo-t1.txt` include day assertions, quality scores, activation and both rollback paths | PASS |

All 13 required named Task 1 tests exist in `tests/test_task1.py`; parametrization exercises all quarantine reasons, all unauthorized operations, and both update dependency outages. Local alerts are durable audit events; external notification delivery is not claimed.

## Task 6 - multilingual conversation and sessions

PASS means the stated local scenario was exercised on Python 3.11 with FakeClock/FakeLLM and real SQLite. Resource recognition is bounded customer-support logic, not a general language benchmark. Raw suite output: `docs/verification/pytest-t6.txt`; actual corpus measurements: `docs/verification/t6-evaluation.json`.

| Requirement text from T6.md | File:function | Test name | Status |
| --- | --- | --- | --- |
| Reuse core/* and the chatbot orchestrator. | `core/conversation.py:ConversationService.turn`, `core/store.py:SessionRepository`, `app/chatbot.py:handle_query, lifespan` | `test_api_multilingual_context_and_owner_binding` | PASS |
| Languages, thresholds, and session timings come from config only. | `core/language.py:LanguageResources.load`, `core/sessions.py:SessionManager._expire, conversation`, `config/default.yaml` | `test_config_changes_thresholds_without_code`, `test_session_timings_are_hot_configurable` | PASS |
| Default extra languages: hi, te, es. | `config/default.yaml:languages`, `resources/languages/*.json` | `test_fixture_conversations_per_language` (en/hi/te/es) | PASS |
| Adding a language must need config and resources, not code changes. | `core/language.py:LanguageResources.load, LanguageProcessor.analyze` | `test_language_added_using_config_and_resources_only` enables a temporary fr resource | PASS |
| Per-message language + intent detection with confidence. | `core/language.py:LanguageProcessor.detect, analyze`, `core/conversation.py:ConversationService.turn` | `test_language_switch_mid_conversation`, `test_unseen_conversation_set` | PASS |
| Handle code-mixing, switching mid-conversation, and romanised input (e.g. Hinglish). | `core/language.py:LanguageProcessor.detect, transform` | `test_mixed_language_message`, `test_language_switch_mid_conversation`, `test_misspelling_and_transliteration` | PASS |
| Below threshold -> ask a clarification. | `core/conversation.py:ConversationService.turn` | `test_low_confidence_asks_clarification`, `test_config_changes_thresholds_without_code` | PASS |
| Entity protection: extract names, order IDs, dates, product codes BEFORE any translation or normalisation, replace with placeholders, and restore them after. | `core/entities.py:EntityProtector.protect, ProtectedText.restore`, `core/language.py:LanguageProcessor.analyze, localize` | `test_entities_preserved_across_languages`, `test_native_names_named_dates_and_leading_zero_orders` | PARTIAL; see audit A-OPEN-5 |
| Test that they survive byte-for-byte. | `core/entities.py:ProtectedText.restore` | `test_entities_preserved_across_languages` checks original UTF-8 bytes, decomposed accents, IDs, dates, source citations and localized output | PARTIAL; see audit A-OPEN-5 |
| Context window: keep at least 10 messages (configurable). | `core/sessions.py:SessionManager.append, conversation` | `test_context_retained_10_messages` verifies both 10 and 20-message windows | PASS |
| Handle corrections ("sorry, order 4521 not 4512": latest value wins, old one recorded as superseded) and multiple requests in one message. | `core/conversation.py:ConversationService.turn`, language resource correction spans/split patterns | `test_correction_overrides_earlier_value`, `test_multiple_requests_in_one_message`, `test_multiple_requests_keep_separate_entity_bindings`, `test_entities_from_one_request_do_not_pollute_another_request` | PASS |
| Sessions: strict isolation per session id (no shared mutable state; prove with a concurrent test). | `core/store.py:SessionRepository.load_session, save_session`, `core/sessions.py:SessionManager.conversation` | `test_concurrent_sessions_isolated` uses eight simultaneous barrier-synchronized requests; `test_same_session_concurrent_updates_do_not_lose_messages` | PASS |
| End after 30 min inactivity via Clock. | `core/sessions.py:SessionManager._expire, expire_idle` | `test_session_expires_after_30min` covers 29:59 and exactly 30:00 | PASS |
| Return within 24h -> restore conversation summary; after 24h -> new session. | `core/sessions.py:SessionManager.conversation, summarize` | `test_return_within_24h_restores_summary`, `test_return_after_24h_new_session`, `test_exactly_24h_restores_and_clock_reset_is_not_wall_time` | PASS |
| All configurable. | `config/default.yaml:conversation, timings, thresholds` | `test_session_timings_are_hot_configurable`, `test_context_retained_10_messages`, `test_config_changes_thresholds_without_code` | PASS |
| test_unseen_conversation_set | `core/language.py:LanguageProcessor.analyze`, `tests/fixtures/unseen.json` | `test_unseen_conversation_set` asserts disjoint wording, language, intent, and no unwanted clarification | PASS |
| Create 30+ fixture conversations per language in tests/fixtures/. | `scripts/create_t6_fixtures.py:write_fixtures`, `tests/fixtures/{en,hi,te,es}.json` | `test_fixture_conversations_per_language` verifies 35 unique initial messages and three turns per conversation in each language | PASS |
| Finish with RTM for T6 and pytest output. | `docs/RTM.md`, `docs/verification/pytest-t6.txt`, `docs/README.md` | Captured full-suite command output; all 14 required named tests exist | PASS |

Additional Task 6 checks cover placeholder spoof/loss, persistent session restart, owner mismatch, API integration, provider-failure atomicity, native names/dates, and corrected entity bindings. No live-provider or unrestricted translation result is inferred from these passes.

## Provider fallback and Task 6 live recheck - 2026-10-14

Source: `docs/tasks/provider-fallback.md`, created from the current user's request. Current suite output: `docs/verification/pytest-provider.txt`. Model choices and observed live limits: `docs/provider_fallback.md`.

| Requirement text | File:function | Test/evidence | Status |
| --- | --- | --- | --- |
| Preserve the supplied Google key and never print it. | Local dotenv edits; provider API uses x-goog-api-key header | Original parsed key equality asserted after edits; sanitized env/model/probe output contains no key | PASS |
| Configure only text models that official Google documentation lists as free-tier eligible and models.list exposes. | `config/default.yaml:provider`, `.env.example`, `core/llm.py:RealProviderAdapter.configured_models` | `test_fallback_deduplication_and_no_paid_model_selection`, actual `provider-models.json`, official pricing links | PASS |
| Keep one key; try configured models in order on recoverable availability/quota/network errors. | `core/llm.py:RealProviderAdapter.generate` | `test_fallback_on_recoverable_http_status`, `test_fallback_on_transport_timeout`, `test_env_fallback_models_used_without_key_rotation` | PASS |
| Bound attempts, HTTP timeouts and dispatch budget; cool down failed models through Clock and honor Retry-After. | `core/llm.py:RealProviderAdapter.generate, _cool_down` | `test_provider_request_budget_and_max_attempts_are_configurable`, `test_all_models_unavailable_is_real_failure_with_cooldown`, `test_retry_after_http_date_uses_clock` | PASS |
| Fail visibly when no model can serve the request. Do not use mocked success or downgrade to FakeLLM. | `core/llm.py:ProviderUnavailableError`, `app/chatbot.py:handle_query` | `test_all_models_unavailable_is_real_failure_with_cooldown`; actual initial live failure report retained | PASS |
| Do not switch models to bypass authentication errors, invalid requests or safety refusals. | `core/llm.py:RealProviderAdapter.generate` | `test_authentication_and_bad_requests_do_not_switch_models`, `test_safety_blocks_never_trigger_fallback` | PASS |
| Reverify Task 6's existing required scenarios and preserve its fixture corpus, RTM and actual pytest output. | Existing Task 6 modules, `tests/test_task6.py`, `scripts/evaluate_t6.py` | All 14 required named tests, 35 three-turn conversations per configured language, actual current pytest/corpus output | PASS |
| Multilingual request filler must not hide retrieved evidence or alter protected entities/negation. | `core/language.py:LanguageProcessor.retrieval_text`, language JSON resources | `test_multilingual_request_filler_does_not_hide_grounded_policy`, `test_retrieval_filler_removal_preserves_entities_and_negation` | PASS |
| Metadata scope reaches the provider as authorized untrusted data, while curated translation accepts citation punctuation spacing. | `core/retrieval.py:PolicyRetrievalEngine.query`, `core/language.py:LanguageProcessor.localize` | `test_authorized_policy_metadata_reaches_provider_as_untrusted_data`, `test_curated_translation_accepts_citation_punctuation_spacing` | PASS |
| Live provider connectivity and four explicit policy questions. | `scripts/check_live_task6.py:probe` | Actual real Gemini 2.5 Flash results with verified citations for en/hi/te/es in `task6-live-provider.json`; synthetic fixtures and fixed Clock only | PASS |

Model listing/free eligibility does not certify the project's billing tier. Backup successful generation and real customer-policy quality remain unverified; no production or general-language-accuracy claim follows from this smoke check.

## Task 5 - sentiment, independent risk, tone, and escalation

Source: `docs/tasks/T5.md`, preserved from the user request because the file was absent. PASS means the named local scenario was exercised using the shared FakeClock/FakeLLM and real SQLite on Python 3.11. It does not imply perfect classification of arbitrary wording. Raw full-suite evidence: `docs/verification/pytest-task5.txt` (201 passed, one preserved dependency warning). Details and API: `docs/task5.md`.

| Requirement text from T5.md | File:function | Test / evidence | Status |
| --- | --- | --- | --- |
| Read RULES.md, docs/tasks/T5.md. Reuse core/*, the language layer from P3, and the Clock. | `core/sentiment.py:SentimentClassifier`, `core/escalation.py:EscalationService`, existing language/config/security/audit/metrics/store, `app/chatbot.py:handle_query` | `test_api_support_layer_and_resolution_access`, `test_simulated_time_change`, `test_tone_changes_policy_unchanged` | PASS |
| Implement Task 5 exactly as in T5.md. | `core/sentiment.py`, `core/risk.py`, `core/tone.py`, `core/escalation.py`, shared store and orchestrator | Named scenarios below; interpretation/provenance in `docs/task5_assumptions.md` | PARTIAL; see audit A-OPEN-4 |
| Classifier returns label + confidence for: positive, neutral, negative, frustrated, urgent, sarcastic. | `core/sentiment.py:Sentiment, SentimentClassifier.classify`, language support resources | `test_classifier_labels_and_confidence_from_authored_set` asserts all six expected explicit labels in each language and confidence bounds | PASS |
| It takes the current message AND recent history (sarcasm and frustration depend on history). | `core/sentiment.py:SentimentClassifier.classify`, `core/escalation.py:EscalationService.observe` | `test_sarcasm_detected_with_history` compares identical current text with and without history for both sarcasm and frustration | PASS |
| Multilingual via the P3 language layer. | `core/language.py:LanguageProcessor.protect, transform, detect`, `resources/languages/{en,hi,te,es}.json:support` | `test_classifier_labels_and_confidence_from_authored_set`, `test_multilingual_risk_independent_of_intent`, `test_tone_changes_policy_unchanged` | PASS |
| HIGH-RISK detection (account compromise, duplicate payment, legal threat) is a SEPARATE detector from sentiment, so a calm high-risk message still escalates. | `core/risk.py:HighRiskDetector.detect`, `core/escalation.py:EscalationService.observe` | `test_calm_account_compromise_escalates`, `test_calm_duplicate_payment_escalates`, `test_calm_legal_threat_escalates` assert neutral label and independent risk-triggered records | PARTIAL; see audit A-OPEN-4 |
| Test this explicitly. | `tests/test_task5.py:calm_escalation` | Three individually named calm high-risk tests above; `test_provider_failure_cannot_suppress_escalation`, `test_injected_message_risk_still_escalates` | PASS |
| Tone adaptation is a presentation layer only. | `core/tone.py:TonePresenter.present`, `core/conversation.py:ConversationService.turn`, `app/chatbot.py:QueryResponse` | `test_tone_changes_policy_unchanged` checks separate preface/display fields | PASS |
| Policy facts come from the RAG answer and must be identical with and without tone changes. | Existing `core/retrieval.py:PolicyRetrievalEngine.query`, `core/tone.py:TonePresenter.present` | `test_tone_changes_policy_unchanged` retrieves real fixture evidence with FakeLLM; toggles config and compares exact body bytes and citations in en/hi/te/es | PASS |
| Test with a diff of facts. | `tests/test_task5.py:test_tone_changes_policy_unchanged` | Actual `difflib.unified_diff` of policy bodies is empty with presentation on/off | PASS |
| Escalation triggers: repeated negative messages (N and window configurable), any high-risk issue, negative conversation unresolved > 15 min (Clock-driven timer). | `core/escalation.py:EscalationService.observe, _timer, tick`, config count/window, existing `timings.escalation_timeout_minutes` | `test_repeated_negative_escalates`, three calm risk tests, `test_unresolved_negative_15min_escalates`, `test_simulated_time_change` | PARTIAL; see audit A-OPEN-4 |
| Routing by time: urgent + outside business hours -> on-call queue; normal complaints outside hours -> scheduled next working day (skip weekends/holidays from config). | `core/escalation.py:EscalationRouter.route`, shared business calendar/timezone/Clock | `test_urgent_after_hours_goes_oncall`, `test_normal_after_hours_next_working_day`, `test_business_hour_boundaries`, `test_urgency_upgrades_scheduled_record` | PASS |
| Every escalation record stores: reason, activated condition, conversation summary (masked). | `core/escalation.py:EscalationService._record, masked`, `core/store.py:EscalationRepository.issue`, shared `core/security.py:mask_pii` | `test_escalation_record_complete` verifies stored/audited reason, condition, summary and names/email/phone/Luhn-card masking while preserving order ID | PASS |
| test_sarcasm_detected_with_history | `core/sentiment.py:SentimentClassifier.classify` | `test_sarcasm_detected_with_history` | PASS |
| test_calm_account_compromise_escalates | `core/risk.py:HighRiskDetector.detect`, `core/escalation.py:EscalationService.observe` | `test_calm_account_compromise_escalates` | PASS |
| test_calm_duplicate_payment_escalates | Same independent risk path | `test_calm_duplicate_payment_escalates` | PASS |
| test_calm_legal_threat_escalates | Same independent risk path | `test_calm_legal_threat_escalates` | PASS |
| test_repeated_negative_escalates | `core/escalation.py:EscalationService.observe` | `test_repeated_negative_escalates` checks configurable count/window and duplicate suppression | PASS |
| test_urgent_after_hours_goes_oncall | `core/escalation.py:EscalationRouter.route` | `test_urgent_after_hours_goes_oncall` | PASS |
| test_normal_after_hours_next_working_day | `core/escalation.py:EscalationRouter.route` | `test_normal_after_hours_next_working_day` skips Saturday/Sunday and Monday holiday | PASS |
| test_unresolved_negative_15min_escalates | `core/escalation.py:EscalationService._timer, tick` | `test_unresolved_negative_15min_escalates` checks no record at 900 seconds, record at 901 with no new message | PASS |
| test_simulated_time_change | `core/escalation.py:EscalationRouter.route, EscalationService.tick` | `test_simulated_time_change` tests business-hour changes and runtime timer reconfiguration | PASS |
| test_tone_changes_policy_unchanged | `core/tone.py:TonePresenter.present`, `core/conversation.py:ConversationService.turn` | `test_tone_changes_policy_unchanged` (four languages) | PASS |
| test_escalation_record_complete | `core/escalation.py:EscalationService._record` | `test_escalation_record_complete` | PASS |
| Finish with RTM for T5 and pytest output. | `docs/RTM.md`, `docs/README.md`, `docs/verification/pytest-task5.txt` | Actual captured `.\.runtime\python311\python.exe -X utf8 -m pytest -q`: 201 passed, one warning | PASS |
| Report classifier accuracy ONLY from a labelled test set you created, with the set committed. | `scripts/evaluate_t5.py:evaluate`, `tests/fixtures/task5/labelled_sentiment.json` | Actual `docs/verification/t5-classifier-evaluation.json`: 52/60 (86.67%), 13/15 per language, all eight misses preserved. Dataset and provenance committed as `681aedc2761e861458e43e72a1d81c47928bffee` | PASS |

Additional checks cover concurrent issue deduplication/owner isolation, transaction failure atomicity, explicit resolution and new episodes, positive messages not falsely resolving issues, restart/expiration survival, negated/hypothetical risk, urgency upgrades, API RBAC, injected input, provider failure, assistant/failed-turn history, background timers during maintenance failures, and complete spaced-card masking. The authored classifier set is diagnostic evidence only; no independent or production accuracy claim is made.


## Task 2 - uploads, extraction, comparison, jobs and retention

Source: docs/tasks/T2.md, preserved from the user request because the file was absent. Scope interpretation: docs/task2_assumptions.md. PASS denotes the stated local scenario, using actual file bytes, real Tesseract/PDFium, shared FakeClock and fake/mocked providers. It does not claim universal malicious-file rejection or arbitrary-layout OCR accuracy. Actual full-suite result: 248 passed, 1 warning in 53.07s. See docs/verification/pytest-task2.txt and docs/task2.md.

| Requirement text from T2.md | File:function | Test / evidence | Status |
| --- | --- | --- | --- |
| Read RULES.md, docs/tasks/T2.md. Reuse core/*, security, and Clock. | Shared config/security/audit/metrics/Clock/LLMClient/SQLite; app/chatbot.py:lifespan, maintenance_worker | test_api_owner_binding_delivery_and_early_body_limit, test_application_worker_purges_bytes_without_customer_poll | PASS |
| Implement Task 2 exactly as in T2.md. | core/upload_gate.py, ocr.py, document_extraction.py, upload_fields.py, upload_processing.py, uploads.py; shared store and API | Required named scenarios below; documented scope in docs/task2_assumptions.md | PARTIAL; see audit A-OPEN-3 |
| Upload gate first: validate magic bytes, size, type allowlist, decompression-bomb limits, and active content in PDFs. | app/upload_api.py:UploadBodyLimit; core/upload_gate.py:UploadGate.validate, _png, _jpeg, _pdf, bounded_inflate | test_unsafe_file_rejected, test_gate_adversarial_variants_before_decoding, test_image_bomb_limits_apply_before_decoder, test_pdf_compression_limit_survives_name_obfuscation | PASS |
| Unsafe -> reject and audit before any parsing. | core/upload_gate.py:UploadGate.validate, core/uploads.py:UploadService.submit, _run | test_unsafe_file_rejected replaces image/PDF/processing entry points with fail-fast spies and checks the rejection audit and absent stored bytes/jobs; structural header inspection is the gate itself | PASS |
| Extraction: OCR (verify Tesseract and language packs are installed with a real check; document install steps) and PDF text with a raster fallback. | core/ocr.py:TesseractOCR.check, recognize; core/document_extraction.py:DocumentExtractor.extract; scripts/check_ocr.py; docs/task2.md | test_real_tesseract_and_all_configured_packs_installed, test_actual_fields_have_confidence_and_source_regions (native and scanned PDF); actual task2-ocr-installation.json, language hashes and documented Windows install commands | PASS |
| Extract order ID, date, amount, product info, error code. | core/upload_fields.py:extract_fields; config/default.yaml:uploads.field_patterns | test_actual_fields_have_confidence_and_source_regions asserts all five expected values on actual PNG/JPEG/native PDF/scanned PDF | PASS |
| Every field returns value, confidence, and source region. | core/ocr.py:TextLine; core/document_extraction.py:DocumentExtractor._native_line; core/upload_fields.py:extract_fields | test_actual_fields_have_confidence_and_source_regions checks bounded confidence, nonempty actual rectangles, page, units and origin | PASS |
| Missing -> null. | core/upload_fields.py:extract_fields | test_missing_field_not_invented checks null values and regions with zero confidence | PASS |
| NEVER infer or fill a missing value. | core/upload_processing.py:UploadProcessor.process; core/upload_fields.py:compare_fields | test_missing_field_not_invented supplies customer-only date/amount/error values and proves none populate document fields; test_sharp_product_without_text_still_routes_to_vision preserves missing fields | PASS |
| Comparison with the customer's message: any mismatch (order ID, amount, date) -> ask for clarification and show what conflicts. | core/upload_fields.py:compare_fields, canonical; core/upload_processing.py:UploadProcessor.process | test_mismatched_invoice_asks_clarification checks all three document/customer value pairs; test_customer_bare_amount_order_date_conflicts_are_not_skipped, test_product_conflicts_still_ask_clarification_without_model | PASS |
| Low quality (blur score, OCR confidence below threshold) -> request another file. | core/ocr.py:blur_score; core/document_extraction.py:DocumentExtractor._raster; core/upload_processing.py:UploadProcessor.process | test_blurred_image_requests_new_file, test_low_ocr_confidence_threshold_requests_another_file, test_empty_product_image_does_not_generate_claims | PASS |
| Product images: route to a vision-capable model through the LLMClient interface. | core/llm.py:LLMClient.supports_vision, RealProviderAdapter.generate; core/upload_processing.py:UploadProcessor.process | test_product_uses_vision_interface_and_isolated_ocr_data, test_sharp_product_without_text_still_routes_to_vision, test_gemini_inline_image_contract_and_no_text_only_fallback; separate actual real-provider task2-live-vision.json | PASS |
| If none is configured, say so honestly and return "cannot analyse", not a guess. | core/upload_processing.py:UploadProcessor.process | test_product_without_vision_cannot_analyse, test_product_conflicts_still_ask_clarification_without_model; offline demo explicitly disables model configuration | PASS |
| Text found inside images/PDFs is untrusted DATA. | core/document_extraction.py:check_untrusted; shared core/security.py:isolate_untrusted_data | test_product_uses_vision_interface_and_isolated_ocr_data checks structural boundaries before a model request | PASS |
| Run it through the injection detector; hidden instructions -> reject the file. | core/upload_gate.py:check_instruction_bytes; core/document_extraction.py:check_untrusted; core/uploads.py:UploadService._run | test_prompt_injection_in_image_rejected uses real OCR and proves vision is not called; test_pdf_instructions_or_active_content_rejected covers native, hidden-white, raster-only and active PDFs | PARTIAL; see audit A-OPEN-3 |
| Mask personal and payment data in all logs. | Shared core/audit.py:AuditLogger and core/security.py:mask_pii; core/uploads.py:_run; gate and API omit original filename/raw OCR/customer content | test_pii_masked_in_logs checks persisted and captured logs for name/email/phone/card absence and actual mask tokens | PASS |
| Anything over 30s -> background job queue (states: queued/running/done/failed), notify the customer, and deliver the result when done. | core/uploads.py:UploadService.submit, _dispatch, _run, get, recover; core/store.py:UploadRepository; app/upload_api.py:submit_upload, upload_result | test_delayed_processing_moves_to_queue_and_notifies advances FakeClock beyond 30s while processing is blocked, then releases actual OCR and receives done/result notice; test_pending_job_survives_restart exercises queued/running/done, test_ocr_dependency_outage_fails_honestly exercises failed; test_api_owner_binding_delivery_and_early_body_limit receives HTTP 202 then the completed owner-bound result | PASS |
| Retention: uploaded files deleted after the configured period via Clock-driven purge. | core/uploads.py:UploadService.purge, _path; core/store.py:UploadRepository.expire_upload; app/chatbot.py:maintenance_worker | test_expired_files_deleted, test_application_worker_purges_bytes_without_customer_poll, test_expiry_during_processing_cannot_publish_result | PASS |
| Test deletion actually removes the bytes from disk. | core/uploads.py:UploadService.purge | test_expired_files_deleted reads the original bytes, advances FakeClock to expiry and asserts the path no longer exists; worker integration proves automatic deletion during a maintenance failure | PASS |
| test_blurred_image_requests_new_file | core/ocr.py:blur_score; core/upload_processing.py:UploadProcessor.process | test_blurred_image_requests_new_file | PASS |
| test_mismatched_invoice_asks_clarification | core/upload_fields.py:compare_fields | test_mismatched_invoice_asks_clarification | PASS |
| test_missing_field_not_invented | core/upload_fields.py:extract_fields | test_missing_field_not_invented | PASS |
| test_delayed_processing_moves_to_queue_and_notifies | core/uploads.py:UploadService.submit, get | test_delayed_processing_moves_to_queue_and_notifies | PASS |
| test_expired_files_deleted | core/uploads.py:UploadService.purge | test_expired_files_deleted | PASS |
| test_prompt_injection_in_image_rejected | core/document_extraction.py:check_untrusted | test_prompt_injection_in_image_rejected | PASS |
| test_unsafe_file_rejected | core/upload_gate.py:UploadGate.validate | test_unsafe_file_rejected (three real unsafe/malformed file cases) | PASS |
| test_pii_masked_in_logs | core/audit.py:AuditLogger; core/security.py:mask_pii | test_pii_masked_in_logs | PASS |
| Create real fixture files (clean, blurred, mismatched, injected, malformed) in tests/fixtures/. | scripts/create_t2_fixtures.py:main; tests/fixtures/task2 actual encoded files and README | Real fixture decoding/extraction in the named tests, plus native/scanned PDF, product/no-text, hidden-instruction and active-PDF scenarios | PASS |
| Finish with RTM for T2 and pytest output. | docs/RTM.md, docs/README.md, docs/verification/pytest-task2.txt | Actual captured command: .\.runtime\python311\python.exe -X utf8 -m pytest -q; 248 passed, 1 warning in 53.07s | PASS |

Additional checks cover PNG metadata/expansion bombs, escaped/commented PDF filters, stored-byte tampering before parsers, unsupported MIME/extensions, dependency outage, normalization without missing-field inference, multi-value ambiguity, restart recovery, API permission/owner isolation, request-body limits, expiry during processing, non-text product photos, and audit-before-terminal-failure publication. Queue delivery is authenticated polling; no external notification or production deployment claim is made.

## Task 3 requirements (2026-10-15)

Source: `docs/tasks/T3.md`, copied from the current user request because no T3.md existed. Each sentence/design condition and required scenario is traced below. Test names refer to `tests/test_task3.py`.

| Requirement text | File:function | Test name / evidence | Status |
| :--- | :--- | :--- | :--- |
| Read RULES.md, docs/tasks/T3.md. Reuse core/*, sentiment from P4, Clock, and session summaries. | `core/tickets.py:TicketService`; `core/conversation.py:ConversationService.turn`; `core/business_time.py:BusinessCalendar`; existing config/security/audit/store/sentiment/sessions | `test_ticket_priority_uses_existing_history_aware_sentiment`, `test_unresolved_chat_collects_separate_drafts_and_reuses_summaries`, `test_background_ticket_sla_runs_without_next_message` | PASS |
| Implement Task 3 exactly as in T3.md. | `core/tickets.py:TicketService`, `app/chatbot.py:collect_ticket`, shared modules | All 12 required named tests below; interpretations in `docs/task3_assumptions.md` | PASS |
| Unresolved conversation -> structured ticket (customer, order, product, issue, evidence, contact). | `core/conversation.py:ConversationService.turn`; `core/tickets.py:TicketService.collect, unresolved, requested_handoff` | `test_unresolved_chat_collects_separate_drafts_and_reuses_summaries`, `test_ticket_api_access_and_draft_completion`, `test_explicit_unresolved_request_creates_draft_despite_factual_answer` | PASS |
| Mandatory fields missing -> ask the customer; do not create a final ticket with invented values. | `core/tickets.py:TicketService.collect`; `app/chatbot.py:handle_query` returns `ticket_questions` | `test_missing_mandatory_requested`, `test_ticket_api_access_and_draft_completion` | PASS |
| Priority = documented, configurable weighted score over severity, sentiment, waiting time, customer impact, SLA state. | `core/priority.py:priority_score`; `core/tickets.py:TicketService._refresh`; `config/default.yaml:tickets.priority` | `test_priority_formula`, `test_ticket_priority_uses_existing_history_aware_sentiment` | PASS |
| Write the formula in docs/priority.md and unit-test it with fixed inputs. | `docs/priority.md`; `core/priority.py:priority_score` | `test_priority_formula`: fixed result 65.25, runtime weights and clamping | PASS |
| Routing by agent skills, availability, workload, and business hours (config). | `core/tickets.py:TicketService._route`; `core/business_time.py:BusinessCalendar` | `test_routing_skills_workload`, `test_after_hours_request`, `test_capacity_released_and_priority_orders_queue` | PASS |
| No eligible agent -> queue with reason, escalate per config. | `core/tickets.py:TicketService._route, _refresh`; configured queue wait/destination | `test_team_unavailable_queued` | PASS |
| SLA arithmetic is business-time only: excludes configured weekends and holidays. | `core/business_time.py:BusinessCalendar.minutes, add_minutes`; `core/tickets.py:TicketService._refresh` | `test_sla_excludes_weekends_and_holidays`, `test_calendar_boundaries_and_clock_rewind` | PASS |
| 75% consumed -> warning event. | `core/tickets.py:TicketService._refresh, _event`; `core/store.py:TicketRepository.transaction` | `test_sla_75_percent_warning` | PASS |
| Breach -> automatic escalation. | `core/tickets.py:TicketService._refresh`; existing Clock worker | `test_breach_auto_escalates`, `test_background_ticket_sla_runs_without_next_message`, `test_durable_sla_events_after_restart` | PASS |
| SLA rules can change at runtime; recompute all open tickets and test it. | `core/tickets.py:TicketService.tick`; shared `get_config`; `app/chatbot.py:maintenance_worker` | `test_runtime_sla_change_recomputes`, `test_invalid_sla_config_rolls_back_all_ticket_changes` | PASS |
| Dedupe: detect duplicate requests (same customer + order + issue similarity), merge. | `core/tickets.py:TicketService.collect, _similar`; `core/store.py:TicketRepository.transaction` | `test_duplicate_ticket_merged`, `test_concurrent_duplicate_creation_is_atomic`, `test_duplicate_merge_preserves_earliest_sla_and_highest_severity` | PASS |
| Group related issues. | `core/tickets.py:TicketService._family, collect` uses group IDs | `test_related_grouped_unrelated_separate` | PASS |
| Keep unrelated issues as separate tickets, even in the same conversation. | `core/tickets.py:TicketService.collect, _similar, unresolved` | `test_related_grouped_unrelated_separate`, `test_similar_wording_with_conflicting_details_is_not_merged`, `test_dedup_does_not_cross_customer_order_product_or_owner` | PASS |
| Handoff summary: masked, no card numbers, phones, or emails. | `core/tickets.py:TicketService.collect`; existing `core/security.py:mask_pii`, `core/escalation.py:EscalationService.masked` | `test_handoff_summary_masked` | PASS |
| test_duplicate_ticket_merged | `core/tickets.py:TicketService.collect` | `test_duplicate_ticket_merged` | PASS |
| test_related_grouped_unrelated_separate | `core/tickets.py:TicketService.collect, _family` | `test_related_grouped_unrelated_separate` | PASS |
| test_missing_mandatory_requested | `core/tickets.py:TicketService.collect` | `test_missing_mandatory_requested` | PASS |
| test_priority_formula | `core/priority.py:priority_score`; `docs/priority.md` | `test_priority_formula` | PASS |
| test_routing_skills_workload | `core/tickets.py:TicketService._route` | `test_routing_skills_workload` | PASS |
| test_team_unavailable_queued | `core/tickets.py:TicketService._route, _refresh` | `test_team_unavailable_queued` | PASS |
| test_after_hours_request | `core/business_time.py:BusinessCalendar`; `core/tickets.py:TicketService._route` | `test_after_hours_request` | PASS |
| test_sla_excludes_weekends_and_holidays | `core/business_time.py:BusinessCalendar.minutes, add_minutes` | `test_sla_excludes_weekends_and_holidays` | PASS |
| test_sla_75_percent_warning | `core/tickets.py:TicketService._refresh` | `test_sla_75_percent_warning` | PASS |
| test_breach_auto_escalates | `core/tickets.py:TicketService._refresh` | `test_breach_auto_escalates` | PASS |
| test_runtime_sla_change_recomputes | `core/tickets.py:TicketService.tick` | `test_runtime_sla_change_recomputes` | PASS |
| test_handoff_summary_masked | `core/tickets.py:TicketService.collect`; shared masker | `test_handoff_summary_masked` | PASS |
| Finish with RTM for T3 and pytest output. | `docs/RTM.md`, `docs/README.md`, `docs/verification/pytest-task3.txt` | Actual captured full command output; Task 3 acceptance output and offline demonstration | PASS |

External helpdesk/paging delivery is not configured. Production agents are supplied by the operator; an empty roster queues with an explicit reason. These boundaries are documented in `docs/task3.md` and do not represent fabricated agent availability.

Actual Task 3 final regression command: `.\.runtime\python311\python.exe -X utf8 -m pytest -q`

```text
274 passed, 1 warning in 62.04s (0:01:02)
```
