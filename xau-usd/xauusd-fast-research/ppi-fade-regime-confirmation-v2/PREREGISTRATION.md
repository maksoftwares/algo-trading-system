# XAUUSD PPI Fade Regime Confirmation V2 Preregistration

## Purpose

PPI Event Reaction V1 tested an unchanged impulse policy and an unchanged fade
policy on 2016-07-01 through 2021-12-31. Neither passed every gate. The fade
policy nevertheless produced 39 raw-tick-verified trades, 1.868 stress PF,
+1.031 average stress R, and positive results in both directions. Its losses
were concentrated in the established `TREND_DOWN` state, while the symmetric
non-trending state set had the following historical stress results:

- `CHOP`: 16 trades, +6.835R.
- `COMPRESSION`: 4 trades, +12.034R.
- `TRANSITION`: 6 trades, +21.793R.

These figures are hypothesis-generation evidence, not validation evidence.
V2 makes one post-outcome refinement and tests it only on the still-unopened
2022-01-01 through 2026-06-30 PPI period.

## Fixed Policy

Attempt 11,102 is `EVENT_PPI_NON_TREND_FADE_RR2`.

- The signal, entry, stop, target, holding period, costs, and raw-tick ordering
  are unchanged from `EVENT_PPI_FADE_RR2` in V1.
- Trade only when the causal H4 state at the signal decision is exactly one of
  `CHOP`, `COMPRESSION`, or `TRANSITION`.
- Abstain in both established trend directions, `UNSAFE_SHOCK`, and `WARMUP`.
- This symmetric rule represents one mechanism: fade a scheduled inflation
  shock only when the pre-existing market state is not an established trend.
- There is no parameter grid, threshold search, direction filter, or fallback.

The outcome-free candidate ledger contains 16 signals across 53 official PPI
events. Candidate count is used only to preregister feasible sample gates; no
2022-2026 exit, P&L, stop/target result, or metric was inspected.

## Fixed Confirmation Gates

All gates must pass together after native spread, ticket and holding costs, and
0.05R stress slippage:

- at least 12 executed trades and 20% event participation;
- stress PF at least 1.25 and average stress return at least +0.10R;
- closed-trade drawdown at most 10R;
- positive P&L after removing the three largest winners;
- at least 50% positive active months and 50% positive active years;
- at least 80% feasible at the current account risk budget;
- one-sided trade-mean p-value, equal to Holm q-value for this one-policy
  family, at most 0.10.

## Interpretation

This is related-data confirmation, not a pristine blind exam. A pass creates a
near-survivor that still requires independent-era replication, portfolio
independence testing, and prospective shadow evidence. A failure closes this
specific PPI regime-filter hypothesis; the period will not be reused to tune
another PPI fade rule.

Research only. No model training, Python serving, EA use, demo/live orders,
broker action, paid data, or Databento use is authorized.
