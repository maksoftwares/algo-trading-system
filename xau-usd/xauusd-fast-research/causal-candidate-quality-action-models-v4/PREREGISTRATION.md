# Action Models V4 Corrected-Data Replay Preregistration

This contract is frozen before any Action V4 model is fitted or any V4 test
prediction is produced.

## Question

Does the exact frozen Action V3 methodology produce defensible action-ranking
and veto evidence after correcting `prior_events_1h` and `prior_events_4h` in
the source dataset?

## Method Parity

Action V4 is a strict corrected-data replay. The disjoint lane ownership,
UNSAFE_SHOCK abstention, 58-feature surface, target, ridge and histogram
gradient-boosting specifications, action tie order, calibration retention
quantiles, calibration gates, acceptance gates, six purged folds, bootstrap,
random seeds, and all evaluation formulas must exactly equal Action V3.

Only the versioned dataset inputs and output names may differ. The V4 package
must hash-lock the Action V3 configuration and reject execution if the
experimental contract differs. The shared model-mechanics source must retain
the frozen Action V3 SHA-256.

## Evaluation

Each fold fits on FIT only, chooses its model and threshold on CALIBRATION only,
and evaluates once on TEST. The three lanes remain disjoint. All confidence
intervals retain the fixed 5,000-resample UTC-week block bootstrap.

The prior V3 result is used only after V4 result construction to report deltas.
It cannot select a model, action, threshold, or gate. All history, including
F2026, is exposed development evidence and is not a pristine holdout.

## Authority

Offline model and threshold fitting are authorized only inside this package.
Portfolio simulation, Python serving, ML shadow, EA consumption, demo/live
trading, sizing changes, terminal changes, and broker action remain forbidden
regardless of the result.
