# Project Instructions

## General Instructions
1. Requirements come only from docs/tasks/Tn.md and docs/instructions.md. Never paraphrase from memory. Ambiguity -> write it in docs/assumptions.md, pick the safest reading, continue.
2. Before using any library, verify it exists and the API you call exists (pip show / import / run a 3-line check). Pin versions in requirements.txt.
3. No placeholders: no TODO, FIXME, pass-only bodies, NotImplementedError, hardcoded return values faking logic, or mocked "success" in non-test code. A stub must raise a clear error and be listed in docs/known_gaps.md.
4. Never invent results. Metrics, accuracy numbers, and demo outputs in docs/README must be copied from a command you actually ran. Show the command and real output.
5. No claim of "done" without: pytest -q output pasted, and a Requirements Trace Matrix (docs/RTM.md) row per sentence of the task: requirement text | file:function | test name | PASS.
6. Every requirement that names an evaluation scenario needs its own named test (test_<scenario>).
7. No dead code, no unused abstractions, no over-engineering. Smallest design that meets each requirement fully. No emoji in code/logs/README. Comments only where logic is non-obvious.
8. Never commit secrets. Keys via .env; ship .env.example.
9. Python 3.11, type hints, ruff-clean, one responsibility per module.

## Workflow Order
- Step 0 (before any code): inspect the cloned training repo. Write docs/baseline.md: what the existing chatbot does, entry points, deps, how to run it. Our work extends THIS project in place. Show me the plan and wait for approval.
- Step 1: build the shared foundation from RULES.md (clock, config, llm, security, store, audit, metrics) with unit tests.
- Step 2: implement Task 4 exactly as in T4.md.
