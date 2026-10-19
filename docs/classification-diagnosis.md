# Classification development diagnosis

The previous frozen evaluation accepted 6/48 provider classifications and reported 22/48 combined accuracy. Its remaining outcomes did not record rejection causes, so their exact division into confidence, schema, injection bypass and provider failure is unknown. Do not retrospectively assign those 42 cases to a cause.

The separately committed workshop-service dev set has 60 examples across en/hi/te/es, including sarcasm history and calm high-risk reports. Pattern-only baseline: 40/60. Resource changes and clearer label definitions use only this dev set. Pattern-only after changes: 59/60. These are tuned development results, not generalization claims.

The instrumented live dev run accepted 6/60, all correct. Its other 54 decisions were explicitly quota fallbacks, also correct on this tuned set. Combined 60/60 is therefore not pure-provider or multilingual-provider accuracy. Wilson 95%: assisted 6/6, 60.97–100%; fallback 54/54, 93.36–100%; combined 60/60, 93.98–100%. No confidence/schema/injection rejection occurred in that run. Unit tests separately exercise each rejection path.

The initial six-second evaluator spacing exhausted a live rate window; later synthetic generation succeeded with the same key. This supports transient throttling but does not identify the account's entire quota policy. Evaluation spacing is now 15 seconds and waits out provider cooldown before starting the next request's deadline. Production requests retain bounded retries inside their own deadline; evaluation pacing is outside it. Historical failed dev runs are retained.

The cache contains only digests of masked text, masked history, session identity, model/config/resources, and validated sentiment results. It is bounded, has a 120-second TTL, and is isolated per session. Provider failure results are not cached. High-risk detection remains independent rule logic; sentiment and provider output cannot suppress it.

Post-fix frozen evaluation rules and the implementation/config identity are registered in `evaluation-preregistration.json` before execution. Those sets were already exposed pre-fix; the post-fix result is a re-evaluation. More than 10% infrastructure failures invalidates a run; only one identical-config rerun is permitted and every run is retained. The final report must distinguish assisted coverage and conditional accuracy from fallback accuracy.
