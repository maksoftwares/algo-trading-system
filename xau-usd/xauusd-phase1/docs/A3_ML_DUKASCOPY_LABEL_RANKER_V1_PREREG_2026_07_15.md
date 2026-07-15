# A3 ML Dukascopy Label Ranker V1 Preregistration

Date locked: `2026-07-15`

## Question

Can one fixed, interpretable ML ranker identify a stable positive subset inside the already frozen and independently unprofitable `dukascopy_h1_symmetric_ema_pullback_v1` candidate family?

The ranker may score and reject candidates. It may not change the candidate rule, stop, target, cost model, labels, or chronological splits.

## Evidence Boundary

- Input: resolved rows from `A3_ML_DUKASCOPY_LABEL_FACTORY_LABELS.csv` only.
- Required upstream result: `DUKASCOPY_LABEL_DATASET_READY_FAMILY_NO_SURVIVOR`.
- Train: July 2018 through June 2021.
- Validation: July 2021 through June 2023.
- Test: July 2023 through June 2024.
- The raw family aggregate test result has already been observed. The ranker's test probabilities and selected-subset result have not.
- No model, feature, threshold, or gate changes are permitted after fitting begins.

## Frozen Features

All are available at the entry quote:

1. Direction indicator.
2. Direction-adjusted EMA20 slope divided by ATR.
3. Absolute EMA20-to-EMA50 gap divided by ATR.
4. Absolute signal-close-to-EMA20 distance divided by ATR.
5. Signal candle body fraction.
6. Direction-adjusted close location.
7. EMA touch distance divided by ATR.
8. Stop distance divided by ATR.
9. `log1p` signal-bar tick count.
10. ATR divided by signal price.
11. Entry spread divided by stop distance.
12. Sine and cosine of UTC decision hour.
13. Sine and cosine of UTC decision weekday.

Forbidden features include exit reason, exit time, P/L, R outcome, MFE, MAE, holding time, future regime, future volatility, and observer events logged after entry.

## Frozen Model

- L2-regularized logistic regression.
- Standardization fitted on train rows only.
- Adam optimizer, `3,000` iterations.
- Learning rate `0.025`.
- L2 coefficient `0.05`.
- No class weighting, resampling, hyperparameter search, feature selection, ensembling, or calibration fitting.

## Frozen Selection Rule

1. Fit once on train.
2. Score validation.
3. Select the highest-probability `25%` of validation rows, rounding the row count upward and using candidate ID as the deterministic tie-breaker.
4. Freeze the lowest selected validation probability as the numerical cutoff.
5. Apply that unchanged cutoff once to test.

The test set is not used to choose coverage or cutoff.

## Frozen Gates

All must pass for a research survivor:

- Validation AUC at least `0.55`.
- Test AUC at least `0.53`.
- At least `250` selected validation rows.
- At least `100` selected test rows.
- At least `40` selected test rows in each direction.
- Selected validation stress PF at least `1.15`.
- Selected test stress PF at least `1.10`.
- Selected validation average stress R at least `0.05`.
- Selected test average stress R nonnegative.
- Selected test maximum closed drawdown no more than `20R`.
- Test selection coverage from `10%` through `40%`.
- At least `60%` positive active exit months in selected validation and selected test.
- The lower `2.5%` bound of a fixed-seed `2,000`-sample calendar-month bootstrap of selected-test average stress R must be above zero.
- Validation and test Brier scores must each beat the constant train-prior predictor.

## Decision Classes

- `DUKASCOPY_LABEL_RANKER_RESEARCH_SURVIVOR`: every gate passes.
- `DUKASCOPY_LABEL_RANKER_NO_SURVIVOR`: the run is valid but at least one gate fails.
- `DUKASCOPY_LABEL_RANKER_INVALID`: input identity, split, causality, or population checks fail.

Even a research survivor remains offline-only. Demo prediction, EA consumption, broker action, and deployment remain disabled.
