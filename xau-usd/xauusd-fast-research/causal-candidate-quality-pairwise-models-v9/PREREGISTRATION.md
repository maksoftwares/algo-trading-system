# Causal Candidate Quality Pairwise Models V9 Preregistration

## Purpose

V9 tests whether V8's action-ranking failure comes from using a pointwise return
target for a within-event ranking decision. The event and action tasks remain
separate, but both are now binary classification problems aligned to their actual
decisions:

1. does the event have any positive stressed available action;
2. for each available action pair, which action produces the higher stressed R.

All outcomes through 2026-06-30 are exposed development evidence. V9 cannot create
promotion, shadow, demo, live, EA, sizing, portfolio, or broker authority.

## Frozen Population And Method

V9 preserves Adaptive V5's corrected V4 action population, stress labels, event and
structural weights, lane ownership, unsafe-shock exclusion, four training variants,
three retention quantiles, calibration-only policy selection, fixed-action
comparator, six purged folds, economic gates, bootstrap, and random seeds.

Both classifiers use standardized L2 logistic regression with `C=0.05`, `lbfgs`,
and at most 2,000 iterations. This fixed specification is reused from the earlier
causal event-action classification work; no V9 hyperparameter search is allowed.
Each lane/fold uses one shared training variant for both classifiers.

## Event Classifier

- Features: the 52 frozen causal non-action event features.
- Target: true when at least one causally available action has positive
  `stress_net_r`.
- Representation: the target is repeated across available action rows. Their
  structural weights must sum exactly to the event evaluation weight.
- Use: the predicted probability is the sole event-retention score.

## Pairwise Action Classifier

- Actions are oriented in the frozen order fast, intraday, then swing.
- Features are left-minus-right differences across the 58 V5 base features and
  the frozen 104 V7 horizon interactions, for exactly 162 pairwise features.
- Target: true when the left action has strictly higher `stress_net_r` than the
  right action.
- Exact outcome ties receive zero fitting weight but remain scored at inference.
- Non-tied pair weights sum to the event evaluation weight, preventing events with
  more available comparisons from receiving greater training influence.
- At inference, each action receives the mean probability that it beats its
  available opponents. The largest mean pairwise win probability is selected;
  frozen action order and candidate ID break exact score ties.

Missing actions are never imputed. Pair availability and all feature differences
are determined without reading pair outcomes. No feature, action, regime, model
variant, threshold, or rule is selected from a test partition.

## Evaluation

Calibration may select only one shared training variant and one frozen retention
quantile. The primary predictive metric is event tradeability AUC. Pairwise AUC,
chosen-action outcome AUC, and hindsight-best action accuracy are diagnostics.

Every lane must pass all frozen V5 economic, stability, drawdown, frequency,
confidence-bound, action-uplift, and latest-fold gates. It must also not regress
from V5 in aggregate selected mean R, aggregate profit factor, or F2026 mean R and
must retain at least 90% of V5 selected candidate-event frequency. A pass is only a
development lead. A failure retires this exact pairwise design.

## Prohibitions

- No same-version classifier, feature, target, variant, threshold, gate, or seed
  tuning after V9 outcomes open.
- No use of F2026 to select or repair a V9 policy.
- No claim that candidate-event frequency is executable trade frequency or P&L.
- No MT5, runtime, observer, deterministic specialist, account, or broker change.
