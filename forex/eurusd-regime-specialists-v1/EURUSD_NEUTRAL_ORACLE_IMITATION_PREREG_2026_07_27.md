# EURUSD Regime 1 Neutral oracle-imitation preregistration

Frozen: 2026-07-27 17:30 UTC

Campaign: `eurusd-neutral-oracle-imitation-v1`

## Hypothesis

A shallow regularized classifier may learn a stable subset of the Neutral
hindsight oracle's entry timing and direction from information already known
when each M5 bar completes. Historical oracle membership is used only as a
supervised label. It is forbidden at inference.

This is adaptive historical research. The oracle distribution and earlier
campaign results were already inspected, so 2023-2026 H1 are chronological
pseudo-OOS falsification windows, not pristine market evidence.

## Frozen design

- Candidates: both directions at every completed EURUSD M5 timestamp whose
  latest completed cross-asset state is non-shock, non-compressed Neutral.
- Features: the already frozen causal bar, DXY, Treasury, time-cycle, and raw
  EURUSD tick-microstructure feature set.
- Positive label: exact timestamp and side equality with a
  `FULL_CALENDAR_PERFECT_FORESIGHT_TRADES.csv` row attributed to `NEUTRAL`.
- Label availability: every positive or negative label is treated as unknown
  until 12 hours after entry; training rows must clear that purge boundary.
- Model: one L2 logistic regression with fixed regularization and balanced
  class weights.
- Development fit: 2019-2020.
- Threshold selection: the frozen grid on 2021-2022 only, maximizing exact
  one-to-one match F1, then 15-minute match F1, then net R. A threshold must
  produce at least 50 trades in each development-selection year.
- Forward tests: annual refits for 2023, 2024, 2025, and 2026 H1, always using
  only earlier label-complete rows and the single development-selected
  threshold.
- Online routing: choose the higher-scored side at a timestamp, then accept
  causally if the threshold, four-position concurrency limit, and four-trade
  UTC-day limit permit it. Future scores are never used to rank current
  entries.
- Risk: fixed 4 pips, 1.50R target, 12-hour maximum hold, exact bid/ask,
  0.70-pip minimum spread, 0.10-pip adverse slippage per side, and stop-first
  ambiguous bars.
- Portfolio exposure: 0.25 portfolio-R per position and at most 1.0 open
  portfolio-R.

## Admission

Every chronological window must contain at least 50 trades, win 45%-55%,
realize 1.35-1.75 payoff, PF at least 1.10, and positive expectancy.
Overall exact-match precision must reach 10%, exact recall 5%, and
same-side 15-minute precision 15%. The campaign must also remain profitable
after an extra half-pip round-trip stress.

Failure of any required gate rejects the campaign. No failed threshold,
feature, direction, hour, concurrency rule, or lifecycle may be repaired
after the outcome pass. The perfect oracle remains contaminated and is never
promotion evidence.
