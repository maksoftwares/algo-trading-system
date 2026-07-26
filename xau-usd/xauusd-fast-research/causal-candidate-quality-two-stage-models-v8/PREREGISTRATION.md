# Causal Candidate Quality Two-Stage Models V8 Preregistration

## Purpose

V8 tests one mechanism-level correction to the failed Adaptive V5 and Horizon V7
models: event tradeability and action-horizon selection are different prediction
problems and should not share one regression target.

The first stage estimates whether an event has any profitable available action under
the frozen stress-cost label. The second stage ranks the available fast, intraday,
and swing actions by their return advantage within that event. The selected action
is retained only when the first-stage event score passes a calibration-only
threshold.

All outcomes through 2026-06-30 are already exposed development evidence. V8 cannot
create promotion, shadow, demo, live, EA, sizing, portfolio, or broker authority.

## Frozen Population And Base Method

V8 preserves Adaptive V5's corrected V4 action population, labels, event and
structural weights, lane ownership, unsafe-shock exclusion, ridge alpha, four
training variants, three retention quantiles, calibration gates, fixed-action
comparator, six purged folds, acceptance gates, bootstrap, and random seeds.

Each fold uses one shared training variant for both stages. Calibration can select
only that shared variant and one of the three frozen retention quantiles. It cannot
select a separate event-stage and action-stage variant.

## Authorized Model Change

### Event stage

- Features: the 52 frozen causal event features, excluding all six action
  descriptors.
- Target: maximum available-action `stress_net_r` for the event, clipped to
  `[-3.0R, 2.5R]`.
- Representation: the target is repeated across available action rows, whose
  structural weights must sum exactly to the event evaluation weight. This prevents
  events with three actions from receiving three times the training influence.
- Score use: event retention only.

### Action stage

- Features: all 58 V5 base features plus the frozen 104 V7 horizon interactions.
- Target: each action's `stress_net_r` minus the arithmetic mean `stress_net_r` of
  the available actions for that event, clipped to `[-3.0R, 3.0R]`.
- Score use: choose the highest predicted action advantage, with the frozen action
  tie order and candidate ID as deterministic fallbacks.

Missing actions remain missing and are never imputed. No feature, action, regime,
training window, or threshold is selected from a test partition.

## Evaluation

V8 is evaluated once on the same six purged out-of-time folds as V5. The primary
AUC is the event-stage score against whether the event's best available stressed
action is positive. Chosen-action outcome AUC and exact best-action accuracy are
diagnostics only.

Each lane must pass every frozen V5 absolute economic, stability, drawdown,
frequency, confidence-bound, and latest-fold gate. It must also not regress from V5
in aggregate selected mean R, aggregate profit factor, or F2026 mean R, and it must
retain at least 90% of V5 selected event frequency. A pass is a development lead,
not runtime approval. A failure retires this exact two-stage design.

## Prohibitions

- No same-version target, feature, model, variant, quantile, gate, or seed tuning.
- No direct comparison-driven repair after reading V8 test outcomes.
- No claim that event frequency is executable trade frequency or realized P&L.
- No MT5, runtime, observer, deterministic specialist, account, or broker change.
