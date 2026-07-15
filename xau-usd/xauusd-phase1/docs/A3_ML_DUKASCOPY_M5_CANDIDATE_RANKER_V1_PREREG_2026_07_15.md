# A3 ML Dukascopy M5 Candidate Ranker V1 Preregistration

Date: `2026-07-15`

Status: `LOCKED_BEFORE_MODEL_OUTCOMES`

## Objective

Determine whether a causal ML ranker can select positive-expectancy, frequent trades from the deterministic trend and mean-reversion candidate streams that were individually unprofitable.

ML ranks or rejects mechanical candidates. It does not invent entries, stops, targets, or directions.

## Population And Splits

Only six broad `1.5R` candidate families are included: H1 pullback, breakout, and trend sweep plus unrestricted band, impulse, and mean-reversion sweep fades. Nested H1/H4 and duplicate `1.0R` variants are excluded.

- train: `2018-07-01` through `2019-12-31`, 388 source days;
- model/cutoff selection: calendar 2020, 259 source days;
- frozen internal test: `2021-01-01` through `2021-06-30`, 127 source days;
- all dates after `2021-07-01` remain forbidden.

Rows from the same decision timestamp and direction are grouped before portfolio selection, preventing duplicate profile variants from becoming multiple trades. The selected stream allows no more than two concurrent positions.

## Frozen Models And Features

Two L2 logistic models differ only in regularization (`0.01` and `0.10`). Features are causal price-normalized signal shape, trend state, spread-to-risk, tick activity, cyclical UTC+4 server time, weekday, direction, and one-hot family identity. No exit, P&L, MFE, MAE, duration, or future regime feature is permitted.

The frozen validation retention fractions are `50%`, `40%`, `30%`, and `20%`. At most one model/fraction may be chosen on 2020 by PF, then frequency, then model ID and fraction. Its probability cutoff is frozen before the internal test is scored.

## Required Evidence

Validation must have AUC at least `0.53`, at least `0.65` trades per source day, PF at least `1.10`, nonnegative average R, both directions, and positive net after removing the top 10 winners.

Internal test must have AUC at least `0.52`, at least `0.65` trades per source day, PF at least `1.15`, average R at least `0.03R`, both directions, at least 50% positive exit months, drawdown no greater than `25R` and `$200`, positive net after removing the top 10 winners, and a positive calendar-month bootstrap `2.5%` average-R bound.

Failure at validation suppresses the internal test. Passing the internal test only creates a research survivor for a later untouched holdout. It grants no Python prediction, EA, demo, live, or broker authorization.
