# V60 Rank-Independent Follow-Through Union V9 Preregistration

## Question

Can the V6 August anti-chase mechanism produce enough historical support when
its bottom-decile rank dependency is removed, while preserving the deployed V60
edge and meeting or exceeding V6's already-observed August and historical risk
metrics?

## Evidence boundary

- V60, V6, all historical outcomes, and August 2026 outcomes were exposed before
  this contract.
- This is a one-candidate retrospective falsification test, not independent
  validation.
- No parameter, threshold, family scope, metric, or gate may be changed after
  the first outcome run.
- A retrospective pass can only nominate a separate clean prospective observer.
  It cannot authorize demo, live, runtime, or broker changes.

## Single structural change

Keep V2 source-health logic and every V6 anti-chase condition unchanged except
for removing `causal_rank < 0.10` from the V57 anti-chase rule. The anti-chase
rule therefore requires:

1. V57 long candidate;
2. at least 50 prior closed V57 trades;
3. ATR ratio at least 1.20;
4. distance below 1.00 ATR from the prior 24-hour high;
5. positive 24-hour return; and
6. `ret_4h / ret_24h < 0.70`.

Missing or nonfinite features retain V60 behavior. V2 remains dynamically
recomputed from each scenario's own prior closed path. No daily veto budget is
used.

## Hard acceptance gates

- Exact V60 baseline identity and every nominal comparative gate pass.
- Full-history net and profit factor are not below frozen V6; closed and equity
  drawdown are not above frozen V6.
- 3-, 6-, and 12-month net and profit factor are not below frozen V6.
- At least 98% of V60 trades and frequency are retained.
- At least 10 executed historical vetoes are attributable to the anti-chase
  component, their avoided P/L is positive, and their baseline profit factor is
  below 0.80.
- At least 20 union vetoes exist.
- August 2026 net and profit factor are not below frozen V6, and closed drawdown
  is not above frozen V6. The result must remain positive and better than V60.
- Dukascopy same-timing delta is not below frozen V6 and every covered year is
  nonnegative.
- Every comparative gate passes under both +$0.10 and +$0.20 per executed trade.
- Clean causal forward evidence remains mandatory before deployment.

Failure rejects V9 without tuning. V60 and frozen V6 remain unchanged.
