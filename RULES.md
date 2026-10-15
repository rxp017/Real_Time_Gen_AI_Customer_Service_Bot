# RULES (apply to every task)

## Anti-hallucination / anti-slop
1. Requirements come only from docs/tasks/Tn.md and docs/instructions.md. Never paraphrase from memory. Ambiguity -> write it in docs/assumptions.md, pick the safest reading, continue.
2. Before using any library, verify it exists and the API you call exists (pip show / import / run a 3-line check). Pin versions in requirements.txt.
3. No placeholders: no TODO, FIXME, pass-only bodies, NotImplementedError, hardcoded return values faking logic, or mocked "success" in non-test code. A stub must raise a clear error and be listed in docs/known_gaps.md.
4. Never invent results. Metrics, accuracy numbers, and demo outputs in docs/README must be copied from a command you actually ran. Show the command and real output.
5. No claim of "done" without: pytest -q output pasted, and a Requirements Trace Matrix (docs/RTM.md) row per sentence of the task: requirement text | file:function | test name | PASS.
6. Every requirement that names an evaluation scenario needs its own named test (test_<scenario>).
7. No dead code, no unused abstractions, no over-engineering. Smallest design that meets each requirement fully. No emoji in code/logs/README. Comments only where logic is non-obvious.
8. Never commit secrets. Keys via .env; ship .env.example.
9. Python 3.11, type hints, ruff-clean, one responsibility per module.

## Shared architecture (build in P1, reuse after; never duplicate)
- core/clock.py: Clock interface. SystemClock, FakeClock(advance, set). ALL time logic (maintenance windows, SLA, sessions, retention, retries, business hours, 15-min escalation) uses Clock. Never call datetime.now()/time.sleep elsewhere.
- core/config.py + config/default.yaml: every threshold, language, timing, SLA rule, role, holiday list, weight. Hot-reloadable at runtime. Timezone Asia/Kolkata.
- core/llm.py: LLMClient interface, one real provider adapter, FakeLLM (deterministic, scripted) for tests.
- core/security.py: RBAC (API key -> role -> permissions), PII/payment masker (cards via Luhn, phones, emails, addresses; order IDs/product codes preserved), prompt-injection detector (pattern rules + structural isolation: retrieved/OCR/uploaded text is DATA, never instructions).
- core/store.py: SQLite repositories. core/audit.py: structured logs, masked by default. core/metrics.py: counters + latency histograms.
- app/chatbot.py: orchestrator wrapping the EXISTING training-project bot. Extend in place; do not replace it. API: FastAPI.
- tests/: pytest, FakeClock + FakeLLM, no network.
