# Adaptive Action Models V5 Preregistration

This contract is frozen before any V5 model is fitted or any V5 test prediction
is produced.

## Question

Can a small, calibration-selected training adaptation improve the stability of
the corrected Action V4 ridge model without changing its candidate population,
features, target, actions, folds, economic gates, or evaluation formulas?

## Frozen Variants

Every variant uses ridge regression with alpha 20 and the same 58 causal
features and clipped stressed-R target.

1. `EXPANDING`: all causally eligible FIT history.
2. `ROLLING_36M`: only the final 36 months of FIT history.
3. `RECENCY_H12M`: all FIT history with a 12-month half-life, a 0.01 weight
   floor, and weight-sum normalization so regularization strength is comparable.
4. `REGIME_LOCAL`: a separate model for each signal-time regime when that
   lane/regime has at least 650 action rows and 200 events; otherwise the
   expanding global ridge model is used for that regime.

No other lookback, half-life, model class, regime grouping, fallback, or
hyperparameter is permitted in this version.

## Nested Walk-Forward Selection

For each disjoint lane and fold, all four variants fit on FIT only. Each variant
ranks available actions on CALIBRATION and is evaluated at the frozen 100%,
80%, and 60% retention policies. The existing Action V4 calibration gates and
deterministic objective choose exactly one variant and threshold. TEST is then
opened once. Action V4's deterministic fixed-action cascade remains the
benchmark.

The six July-to-July test folds, structural episode weights, weekly block
bootstrap, acceptance gates, and UNSAFE_SHOCK abstention are unchanged. F2026
and all earlier history are exposed development evidence, never pristine proof.

## Authority

Offline fitting and calibration are authorized only inside this package.
Portfolio simulation, Python serving, ML shadow, EA consumption, demo/live
trading, sizing, terminal changes, and broker action remain forbidden.
