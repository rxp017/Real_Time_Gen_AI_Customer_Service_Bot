# Design assumptions

- Latest applicable family/product/region resolution occurs before lexical or embedding scoring. Historical/future policy vectors may exist for authorized as-of queries but cannot bypass current-date filters.
- T4 and T5 development sets were committed separately before implementation changes. Only these development sets drove thresholds, prompts and resources. Existing exposed frozen sets are re-evaluated after source/config registration; no outcome drove further tuning. CI checks immutable hashes and complete normalized text contamination.
- T4 retains the flagged parent for audit. Independent safe sentences are projected into an unflagged retrieval/embedding view; neutralized instructions never become evidence. Pure injected content remains excluded, and T1 still quarantines injection-flagged source files. Sentence adjacency can conservatively lose safe text.
- Hybrid rank/margin and requested-attribute gates supplement thresholds; top-k claims still require support by each cited source. Development replay uses measured cached vectors and deterministic FakeLLM quotation, so its metrics are not live generation quality.
- Provider retries are bounded by the original request deadline. Evaluation pacing and cooldown waits happen before the next deadline. No key rotation or billing change is performed. The classifier cache keys masked text and history hash, session identity and configuration; short TTL/bounds prevent indefinite cross-session reuse.
- Registration `980e44338656f551dbfe44b6babfe55972e109539920890619c8b6a8a15ae0c4` preceded post-fix evaluation. More than 10% infrastructure failures invalidates a run; only one identical-config rerun is permitted. All runs and prior pre-fix exposure are disclosed. After the daily cap was observed, the user selected quota-limited completion: retain complete invalid T4 run 1, skip optional rerun and live T5, and measure fallback separately. No valid post-fix model accuracy or live translation success is inferred.
- Original FAQ bytes and mentor attribution remain. The normal API imports FAQs to shared metadata-bearing RAG for a new configured empty store; preserved legacy entry points remain unverified. Existing ACTIVE snapshots are not overwritten by bootstrap.
- Names/order IDs/dates/products are protected before normalization; unknown names remain a bounded-recognition limit. Translation retains canonical source_answer and actual answer_language. Provider failure or token validation failure uses curated/source fallback, never an invented success.
- OCR uses runtime override before environment and then configured/PATH discovery, with standard Windows fallback. One worker/instance, no browser-persisted keys, bounded uploads and restricted origins remain supported deployment assumptions. Render Free sleeps and ephemeral disk are explicit demonstration limits.


## Uploads and ticket inputs

- Upload validation reads bounded format headers before content decoding. The allowlist is PNG, JPEG and a conservative PDF subset. Unsupported PDF features are rejected; this is not universal malware containment.
- Field extraction uses explicitly labelled document values. Missing values remain null. Message values are used for comparison and never fill document gaps. OCR confidence does not prove authenticity.
- Upload completion is delivered through owner-bound job polling. Retention removes stored bytes and result content; minimal expiry tombstones remain.
- Ticket severity and impact are explicit inputs. Omitted values use recorded configuration defaults. Mandatory customer/contact fields must be supplied before final creation. Alerts and queue destinations are local records.
