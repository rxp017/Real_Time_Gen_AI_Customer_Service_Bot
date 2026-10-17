# Task 3 tickets

Unresolved RAG requests, support escalations, configured explicit handoff phrases and a customer's `unresolved: true` query flag create owner-bound structured drafts through `ConversationService`. A factual RAG answer never overrides an explicit unresolved/human-handoff request. Each detected request retains its own order/product context. Current session summaries (including restored summaries) supply factual context; customer identity/contact are never inferred. Low language confidence alone creates no final ticket.

`POST /query` returns `tickets` and `ticket_questions`. Present these questions to the customer separately from the policy answer, which retains its citations and tone invariants. Each draft returns its `id`, `fields`, `missing_fields` and `question`. Missing customer/order/product/issue/evidence/contact prevents finalization. Repeated identical unresolved requests reuse the pending draft.

Complete a draft using `POST /tickets` with the same authenticated customer key:

```json
{
  "session_id": "the-session-from-query",
  "draft_id": "the-draft-id-from-query",
  "fields": {
    "customer": "customer-supplied identifier",
    "order": "customer-supplied order",
    "product": "customer-supplied product",
    "issue": "customer's actual unresolved issue",
    "evidence": "customer's statement or evidence reference",
    "contact": "customer-supplied contact"
  },
  "severity": "normal",
  "impact": "individual"
}
```

The example describes API fields; it is not real customer data. `draft_id` may be omitted for an explicit new request in an existing owned session. Structured fields are bounded strings, never model-generated fills. Evidence strings are customer-supplied statements/references, not a claim of upload authentication or extracted document validity. Optional severity/impact use configurable operational defaults when absent.

Customer roles need `ticket:create` and `ticket:view_own`. `GET /tickets` returns only their owned records; support managers/admins can inspect all records. Unknown keys, foreign sessions/drafts and unauthorized management calls reject and audit. `POST /tickets/{id}/close` takes `{"reason":"actual resolution"}` and requires `ticket:manage`. Closure frees assigned workload; resolved tickets stop SLA processing. MERGED records are collection tombstones linking to the surviving ticket.

SQLite transactions atomically persist collections, deduplication, group IDs, agent workload decisions and events. Similarity uses token Jaccard with configured stopwords; numeric distinctions and configured negation words must match. Related groups use configured issue families in addition to customer/order/product. Unknown issue types do not get guessed into a team. Handoff summaries and resolution reasons pass through the shared masker; raw structured contact is retained only in authorized ticket data, never audit logs or masked summaries.

Business hours, workdays and holidays come from the shared calendar. `tickets.sla_minutes` maps severity to business-minute targets. At 75% a durable warning is recorded; at 100% a durable breach escalation is recorded. The existing Clock worker recomputes every open ticket, including idle conversations, and retries queued assignment. A sentiment worker or maintenance outage does not block ticket processing. Rule/hour/holiday changes take effect on the next tick (default 10 seconds); restart is not required. Historical SLA events remain after a rule relaxation.

Routing requires configured issue/product skills, agent availability and remaining capacity, and only assigns inside business hours. Queues store explicit reasons and next opening. Queue wait escalation uses configured business minutes and a configured destination. Events/queues are local durable records; external paging/helpdesk delivery is not configured.

`tickets.agents` intentionally defaults to an empty list. Supply real agent IDs, skills, availability and capacity there. Each agent entry uses `id`, `skills` (list), `available` (boolean), `capacity` (integer). `tickets.product_skills` can add product-specific requirements. The authored test/demo agents exist only in their temporary configurations.

[Priority formula](../priority.md), [assumptions](../task3_assumptions.md), [RTM](../RTM.md), [actual pytest output](verification/pytest-task3.txt).

Offline demonstration:

```powershell
.\.runtime\python311\python.exe -X utf8 scripts/demo_t3.py
```

Actual output is saved in `docs/verification/demo-task3.txt`. It exercises collection, merge, a weekend and holiday, warning, agent availability and breach; it does not claim external helpdesk delivery.
