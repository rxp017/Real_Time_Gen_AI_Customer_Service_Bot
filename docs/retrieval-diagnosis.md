# Development diagnosis before retrieval changes

Only `tests/fixtures/task4/dev/` was used. No frozen held-out questions or outcomes were used to select changes.

Commands:

```sh
python scripts/evaluate_development.py --output docs/verification/revision-t4-dev-baseline-offline.json
python scripts/evaluate_development.py --live --output docs/verification/revision-t4-dev-baseline-live.json
```

The corpus has 86 cases (48 answerable, 38 requiring refusal) and 111 documents, including 100 unrelated distractors. Independent safe sentences beside a malicious instruction are answerable dev cases; the pre-fix whole-chunk exclusion prevents those answers. Explicit product/region scope is passed through the normal query path.

The deterministic lexical baseline answered 6/48 supported questions and falsely answered 1/38 refusal cases. Its decisions were 79 threshold refusals and seven answers. The false answer used cell-collection opening information for a question about payment: source grounding alone does not establish that a sentence answers the requested attribute. These are lexical/extractive diagnostic results, not live model accuracy.

The actual provider baseline produced 59 threshold refusals, three ambiguity clarifications and 24 provider failures. Every case had incomplete embedding coverage; four embedding batches failed with HTTP 429. Returned retry delays of 25–43 seconds exceeded the 20-second request deadline and were correctly not waited out. Generation was quota-blocked or in cooldown. Its 0/48 answer rate cannot establish retrieval quality because infrastructure failed. The full trace records component scores, rank, margin, threshold and filter reasons; filtered text is never scored.

Changes justified by this dev evidence: evaluate lower dev-calibrated score floors with a rank margin; avoid treating weak competing top-k hits as scope ambiguity; refuse missing requested attributes; retain only independent safe sentences after instruction-span removal; preserve exact source-sentence verification. Actual cached embeddings can be replayed for dev score selection without inventing missing vectors. Report hybrid replay separately from live generation, and retain every failed live run.
