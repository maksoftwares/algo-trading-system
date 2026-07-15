# A3 ML Dukascopy Microstructure Regime V1 Preregistration

Date: `2026-07-16`

## Purpose

Test whether causal information absent from the rejected candle-only campaigns can rank mechanically defined XAUUSD specialist candidates after actual bid/ask costs.

This is a research campaign. It cannot authorize Python demo predictions, EA consumption, broker action, or deployment.

## Data Lock

- Official Dukascopy bid/ask ticks and top-of-book bid/ask volumes.
- Synchronized `XAUUSD`, `XAGUSD`, `EURUSD`, and `USDJPY` coverage.
- `GBPUSD` is excluded because verified local coverage is incomplete.
- Contiguous research period: `2018-07-01` through `2024-06-30`.
- The run must inventory and hash every consumed Parquet input.

## Chronological Firewall

| Segment | Period | Opening rule |
| --- | --- | --- |
| Train | 2018-07 through 2020-06 | Open |
| Validation | 2020-07 through 2021-06 | Open for the frozen campaign |
| Internal test | 2021-07 through 2022-06 | Open only if a validation policy passes every gate |
| Exam | 2022-07 through 2024-06 | Open only if the same frozen policy passes every internal-test gate |

No random split, shuffled split, threshold search, model search, or post-outcome family change is allowed.

## Separate Specialists

1. `TREND_PULLBACK`: trade a completed-bar EMA reclaim in the detected trend direction.
2. `TREND_BREAKOUT`: trade a completed-bar break of the prior 12-bar boundary in the detected trend direction.
3. `RANGE_FADE`: fade a new 1.5-standard-deviation excursion while the range regime is active.
4. `SHOCK_CONTINUATION`: follow the direction of a one-ATR 15-minute shock.
5. `SHOCK_REVERSAL`: fade the same shock as an independently scored candidate.

Transition/undefined conditions produce no candidate.

Each family must first pass the frozen train-only raw-quality gate. This prevents ML from being asked to rescue a deeply losing candidate family.

## New Causal Information

At each completed M5 bar, the model may use only information timestamped at or before that bar's close:

- signed tick-direction imbalance over 5, 15, and 60 minutes;
- quote intensity and its trailing ratio;
- realized tick volatility and acceleration;
- mean/latest spread, spread shock, and price efficiency;
- top-of-book volume imbalance and microprice edge;
- synchronized XAGUSD, EURUSD, and USDJPY returns;
- causal ATR, EMA, hour, weekday, regime, family, and direction fields.

No feature may use entry-bar or post-entry data.

## Execution Lock

- Decision after a completed M5 bar; entry at the next contiguous M5 executable open.
- Long entry uses ask; long exits use bid.
- Short entry uses bid; short exits use ask.
- Initial risk: `1.0 x ATR14`.
- Target: `1.5R`.
- Maximum hold: 12 M5 bars.
- Maximum entry spread: `0.25R`.
- Same-bar stop/target collision: stop first.
- Stress result subtracts an additional `0.10R` per trade.
- Missing or non-contiguous execution windows are rejected, not filled synthetically.

## Model Lock

One histogram gradient-boosting regressor predicts stressed net R. Hyperparameters, features, seed, and three train-score retention fractions are frozen in the JSON contract. There is no alternative model family.

The model ranks and rejects specialist candidates. It does not invent unrestricted buy/sell decisions.

## Promotion Gates

Validation and internal test require, among other locked checks:

- at least `0.50` trades per source day and no more than `3.0`;
- stressed PF at least `1.10`;
- positive stressed expectancy;
- controlled closed-trade drawdown;
- at least half of active months positive;
- positive net result after removing the ten largest winners;
- measurable ranking signal through frozen AUC/Spearman checks.

The two-year exam is stricter: stressed PF at least `1.15`, average stressed result at least `0.04R`, and at least 55% positive active months.

## Decision Rule

Failure is a valid result and must be preserved. Rules may not be loosened after outcomes are seen. A research survivor still requires exact tick replay of selected trades, broker transfer testing, prospective shadow evidence, and account-level portfolio risk validation before any demo decision.
