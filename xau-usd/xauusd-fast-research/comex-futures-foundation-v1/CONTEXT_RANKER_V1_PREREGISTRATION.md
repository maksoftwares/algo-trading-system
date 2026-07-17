# COMEX Context Ranker V1 Preregistration

Date: `2026-07-17`

## Question

Can completed spot trend, range, volatility, spread, and tick context rank the two
mechanical COMEX flow candidate families well enough to isolate positive stressed
expectancy without changing their entries or labels?

## Chronology

- Fit: `2022-07-01` through `2023-06-30`.
- Calibration: `2023-07-01` through `2024-06-30`.
- Validation: `2024-07-01` through `2025-06-30`.
- Exam: `2025-07-01` through `2026-06-30`, prohibited in this run.

The model is fit once per candidate family. Its threshold is the greater of zero
or the calibration-score 90th percentile. Validation is decision-ineligible if
calibration fails. Exam remains unscored unless calibration and validation pass.

## Features And Model

The fixed features are direction-adjusted COMEX flow and impulse, absolute flow
and impulse, short-window volume, and completed Dukascopy M5 returns, EMA trend,
one-hour range location, ATR regime, spread, quote intensity, spot tick imbalance,
microprice edge, efficiency, candle body, local hour, and weekday. No outcome,
future bar, observer result, account state, or exam statistic is a feature.

Each family uses one `HistGradientBoostingRegressor` with 150 iterations, learning
rate 0.05, 15 leaves, 200 minimum samples per leaf, L2 regularization 3.0, and
random seed 42. There is no parameter grid.

## Selection And Gates

Selection allows one open trade per family, a 15-minute post-exit cooldown, and at
most two trades per family per day. Calibration requires at least 100 trades,
0.25 trades per weekday, stress PF 1.10, average stress R 0.02, drawdown at most
30R, and positive P&L after removing the five largest winners. Validation tightens
PF to 1.15, average stress R to 0.03, and drawdown to 25R.

This experiment is research-only. No model, prediction, EA, demo, or broker action
is authorized by a retrospective pass.
