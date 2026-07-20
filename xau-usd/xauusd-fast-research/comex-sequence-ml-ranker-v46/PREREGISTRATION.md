# COMEX Sequence ML Ranker V46 Preregistration

## Status And Question

V46 is a research-only Python ranking diagnostic. It grants no prediction, EA,
demo/live, account, terminal, or broker authority. V45 is a terminally rejected
raw strategy, but its 1,939 resolved development rows are valid executable
candidate labels. V46 asks whether a fixed low-capacity model can reject poor
V45 events while preserving the satellite density target.

This is disclosed successor research after broad history and aggregate V45
development economics have been exposed. No historical result can be treated as
a pristine holdout. Even an all-stage pass requires an unchanged new forward
shadow and a sealed V42 shared-account test.

## Frozen Inputs And Features

The source is the immutable V45 policy
`TC30__RL05__TS70__IM35__AC125`, contract SHA-256
`3e950672a46401187d2bcddbc2634c53bd862a420c15b2c8c19c59a26cec019b`.
The label is `profitable_after_stress`, derived from verified executable
Dukascopy bid/ask replay with V45's fixed costs and extra 0.05R stress.

Only candidate-time fields are allowed. The ordered model vector is:

1. log1p current five-second trade count;
2. log1p preceding thirty-second trade count;
3. log1p current five-second contract volume;
4. current signed-volume imbalance;
5. current same-side transition share;
6. log1p clipped arrival acceleration;
7. log1p terminal same-side run trades;
8. log1p terminal same-side run volume;
9. clipped current directional price impulse;
10. terminal direction sign; and
11. New York session progress from 08:20 to 13:30.

No entry, spread, ATR observed after the decision, exit, MFE, MAE, P/L, label,
future regime, candidate ID encoding, or date identity is a feature.

## Frozen Model And Chronology

The model is `HistGradientBoostingClassifier` with learning rate 0.05, 100
iterations, seven leaf nodes, minimum 50 samples per leaf, L2 regularization
1.0, early stopping disabled, and random seed 460046. No hyperparameter search,
feature selection, resampling, or class weighting is permitted.

- Fit: decisions from 2022-08-01 through 2023-07-01 whose exits are strictly
  before the fit boundary.
- Threshold calibration: candidates from 2023-07-01 through 2024-01-01. Their
  outcomes are not read by the trainer.
- Internal exam: 2024-01-01 through 2024-07-01. Its labels remain unread until
  the model bytes, features, and threshold are hashed and locked.
- Historical validation: 2024-07-01 through 2025-07-01, sealed unless the
  internal exam passes.
- Historical exam: 2025-07-01 through 2026-07-01, sealed unless validation
  passes.

The threshold selector uses only model scores and candidate facts. It requires
2.3869731801-3.3869731801 accepted candidates per eligible full weekday, at
least 80% active days, and at least 30% minority direction. It minimizes
distance from 2.8869731801/day and then prefers the higher score threshold.
No P/L or label participates in threshold selection.

## Gates

The internal exam, validation, and exam each require:

- rank AUC >= 0.55 on all resolved raw candidates;
- 2.3869731801-3.3869731801 accepted resolved trades/full weekday;
- positive base and stress net and positive mean stress P/L;
- base PF >= 1.20 and stress PF >= 1.10;
- at least 50% profitable full weekdays and positive calendar months;
- at least 20% accepted trades in each direction;
- first- and second-half stress PF >= 1.00;
- positive stress net after removing the five largest winners;
- closed stress drawdown <= USD 250; and
- centered-null five-weekday circular-block bootstrap one-sided p <= 0.01.

The internal exam requires at least 200 accepted trades; validation and exam
also require 200. The first failed stage terminates V46. Threshold changes,
retraining, feature changes, mirror labels, alternate seeds, or economic-rule
changes after the model lock are forbidden.

## Authority And Drawdown Firewall

V46 cannot rehabilitate raw V45, change Core, bypass V43's capital failure,
enter V42 without separate same-period evaluation, or interrupt V24.1/V26
forward collection. Model training is authorized only to create this hashed
research artifact. Python execution predictions, EA consumption, demo/live use,
and broker action remain false regardless of historical results.
