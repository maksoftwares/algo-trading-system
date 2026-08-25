# V60 Persistent Source-Health Union V11 Preregistration

## Question

Can a causal persistence requirement remove V6's marginal cost-induced V2 state
changes while preserving the exact August anti-chase protection and all nominal
edge?

## Failure being addressed

Frozen V6 passes every nominal gate and every `+$0.10` comparative gate. At
`+$0.20`, one 2021 winner is additionally vetoed after the rolling source PF
crosses just below 1.00, making 2021 `$3.57` worse than V60. V7 and V8 changed
the PF threshold to 0.90 and 0.95; both were rejected. This lane will not screen
another PF threshold.

## Single structural change

Keep the PF threshold at 1.00, rank below 0.10, 20-trade window, 50-trade
maturity, dynamic retained-path state, and the complete V6 anti-chase rule.

For V2 only, require rolling PF below 1.00 in both:

1. the latest 20 retained closed outcomes; and
2. the immediately preceding 20-outcome window, shifted back by one close.

The current candidate must still have causal rank below 0.10. This one-close
hysteresis rejects only persistent source degradation; a state that crossed the
threshold on the latest close cannot veto yet. All state is recomputed causally
inside each nominal and cost-stressed scenario.

No threshold, feature, anti-chase condition, daily budget, or account rule is
changed.

## Evidence boundary

- V60, V6-V10, historical outcomes, August 2026 outcomes, and V6 cost-stress
  outcomes were exposed before this contract.
- Persistence was nominated specifically after the V6 `+$0.20` failure was
  known. This is post-hoc retrospective falsification, not independent evidence.
- No policy, gate, or threshold may change after the first replay.
- Demo, live, runtime, ML, and broker changes are prohibited.

## Hard acceptance gates

- Exact V60 identity and every nominal comparative gate pass.
- Full-history and 3/6/12-month net/PF are not below frozen V6; full closed and
  equity drawdown are not above frozen V6.
- At least 99% of V60 trades and frequency are retained.
- At least 10 executed V2 vetoes and one executed anti-chase veto remain; each
  component has positive avoided P/L and PF below 0.80.
- August net/PF/drawdown are no worse than frozen V6 and better than V60.
- Dukascopy same-timing delta is no lower than frozen V6 and every year is
  nonnegative.
- Every comparative gate passes at both `+$0.10` and `+$0.20` per trade.
- Clean causal forward evidence remains mandatory before deployment.

Failure rejects V11 without tuning. V60 and frozen V6 remain unchanged.
