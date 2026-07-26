# Causal Horizon Interaction Models V7 Preregistration

## Purpose

V7 tests whether the action-ranking failure is caused by Adaptive V5's shared
market-feature slopes across fast, intraday, and swing actions. In V5, all rows for
one event have identical market features, so a pooled linear model can vary action
scores mainly through fixed action offsets. Regime-local fitting can change those
offsets by regime, but it still cannot learn a general context-dependent horizon.

All outcomes through 2026-06-30 are exposed development evidence. V7 cannot create
promotion, shadow, demo, live, EA, sizing, or broker authority.

## Frozen Population And Method

V7 preserves Adaptive V5's corrected V4 action population, labels, structural
weights, lane ownership, unsafe-shock exclusion, clipped stress-R target, ridge
alpha, four training variants, three retention quantiles, calibration-only policy
selection, fixed-action comparator, six purged folds, acceptance gates, bootstrap,
and random seeds.

## Single Authorized Change

The 58 V5 features remain present. The six action descriptor features are separated
from the other 52 event features. V7 mechanically adds:

- every event feature multiplied by `action_intraday`;
- every event feature multiplied by `action_swing`.

`FAST_1R_4H` is the reference action. This creates exactly 104 interactions and 162
total model features. No event feature or interaction is hand-picked, removed, or
chosen from an outcome subgroup. The ridge model partially pools the common base
slopes while allowing intraday and swing slopes to differ from fast slopes.

## Evaluation

Each lane and fold is fit and calibrated exactly as in V5. V7 must pass every V5
absolute gate, including all six calibration folds, positive confidence bounds,
drawdown, stability, frequency, AUC, and nonnegative F2026 mean/action uplift with
F2026 PF at least 1.05.

It must also not regress from V5 in aggregate selected mean R, aggregate PF, or
F2026 mean R, and must retain at least 90% of V5 candidate-event frequency. Passing
would be a development lead only; failing retires this fixed interaction design.

## Prohibitions

- No outcome-derived action rule, regime rule, threshold, or feature subset.
- No same-version alpha, interaction, training-window, or gate tuning.
- No claim that candidate-event frequency is executable trade frequency or P&L.
- No MT5, runtime, observer, deterministic specialist, account, or broker change.
