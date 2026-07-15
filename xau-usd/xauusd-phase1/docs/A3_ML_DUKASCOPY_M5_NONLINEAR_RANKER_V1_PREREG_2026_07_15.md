# A3 ML Dukascopy M5 Nonlinear Ranker V1 Preregistration

Date: `2026-07-15`

Status: `LOCKED_BEFORE_MODEL_OUTCOMES`

## Objective

Test one bounded nonlinear hypothesis: shallow feature interactions may rank the six frozen M5 candidate families even though L2 logistic regression could not.

## Frozen Model

Use one scikit-learn histogram gradient-boosting classifier:

- learning rate `0.05`;
- `200` iterations;
- maximum `7` leaves and depth `3`;
- minimum `100` rows per leaf;
- L2 regularization `1.0`;
- fixed seed `20260715`;
- early stopping disabled.

No hyperparameter search, feature change, family change, or additional retention threshold is allowed.

The model inherits the exact hash-bound linear-ranker inputs, causal features, grouped-event selection, maximum-two-position portfolio, chronological splits, four retention fractions, validation gates, internal-test gates, and reserved-date prohibition.

If no validation fraction passes, internal test is suppressed. If one passes, select by PF then frequency and freeze its probability cutoff before scoring internal test. No result authorizes Python predictions, EA consumption, demo, live, or broker action.
