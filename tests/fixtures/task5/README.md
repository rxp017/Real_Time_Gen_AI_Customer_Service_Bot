# Authored Task 5 labelled set

`labelled_sentiment.json` contains 60 authored examples: 15 each in English, Hindi (including Hinglish), Telugu (including romanised Telugu), and Spanish. Each language has positive, neutral, negative, frustrated, urgent, and sarcastic labels, including history-dependent pairs, calm risk reports, negation, and implicit-expression challenges. Labels were written before running the evaluator.

The runtime classifier loads only `resources/languages/`; it never reads this dataset. This is an authored regression and diagnostic set, not an independent blinded benchmark or evidence of production accuracy. Rule resources and the dataset have the same author, and no external native-speaker adjudication has been performed. Known misses are retained in the evaluation output; expected labels are not rewritten to match predictions.

Run `scripts/evaluate_t5.py` with the pinned Python 3.11 runtime. It prints the exact correct/total counts, per-language results, confusion matrix, dataset SHA-256, and every misclassified example. Record those measured results with the command in docs/README.md and docs/RTM.md. The set and this provenance file are committed locally as requested; no remote publication is implied.
