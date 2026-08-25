# V60 Causal Protection-Action Utility V21 Preregistration

Date locked: 2026-08-25 UTC, before extracting any action-time feature
relationship or fitting the model described below.

Status: retrospective, outcome-exposed, read-only diagnostic. This experiment
cannot authorize broker actions, change deployed V60, or change frozen Dynamic
V6. Any nominated policy requires a separate preregistered path-dependent
replay and clean prospective confirmation.

## Question

At an actual frozen Dynamic V6 `OPEN_PROFIT_GIVEBACK` decision, do causal
properties of the open basket identify the uncommon actions where retaining a
position until its already-frozen source endpoint would have produced more
utility than closing it immediately?

This is not a generic specialist-health rule, a threshold search, or a direct
policy simulation. It is the final diagnostic in the profit-protection lane
after V18 and V20 rejected broad and V7-only exemptions.

## Frozen runtime and identity

The diagnostic wraps the exact Dynamic V6 scenario and shared tick replay. The
wrapper may only observe state immediately before the parent protection method
runs. The following must match frozen V6 exactly:

- ordered accepted trade IDs;
- ordered close timestamps, close reasons, and closed P/L;
- veto audit rows;
- total trades, net P/L, profit factor, win rate, closed drawdown, and equity
  drawdown;
- no open-position, flat-state, or floating-state deadlock.

Any difference is an implementation failure and invalidates all model results.

## Observation unit

One protection action is identified by:

`giveback timestamp UTC + sorted open trade IDs`

One row is recorded for each position closed by that action. Every row from an
action receives sample weight `1 / positions_in_action`, so a multi-position
basket contributes the same total fitting weight as a one-position basket.
All acceptance statistics are also reported at action-cluster level to avoid
pretending simultaneous closes are independent observations.

## Causal snapshot

Only values available immediately before the frozen giveback close may be model
features. The fixed feature set is:

Categorical:

- `source_id`
- `direction`

Numeric:

- `own_open_pnl_r`: current marked position P/L divided by its initial risk;
- `basket_open_pnl_r`: aggregate marked basket P/L divided by active initial
  risk;
- `basket_peak_pnl_r`: frozen protection peak P/L divided by active initial
  risk;
- `basket_giveback_from_peak_r`: peak minus current basket P/L, divided by
  active initial risk;
- `own_risk_share`: position initial risk divided by active initial risk;
- `own_open_pnl_share`: position marked P/L divided by the absolute aggregate
  marked P/L, with zero when the denominator is zero;
- `holding_hours`: elapsed time since the position's candidate entry;
- `minutes_since_protection_arm`: elapsed time since the current protection
  episode armed;
- `open_position_count`;
- `close_hour_sin` and `close_hour_cos`, calculated from UTC minute of day.

The snapshot may retain identifiers and timestamps for audit, but they are not
features. Candidate endpoint P/L, endpoint exit time, future maximum adverse or
favourable excursion, future prices, eventual close reason, calendar year, and
fold identity are forbidden features.

## Label

The label is used only after the causal snapshot is frozen:

`keep_open_utility_r = (source_endpoint_pnl_usd - protected_close_pnl_usd) / initial_risk_usd`

A positive value means the already-frozen endpoint would have outperformed the
actual protection close for that position. This counterfactual ignores later
portfolio capacity and therefore cannot itself prove portfolio improvement.

## Fixed model

There is one model and no hyperparameter, feature, threshold, or fold search:

- numeric features: median imputation followed by `StandardScaler`;
- categorical features: most-frequent imputation followed by
  `OneHotEncoder(handle_unknown="ignore")`;
- estimator: `Ridge(alpha=10.0, fit_intercept=true)`;
- fitting weights: `1 / positions_in_action`;
- prediction: expected `keep_open_utility_r`;
- diagnostic skip nomination: predicted utility strictly greater than zero.

No classification model, nonlinear model, probability threshold, source
exclusion, calibration, or alternate alpha is permitted in V21.

## Fixed expanding annual folds

Rows are assigned by protection-action timestamp. No shuffled or random split
is allowed.

| Fold | Training actions | Evaluation actions |
|---|---|---|
| F1 | 2021-2022 | 2023 |
| F2 | 2021-2023 | 2024 |
| F3 | 2021-2024 | 2025 |
| F4 | 2021-2025 | 2026 through the frozen historical end |

Rows from one action must remain entirely in one fold. Model diagnostics such
as MAE, weighted R-squared, and rank correlation are descriptive only.

## Fixed acceptance gates

V21 may nominate exactly one later path-dependent V22 experiment only if all
of the following pass:

1. Exact frozen Dynamic V6 behavioral parity passes.
2. Every feature is demonstrated to be available before the giveback close and
   no forbidden field enters the preprocessing or model matrix.
3. All four fixed evaluation years contain predictions.
4. At least 20 position rows across at least 12 distinct protection actions are
   nominated to skip in the combined evaluation folds.
5. Every evaluation fold contains at least three distinct nominated actions.
6. The realized weighted keep-open utility of nominated rows is positive in at
   least three of four evaluation folds.
7. The realized weighted keep-open utility is nonnegative separately in 2025
   and 2026.
8. Combined realized weighted keep-open utility is positive.
9. No single action contributes 50% or more of combined positive nominated
   utility.
10. A deterministic action-cluster bootstrap with seed `20260825`, 10,000
    resamples, and year-stratified sampling has a strictly positive 10th
    percentile for combined mean nominated utility R.

The bootstrap resamples whole actions with replacement within each evaluation
year and combines the sampled action-weighted utility. Missing or non-finite
values fail closed.

## Decisions

- `DIAGNOSTIC_NOMINATES_PATH_DEPENDENT_V22`
- `NO_STABLE_PROTECTION_UTILITY_KEEP_V6`
- `INVALID_BEHAVIOR_OR_CAUSALITY_PARITY_FAILURE`

A positive result is still exposed pseudo-out-of-time evidence, not causal
out-of-sample authorization. A separately locked V22 would have to replay the
policy path-dependently, preserve the canonical V6 metric and cost-stress
battery, and then collect clean Capital.com prospective evidence. A negative
result closes the protection-management research lane without trying another
variant.

