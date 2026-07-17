# XAUUSD ML Candidate Rankers V1 Preregistration

Date: `2026-07-17`

## Question

Can causal Dukascopy tick-imbalance and quote-intensity features rank two broad,
mechanical XAUUSD candidate families well enough to produce positive stressed
walk-forward trading evidence?

## Candidate Families

1. `ML_M15_MOMENTUM_RANKER_V1`: completed M15 directional expansion. The last
   one-hour return must be at least `0.50 ATR(14)`, the current candle must agree
   with that direction, body fraction must be at least `0.35`, and efficiency
   ratio over 16 bars must be at least `0.25`. Stop `1.50 ATR`, target `2R`, maximum
   hold eight hours.
2. `ML_M15_REVERSION_RANKER_V1`: completed M15 close at least `1.50` prior-window
   standard deviations from the prior 32-bar mean while 16-bar efficiency ratio
   is at most `0.45`. Direction is toward the prior mean. Stop `1.25 ATR`, target
   `1.50R`, maximum hold six hours.

Entry is the next contiguous M5 open, long at Ask and short at Bid. Exits use the
opposite executable side. Native spread is embedded. Stress subtracts `$0.30`,
`$0.35` per 24 hours held, and `0.05R`. Stop/target collisions are stop-first.

## Features

Only values known at the completed M15 signal time are allowed:

- direction-adjusted 15-minute, 1-hour, 4-hour, and 24-hour returns;
- ATR-normalized momentum and range;
- ATR ratio, body fraction, direction-adjusted close location;
- 16-bar efficiency ratio and EMA32 distance;
- causal M15 quote-intensity ratio;
- last completed M5 `tick_imbalance_5m`, `tick_imbalance_15m`, and
  `quote_intensity_ratio`, direction-adjusted where directional;
- executable spread divided by M15 ATR;
- UTC hour and weekday sine/cosine encodings.

No observer outcome, account state, future regime, future bar, or broker result is
a feature.

## Label

Each candidate receives its independent native Bid/Ask trade outcome under the
frozen stop, target, hold, and stress costs. The regressor target is stressed R.
Overlapping labels are permitted for model learning but selected trades enforce
one open position per family, a two-hour cooldown, and at most two entries per UTC
day.

## Model

One fixed `HistGradientBoostingRegressor` per family:

- learning rate `0.05`;
- maximum iterations `100`;
- maximum leaf nodes `15`;
- minimum samples per leaf `100`;
- L2 regularization `1.0`;
- random seed `42`.

For each walk-forward stage, the available history is split chronologically: first
80% fit, last 20% calibration, with an eight-hour purge. The score threshold is
the greater of zero or the calibration 80th percentile. The model is not refit
after threshold calibration. This is a ranker, not a probability claim.

## Walk-Forward Windows

- Train evaluation: 2018-07-01 through 2020-06-30, fit/calibrate only earlier data.
- Validation: 2020-07-01 through 2022-06-30.
- Internal test: 2022-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Recent tail is the fixed exam-model subset from 2025-07-01 through 2026-06-30;
  no tail refit is allowed.

Later stages are decision-ineligible after the first failed stage. No period is
described as untouched because the repository has inspected retrospective data.

## Gates

Every family must pass sample size, frequency, stress PF, average stress R, active
month stability, drawdown, and winner-removal gates. A combined portfolio requires
both survivors, at least `0.80` trades per source day, stress PF `1.30`, average
stress R `0.05`, drawdown at most `25R`, no more than two concurrent trades, and no
more than four entries per day. Survivor pairs must have same-direction entries
within 60 minutes at or below 20% and absolute daily stress-P&L correlation at or
below 0.60.

## Anti-Overfit And Authorization

There is one fixed candidate definition and one fixed model per family. There is
no parameter grid and no same-version repair. Research only; model files, scores,
or a retrospective pass cannot authorize Python predictions, EA consumption,
demo orders, or live orders.
