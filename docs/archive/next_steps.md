# Steps requiring your input

No user action is required to run the completed offline tests.

For a live bot:

1. Your Google key was preserved and authenticated on 2026-10-14. `.env` now uses live-verified `gemini-2.5-flash` with four model backups. Six formerly blank role keys were generated locally. Keep `.env` private and use its role keys in the API's x-api-key header. Check your AI Studio project's billing tier is Free: an AI Studio key and free-tier-eligible model do not themselves force free billing. No billing setting was changed.
2. Supply your actual support-policy JSON files in `data/inbox/` and expected answers for your policies in `data/golden/`. The shipped bootcamp/sample documents and golden answers are fixtures.
3. Run the server with the Python 3.11 command in the root README, then ingest, measure, approve and activate an update through the documented API workflow. Activation is restricted by the configured maintenance window.
4. For vocabulary outside the supplied support domain, add markers, entity patterns, phrase normalizations, and translations in `resources/languages/<code>.json`, and enable the code in `config/default.yaml`. Have fluent speakers review production language resources and add real unseen customer conversations to evaluation before making broad accuracy claims.
5. Configure real agents in `tickets.agents` in `config/default.yaml`: ID, skills, availability and capacity. The default roster is empty, so final tickets queue honestly. Review issue/product skill mappings, business hours, holidays and SLA targets there. Ticket questions are returned by `/query`; complete drafts through `/tickets` using actual customer data. See `docs/task3.md` and `docs/priority.md`. Escalation queues/events are local; external helpdesk delivery is not configured.

Remaining Task 4 semantic-search and legacy-bot limitations are documented in `docs/known_gaps.md`. Four synthetic policy questions passed through the real Gemini provider and the Task 6 wrapper; real customer-policy quality remains unverified. See `docs/provider_fallback.md` for models, fallback behavior and evidence.
