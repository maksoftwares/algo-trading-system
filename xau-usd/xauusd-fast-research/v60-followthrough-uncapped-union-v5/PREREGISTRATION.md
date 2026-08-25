# V60 Follow-Through Uncapped Union V5 Preregistration

## Status

Retrospective, post-hoc research only. Deployment and broker action are prohibited.

## Frozen policy

V5 is the direct union of:

- every frozen V2 source-health veto proposal; and
- every frozen V57 anti-chase proposal for which `ret_24h > 0` and
  `ret_4h / ret_24h < 0.70`.

Duplicate proposals for the same trade count once. There is no daily veto budget.
Missing or nonfinite follow-through features retain V60 behavior.

V4 demonstrated that a daily budget was unnecessary after follow-through filtering
and caused the locked cost-stress closed-drawdown gate to fail. Removing that budget
is the only V5 change.

## Selection disclosure

All historical and August outcomes were exposed. The 0.70 threshold and removal of
the daily budget were selected after inspecting prior experiment results. Therefore,
the replay can reject V5 or nominate it for forward observation, but cannot authorize
deployment.

## Acceptance gates

- Exact V60 benchmark identity.
- Net P/L and PF no worse than V60.
- Closed and exact sampled equity drawdown no worse than V60.
- At least 99% trade and frequency retention.
- No harmed calendar year or final 3/6/12-month window.
- At least 10 executed vetoes with veto-cohort PF below 1.
- Every comparative gate passes at +$0.10 and +$0.20 per trade.
- Exposed August net/PF improve and closed drawdown does not worsen.
- Dukascopy same-timing delta is positive with no harmed year.
- Clean causal forward evidence remains mandatory before deployment.
