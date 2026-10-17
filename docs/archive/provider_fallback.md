# AI Studio model fallback - verified 2026-10-14

`.env` retains the original Google key. Six blank role keys were generated locally. No secret was printed, no key was rotated, and no billing setting was changed.

Current model chain:

1. gemini-2.5-flash (primary; successful live generation)
2. gemini-3.5-flash-lite
3. gemini-3.1-flash-lite
4. gemini-3.8-flash
5. gemini-3.6-flash

All appear in this key's model inventory and in the [official pricing catalog](https://ai.google.dev/gemini-api/docs/pricing) as free-tier-eligible text models. The [billing documentation](https://ai.google.dev/gemini-api/docs/billing) explains that an AI Studio key does not by itself establish Free-tier billing. Confirm the project's tier in AI Studio; this implementation cannot force Free-tier billing from the key.

Fallback handles recoverable HTTP availability/quota failures and transport failures, with one attempt per eligible model. It deduplicates the list, respects model cooldowns/Retry-After via Clock, and stops at the configured dispatch/attempt limits. Authentication errors, other client errors and safety blocks are never bypassed by switching models. Empty/malformed responses can fall back; internal thought parts are not returned as answer text. Exhaustion raises a real error and the API returns 503.

The token cap, cooldown, timeout, attempt cap, eligible catalog and dispatch budget live in config/default.yaml. Model order lives in GOOGLE_MODEL and GOOGLE_FALLBACK_MODELS. An explicit empty GOOGLE_FALLBACK_MODELS disables fallback. Restart the app after changing .env; YAML provider-policy changes are hot-reloaded.

Observed live evidence:

- `scripts/check_provider_models.py`: models.list authenticated successfully. [Sanitized inventory](verification/provider-models.json).
- Initial `scripts/check_provider_generation.py`: newer candidates timed out/returned 503; 2.5 Flash-Lite returned 404. That model was removed from the active chain. [Original failure report](verification/provider-generation.json).
- Isolated 2.5 Flash probe returned HTTP 200 with READY. [Actual result](../verification/provider-flash-probe.json).
- `scripts/check_live_task6.py`: four explicit synthetic refund-policy questions passed through the real provider, with en/hi/te/es recognition, localized answers and verified citations. [Actual result](verification/task6-live-provider.json). [Earlier smoke results](verification/task6-live-provider-runs.jsonl) remain available, including safe refusals to unsupported action instructions.

These checks establish connectivity and four supported fixture answers. Backup generation success, project billing tier, real customer-policy quality and general language accuracy remain unverified. Project-wide quota cannot be bypassed by changing models; see [Google's rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits).

Offline tests mock only HTTP transport and use FakeClock. They cover recoverable statuses, timeouts, Retry-After, cooldown expiry, authentication/client/safety termination, budget/attempt caps, catalog restrictions, deduplication, malformed output and actual-model reporting. Task 6's 14 required names and 35 three-turn conversations per language remain present.
