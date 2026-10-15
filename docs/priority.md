# Ticket priority

`core/priority.py:priority_score` reads `tickets.priority` from the shared hot-reload configuration on every call. No model decides the score.

For severity `s`, sentiment label `l`, elapsed business minutes `t`, customer impact `i`, and consumed SLA fraction `r`:

```
S = severity[s]
M = sentiment[l]
W = clamp(t / waiting_cap_minutes, 0, 1)
I = impact[i]
L = clamp(r, 0, 1)
priority = round(100 * (wS*S + wM*M + wW*W + wI*I + wL*L)
                      / (wS + wM + wW + wI + wL), 6)
```

Default weights: severity 0.30, sentiment 0.20, waiting 0.15, impact 0.20, SLA 0.15. The waiting cap is 480 business minutes. All maps and weights are in `config/default.yaml`; weights must be finite, nonnegative and sum to more than zero. Components must be in [0,1]. The result is in [0,100].

Default severity values: low 0.10, normal 0.40, high 0.75, critical 1.00. Default impact values: individual 0.25, team 0.60, widespread 1.00. Default sentiment values: positive 0, neutral 0.20, negative 0.60, frustrated 0.80, urgent 1.00, sarcastic 0.80.

Severity/impact are explicit structured operational inputs. If omitted, normal/individual are recorded as configured defaults. Sentiment comes from the existing history-aware multilingual `SentimentClassifier`, using the issue and actual recent session history. No classifier accuracy is claimed for this task.

Waiting and SLA consumption both use `BusinessCalendar.minutes(created_at, Clock.now())`. Creation time starts when required customer data is complete. The SLA target is selected by severity from `tickets.sla_minutes`; it does not depend on priority, preventing a circular formula. Default targets: critical 30, high 60, normal 240, low 480 business minutes.

Fixed example tested by `test_priority_formula`: high severity, negative sentiment, 240 waiting minutes, team impact and 75% SLA consumed -> **65.25**. The test also changes weights at runtime and checks clamping.

Every tick recomputes all open tickets against current targets, weights, hours and holidays. Queued tickets are then considered by descending score, oldest creation time, and ticket ID. Eligible agents must be available, cover all configured issue/product skills, and be below their capacity. Lowest current assigned workload wins; agent ID breaks ties. Existing assignments are not preempted. Closed tickets release workload.

At 75% SLA consumption a durable warning event is stored; at 100% a durable breach/escalation event is stored. Each condition fires once per ticket. Relaxing a target clears current breach state when applicable but preserves escalation history. Queue escalation defaults to 60 business minutes and the supervisor queue. These are local events and queue destinations, without an external notification transport.
