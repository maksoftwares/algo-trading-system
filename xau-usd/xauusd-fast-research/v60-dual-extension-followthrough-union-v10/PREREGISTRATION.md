# V60 Dual-Extension Follow-Through Union V10 Preregistration

## Question

Can V6's August protection obtain adequate historical support when two causal
signs of late-stage extension are treated as alternatives, while preserving the
deployed V60 edge and meeting or exceeding frozen V6?

## Outcome-blind nomination

The frozen causal feature ledger contains 261 mature V57 long candidates with
finite required features. Without reading P/L, the V6 funnel contained:

- 32 bottom-decile rank candidates;
- 76 ATR-ratio-at-least-1.20 candidates;
- 72 candidates within 1.00 ATR of the prior 24-hour high;
- 129 weak-follow-through candidates; and
- 1 candidate satisfying every V6 anti-chase condition.

One-condition ablations produced 6 candidates without ATR, 5 without distance,
17 without rank, 1 without positive 24-hour return, and 2 without weak
follow-through. V9 tested the highest-density rank ablation and failed because
rank was carrying useful selectivity.

ATR expansion and proximity to the prior high are alternative observations of
the same extension mechanism. The outcome-blind union
`ATR >= 1.20 OR distance_to_24h_high < 1.00 ATR`, while retaining every other
condition, nominates exactly 10 historical candidates. This density calculation
did not use trade outcomes.

## Single structural change

Keep V2 unchanged. Keep V6 maturity, source, direction, bottom-decile causal
rank, positive 24-hour return, and weak-follow-through requirements unchanged.
Replace only:

`ATR >= 1.20 AND distance_to_24h_high < 1.00 ATR`

with:

`ATR >= 1.20 OR distance_to_24h_high < 1.00 ATR`.

Missing or nonfinite features retain V60 behavior. V2 state is recomputed from
each scenario's own prior retained outcomes. No daily veto budget is used.

## Evidence boundary

- V60, V6, V7-V9, historical outcomes, and August 2026 outcomes were exposed
  before this contract.
- This is one retrospective falsification test, not independent validation.
- No threshold, scope, metric, or gate may change after the first replay.
- A pass can only nominate a separate clean prospective observer.
- Demo, live, runtime, ML, and broker changes are prohibited.

## Hard acceptance gates

- Exact V60 identity and every nominal comparative gate pass.
- Full-history and 3/6/12-month net and PF are not below frozen V6; full closed
  and equity drawdown are not above frozen V6.
- At least 98% of V60 trades and frequency are retained.
- At least 10 historical anti-chase vetoes have positive avoided P/L and PF below
  0.80; at least 20 union vetoes exist.
- August remains positive and better than V60, with net/PF no lower and closed
  drawdown no higher than frozen V6.
- Dukascopy same-timing delta is no lower than frozen V6 and every covered year
  is nonnegative.
- Every comparative gate passes at +$0.10 and +$0.20 per trade.
- Clean causal forward evidence remains mandatory before deployment.

Failure rejects V10 without tuning. V60 and frozen V6 remain unchanged.
