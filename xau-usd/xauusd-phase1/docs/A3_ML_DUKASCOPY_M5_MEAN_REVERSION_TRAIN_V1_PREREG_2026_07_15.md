# A3 ML Dukascopy M5 Mean Reversion Train V1 Preregistration

Date: `2026-07-15`

Status: `LOCKED_BEFORE_TRAIN_OUTCOMES`

## Objective

Test whether frequent XAUUSD M5 overextensions have positive mean-reversion expectancy after verified bid/ask costs. This is a mechanically distinct response to the rejected trend-continuation family.

Only `2018-07-01` through `2021-06-30` may be evaluated. Validation, test, and the new `2024-07` through `2026-06` holdout remain closed.

## Frozen Matrix

Twelve profiles combine:

- Bollinger `20` z-score at `2.0` plus RSI `14` at `30/70`;
- a three-M5-bar impulse of at least `1.5 ATR` faded from an extreme close;
- a prior-12-bar extreme sweep followed by a close back inside the range;
- either no regime restriction or a completed-H1 range filter;
- `1.0R` and `1.5R` targets.

The H1 range filter requires EMA20/EMA50 separation no greater than `0.5 H1 ATR` and EMA20 three-bar slope no greater than `0.25 H1 ATR`. Every higher-timeframe value must come from a completed H1 bar.

All profiles use a `2.0 M5 ATR` stop with a `350`-point floor and `1,800`-point ceiling. Signals enter only after the M5 bar closes.

## Execution And Gates

Execution uses raw Dukascopy bid/ask ticks, fixed `0.01` lot, actual spread, maximum spread `75` points, maximum spread-to-stop cost `0.10R`, `$0.30` extra stress, and `$0.35` holding stress per 24 hours. One position per profile, a five-minute cooldown, and 12 entries per UTC+4 server day are enforced.

The profitability, frequency, direction-balance, drawdown, monthly concentration, top-25 removal, and calendar-bootstrap gates are identical to the preceding train campaign. At most one all-gate survivor may be selected by PF, then frequency, then family ID.

A train survivor only authorizes freezing one profile for later evaluation. It grants no validation, test, prediction, EA, demo, live, or broker permission.
