# Provider configuration and fallback - 2026-10-14

Source: user's request to inspect .env, configure AI Studio free-tier models and add a fallback layer. Task 6 requirements remain in T6.md.

- Preserve the supplied Google key and never print it.
- Configure only text models that official Google documentation lists as free-tier eligible and the key's models.list inventory exposes.
- Keep one key; try configured models in order on recoverable availability/quota/network errors.
- Bound attempts, HTTP timeouts and dispatch budget; cool down failed models through Clock and honor Retry-After.
- Fail visibly when no model can serve the request. Do not use mocked success or downgrade to FakeLLM.
- Do not switch models to bypass authentication errors, invalid requests or safety refusals.
- Reverify Task 6's existing required scenarios and preserve its fixture corpus, RTM and actual pytest output.

Model eligibility does not force the API project's billing tier. Ask the user to confirm that the project remains on the Free tier; never enable billing or change quotas.
