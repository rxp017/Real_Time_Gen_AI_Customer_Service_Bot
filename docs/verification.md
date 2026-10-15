# Antigravity audit and current verification

The original 21 fixture tests were rerun and passed after moving pytest's temp directory away from an inaccessible inherited folder. Passing those tests did not substantiate all completion claims.

Confirmed original defects:

1. `/query` returned `Echo response for: ...` with `verified=True`, without invoking the training bot or Task 4.
2. `verify_claim` returned True for `Learners are not eligible for a refund within 14 days.` against `Learners are eligible for a refund within 14 days.`
3. Injection neutralization retained both the matched instruction and its remaining payload.
4. Retrieval never rescanned an unflagged stored chunk, ignored product/region arguments, and discarded zero-score new versions before conflict resolution, allowing old policies to resurface.
5. Unknown access labels defaulted to public rank. API keys were hardcoded in the YAML, while .env key names were unused.
6. The claimed Python 3.11 environment was actually Python 3.14.7.
7. T1.md did not exist; the upstream dependency manifest was not a valid supported runtime install.

Repairs are covered by `tests/test_verification.py`, along with API ingestion, evaluation, approval, activation, querying ACTIVE, lifecycle initialization, and secret masking. Task 1 uses the existing SQLite Document model, retrieval engine, Clock, config, LLM interface, RBAC, audit, and metrics.

The supported runtime now has Python 3.11 evidence. `docs/verification/pytest.txt`, `ruff.txt`, `pip-check.txt`, `demo-t1.txt`, and `demo-t4.txt` are captured command output, not manually authored result claims. The complete maintenance-day demo uses real SQLite and explicitly scripted FakeClock/FakeLLM.

Remaining limits are listed in `docs/known_gaps.md`; the Task 4 semantic-search RTM row remains PARTIAL. Provider REST fields follow [Google's generateContent reference](https://ai.google.dev/api/generate-content); no live-provider success is claimed.
