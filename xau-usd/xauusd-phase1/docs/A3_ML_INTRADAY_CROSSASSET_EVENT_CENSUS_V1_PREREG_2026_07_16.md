# A3 ML Intraday Cross-Asset Event Census V1 Preregistration

Date: 2026-07-16

## Purpose

Test whether causal intraday U.S. dollar-index and U.S. Treasury-bond price CFD
proxies can identify higher-frequency XAUUSD opportunities that survive
realistic Bid/Ask execution and the locked target-broker cost stress.

This preregistration is committed before joining the new cross-asset features to
gold outcomes. The complete machine-readable rules are in
`config/ml/a3_ml_intraday_crossasset_event_census_v1.json`.

## Economic Direction

For a potential gold long, a falling dollar and rising Treasury-bond price are
treated as supportive. A rising dollar and falling bond price support a gold
short. The bond CFD is a price proxy, so its sign is opposite the usual yield
interpretation.

The four fixed families test:

1. Joint dollar-and-bond agreement with immediate gold confirmation.
2. A dollar impulse while the bond proxy is not strongly opposing.
3. A bond-price impulse while the dollar proxy is not strongly opposing.
4. Persistent macro agreement followed by a small gold catch-up move.

The feeds are Dukascopy CFDs. They are not ICE DXY, exchange Treasury futures,
Treasury yields, exchange volume, or order flow.

## Causality

- Decisions occur only after completed UTC-aligned M15 bars from 06:00 through
  19:59 UTC.
- M15 bars require three contiguous M5 source bars.
- Source returns use exact observations without forward fill or crossing gaps.
- Return normalization uses a one-bar-lagged rolling volatility scale.
- Gold signals use Mid prices; simulated entries and exits use executable
  Bid/Ask prices on the next contiguous M5 bar.
- No future regime, volatility, spread, price, or outcome enters a feature.

## Chronology

| Segment | Window |
|---|---|
| Train | 2019-01-01 to 2021-12-31 |
| Validation | 2022-01-01 to 2022-12-31 |
| Internal test | 2023-01-01 to 2023-12-31 |
| Exam | 2024-01-01 to 2026-06-30 |
| Prospective holdout | From 2026-07-01 |

Each family and direction is a separate hypothesis. Validation opens only after
its train gates pass, internal test opens only after validation passes, and exam
opens only after internal test passes. The historical exam is not claimed as an
untouched holdout because this program has already examined gold history.

## Execution Lock

- Fixed 0.01 lot.
- Stop distance is the maximum of 1.25 causal XAU ATR, a buffered signal-bar
  structural stop, and the locked $7.00 minimum.
- Target is 1.5R and maximum hold is 12 hours.
- Target-broker spread floor is $0.75, with an additional $0.30 cost per trade
  and $0.35 per 24 hours held.
- Same-bar ambiguity is resolved stop first.
- Initial risk may not exceed $50 and stressed entry cost may not exceed 0.15R.

## Selection Lock

There are four families and two directions, for at most eight hypotheses. There
is no parameter grid, context subgroup promotion, or same-iteration tuning.
Train selection requires adequate event count, PF, average R, month stability,
drawdown, winner-removal robustness, and a positive 2.5% calendar-month
bootstrap bound. Later segments use progressively stronger economic gates.

The portfolio research target is one qualified trade per source day, with two
per day aspirational. Frequency never overrides positive expectancy or risk
gates.

## Decision Outcomes

- A family-direction pair that fails train is rejected without using later
  segments for selection.
- A final research survivor must pass train, validation, internal test, and exam.
- No survivor means this cross-asset branch is rejected without threshold repair
  in this iteration.
- At least 2,000 resolved candidates, two final survivors, and both long and
  short representation are prerequisites for considering a separate ML-label
  review. They do not automatically authorize training.

## Authorization

This is research only. It does not authorize model training, Python demo
predictions, EA consumption, broker action, or live trading.
