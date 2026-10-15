# Task 5 interpretation

- T5.md was absent; its requirements are the current user prompt, preserved in docs/tasks/T5.md. P3 means the existing Task 6 LanguageProcessor and resource files.
- Urgency determines routing of triggered escalations. Urgency alone is not an additional escalation trigger. High-risk issues use urgent routing even with neutral sentiment.
- The unresolved deadline is strictly greater than the configured 15 minutes. The background worker checks it without another message. A policy reply, positive sentiment, session expiration, or LLM failure never proves resolution.
- Only a caller with ticket:manage can explicitly resolve an issue through the escalation API. Resolution closes the episode, preserves records, and resets escalation deduplication for subsequent issues.
- Each trigger emits one durable record per session generation and unresolved episode. Separate high-risk categories retain separate records; a later urgency upgrade reroutes open records immediately without changing their original trigger evidence.
- Business hours are start-inclusive, end-exclusive, same-day intervals in the configured timezone. Workdays and holidays come from config. Invalid calendar settings fail explicitly.
- Sentiment is a resource-driven rule classifier using current text and recent user/assistant history. Its confidence is an evidence score, not a calibrated probability. Ambiguous unmatched text is neutral with low confidence. No LLM calls are necessary for classification or escalation.
- Tone is a separate localized preface. The answer field and cited policy body remain byte-for-byte unchanged; display_answer combines them for presentation.
- Queue routing is persisted locally. No external ticketing, paging, email, or messaging service is configured; creating an on-call record does not claim a human was notified.
- No Git repository exists initially. The requested labelled-set commit will initialize local Git and commit only the authored evaluation dataset and its provenance; no remote publication is requested.
