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

## Dev-only selection and follow-up

The first 36 score/weight/margin combinations retained one false answer. A 12-combination component-coverage sweep could remove it but reduced supported coverage to 23/48. Inspection of that dev lookalike showed an unsupported damage/eligibility condition, so the generic requested-condition check was extended rather than treating topic similarity as proof. All sweeps are retained in `verification/revision-t4-dev-*-tuning.json`.

The final six-combination sweep selected hybrid floor 0.50, semantic/lexical weights 0.80/0.20, margin 0.08. A separately measured lexical fallback sweep selected floor 0.40 (37/48 supported and 0/38 false). Query-overlap gating was evaluated but disabled after reducing dev recall. Rank acceptance remains enforced; a runner-up cannot replace a rejected highest-scoring match. Close competing scopes still require clarification. Top-k generation and each claim's own source citation remain subject to complete-sentence verification.

The final replay used all 197 actual dev embedding vectors, now published with their model/hash in the compressed verification artifact. With deterministic source quotation it produced 48/48 correct cited answers (Wilson 95%: 92.59–100%) and 0/38 false answers (0–9.18%). This is a tuned dev regression, not live generation accuracy or independent generalization evidence.

The separate post-fix live dev run had 48 provider failures, 16 rank-margin refusals, nine score refusals and 13 unsupported-attribute refusals. Embedding coverage was complete, but generation quota prevented every supported answer. The descriptive live rate is 0/48; it is infrastructure-confounded. No held-out data was used to choose any of these changes.
