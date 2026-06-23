# CODEX PRE-LOCK ADDENDUM — A3 Python ML Signal-Quality Spec V1.2

**Project:** `maksoftwares/algo-trading-system`  
**Base specification:** `CODEX_A3_PYTHON_ML_SIGNAL_QUALITY_SPEC_V1_1_2026_06_21.md`  
**Review incorporated:** `A3_ML_SIGNAL_QUALITY_SPEC_V1_1_REVIEW_2026_06_21.md`  
**Revision date:** 2026-06-21  
**Scope:** A3 account `1033669`, XAUUSD, breakout-retest meta-labeling  
**Mode:** Repo-only / shadow-only  
**Broker action:** prohibited  
**A3 runtime:** `933200`, `933300`, and `933400` remain paused; profit-lock remains dry-run/disarmed  

---

# 1. Verdict

V1.1 is cleared for contract hash-lock after two small pre-lock protocol edits.

No architectural rewrite is required.

This V1.2 addendum adds:

```text
1. Direction-asymmetry validation for the pooled long/short model.
2. A conditionally eligible single direction-interaction feature.
3. An exact post-calibration definition of minority_events_min.
4. Per-fold purge, calibration, class-count, and feature-budget diagnostics.
5. A fail-closed response when the earliest fold starves the feature budget.
6. An owner-facing timeline expectation for CONTINUE_EVIDENCE.
```

After these changes are incorporated into the ML contracts:

```text
ML-00 inventory:                   GO
ML-00A execution/data contracts:  GO
ML-01 hash-lock:                  GO
Model training before ML-01:      NO-GO
A3 broker action:                 NO-GO
```

---

# 2. Files to add or update before ML-01

Add:

```text
docs/A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md
docs/A3_ML_FEATURE_BUDGET_CONTRACT_V1.md
docs/A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md
```

Update before hashing:

```text
docs/A3_ML_VALIDATION_PROTOCOL_V1.md
docs/A3_ML_MODEL_SELECTION_PROTOCOL_V1.md
docs/A3_ML_DATA_CONTRACT_V1.md
docs/A3_ML_POWER_MDE_PROTOCOL_V1.md
outputs/manifests/A3_ML_V1_LOCK_MANIFEST.json
```

Add tests:

```text
tests/test_a3_ml_direction_asymmetry.py
tests/test_a3_ml_feature_budget.py
tests/test_a3_ml_fold_diagnostics.py
tests/test_a3_ml_horizon_sensitivity.py
```

---

# 3. Direction-asymmetry protocol

## 3.1 Why this is required

V1.1 direction-normalizes signed features:

```text
direction_sign = +1 for LONG
direction_sign = -1 for SHORT
```

This is statistically efficient because long and short examples share coefficients.

It also assumes:

```text
the relationship between an aligned feature and signal quality
is symmetric for LONG and SHORT signals
```

That assumption may be false for XAUUSD because upward trends, downward sell-offs, liquidity, volatility, and reversal speed can differ by direction.

The pooled symmetric model remains the primary model.

Do not train separate long and short models in V1.

---

## 3.2 Required per-direction diagnostics

For every outer walk-forward fold, using untouched outer-test predictions from the selected symmetric model, report separately for LONG and SHORT:

```text
labeled setup groups
positive labels
negative labels
retained signals
retention rate
Brier score
log loss
ROC-AUC
PR-AUC
calibration intercept
calibration slope
mean calibrated probability
observed win rate
PF under P95-stress labels
expectancy per retained trade
expectancy per raw base signal
BAD_SIGNAL share
```

Aggregate across outer folds and report:

```text
LONG minus SHORT Brier
LONG minus SHORT calibration intercept
LONG minus SHORT calibration slope
LONG minus SHORT expectancy per raw base signal
LONG minus SHORT retention
```

Use a 5-active-day moving-block bootstrap for the aggregate differences.

The outer-test diagnostics are reporting only.

They may not retroactively select the model used on that outer fold.

---

## 3.3 Inner-fold asymmetry gate

The direction-interaction model may enter selection for an outer fold only when asymmetry is demonstrated using the outer-training block’s inner OOF predictions.

Required sample adequacy inside the outer-training block:

```text
LONG labeled setup groups >= 100
SHORT labeled setup groups >= 100
LONG minority class >= 30
SHORT minority class >= 30
```

If these conditions are not met:

```text
direction_asymmetry_status = INSUFFICIENT_DATA
interaction candidate is not eligible
```

Asymmetry is demonstrated only when all are true:

```text
1. At least one primary diagnostic exceeds its threshold:

   absolute LONG/SHORT Brier difference >= 0.020
   OR
   absolute calibration-slope difference >= 0.30
   OR
   absolute calibration-intercept difference >= 0.25

2. The sign of the same diagnostic is consistent in at least
   2 of the 3 inner expanding folds.

3. The pooled block-bootstrap 90% confidence interval for that
   diagnostic difference does not include zero.

4. Neither direction has calibration status INVALID.
```

Status values:

```text
SYMMETRY_NOT_REJECTED
ASYMMETRY_DEMONSTRATED
INSUFFICIENT_DATA
INVALID_CALIBRATION
```

---

## 3.4 Pre-registered interaction feature

Exactly one additional feature is conditionally eligible:

```text
h1_slope_direction_interaction
    = direction_sign * h1_ema20_slope_aligned_atr
```

Because:

```text
h1_ema20_slope_aligned_atr
    = direction_sign * raw_h1_slope_atr
```

the interaction allows different H1 slope effects for LONG and SHORT without creating separate models.

It is pre-registered because H1 trend alignment is the strongest existing directional repair hypothesis.

Do not select another interaction after seeing results.

---

## 3.5 Feature-budget treatment

The interaction term counts as one effective feature.

It may be added only when:

```text
ASYMMETRY_DEMONSTRATED
AND
global_feature_budget has one unused slot
```

If the base ordered feature prefix already uses the entire budget:

```text
drop the lowest-priority base feature in the selected prefix
and insert the interaction at that final position
```

Do not exceed the global feature budget.

Example:

```text
global_feature_budget = 10

symmetric model:
  ordered features 1–10

interaction model:
  ordered features 1–9
  + h1_slope_direction_interaction
```

The base feature removed is always the last feature in the ordered prefix.

No performance-based choice of which feature to remove is allowed.

---

## 3.6 Interaction-model selection

Define:

```text
M1_LOGISTIC_L2_SYMMETRIC
M1_LOGISTIC_L2_DIRINT
```

`M1_LOGISTIC_L2_DIRINT` is eligible only when the inner asymmetry gate passes.

Both models use:

```text
same C grid
same inner folds
same calibration procedure
same threshold grid
same retention gate
same deterministic benchmark
```

Selection follows the existing V1.1 rule:

```text
1. Find configurations within one standard error of best Brier.
2. Among those, maximize expectancy per raw base signal at a
   retention-valid threshold.
3. Tie-break toward stronger regularization.
4. If still tied, select the symmetric model.
```

Additional condition for selecting the interaction model:

```text
inner OOF Brier must not worsen
AND
inner OOF expectancy per raw base signal must improve by >= 0.01R
AND
neither direction’s expectancy per raw base signal may decline by > 0.02R
```

The interaction model is not automatically preferred because asymmetry exists.

---

## 3.7 Direction-asymmetry NO-GO conditions

The interaction model is blocked when any applies:

```text
sample adequacy fails
asymmetry is inconsistent across inner folds
bootstrap interval includes zero
interaction exceeds feature budget
interaction harms one direction by >0.02R per raw signal
interaction improves only the training fit
interaction is selected using outer-test results
separate long/short models are proposed
a second interaction term is added
```

---

# 4. Exact feature-budget definition

## 4.1 Timing of the minority count

For each outer fold, apply operations in this order:

```text
1. Create chronological outer-training block.
2. Remove fuzzy setup groups assigned to outer test.
3. Purge event intervals overlapping outer test.
4. Apply the locked embargo.
5. Remove unresolved / non-trainable labels.
6. Reserve the pre-registered chronological calibration tail.
7. Remaining rows form the model-fit segment.
8. Count positive and negative labels in the model-fit segment.
```

Define:

```text
fit_positive_fold
fit_negative_fold
minority_events_fit_fold =
    min(fit_positive_fold, fit_negative_fold)
```

Then:

```text
minority_events_min =
    minimum minority_events_fit_fold across all outer folds
```

This is explicitly:

```text
post fuzzy grouping
post purge
post embargo
post unresolved-label removal
post calibration split
```

Do not calculate the feature budget from the pre-calibration training block.

---

## 4.2 Global budget

```text
global_feature_budget =
    min(16, floor(minority_events_min / 15))
```

Use one global feature prefix across all folds.

Missingness indicators and the conditional direction-interaction term count toward the budget.

If:

```text
global_feature_budget < 5
```

then:

```text
dataset_status = PIPELINE_ONLY
supervised model training = prohibited
```

---

# 5. Per-fold budget and purge diagnostics

`A3_ML_DATA_AUDIT.md` and `A3_ML_SPLIT_MANIFEST.json` must include one row per outer fold:

```text
fold_id
train_start_utc
train_end_utc
test_start_utc
test_end_utc
pre_grouping_rows
exact_unique_signals
fuzzy_setup_groups
outer_train_groups_before_purge
purged_overlap_groups
purge_loss_pct
embargo_excluded_groups
unresolved_label_groups
eligible_outer_train_groups
calibration_groups
calibration_positive
calibration_negative
model_fit_groups
model_fit_positive
model_fit_negative
minority_events_fit_fold
feature_budget_fold
```

Also report:

```text
minority_events_min
global_feature_budget
budget_binding_fold_id
```

`feature_budget_fold` is diagnostic:

```text
min(16, floor(minority_events_fit_fold / 15))
```

The model still uses the global minimum budget.

---

# 6. Earliest-fold starvation policy

The earliest expanding fold may become the binding fold.

This is not automatically a bug.

Codex must report:

```text
which fold binds the budget
how many groups were removed by purging
how many groups were reserved for calibration
how much the 288-active-bar horizon contributes to overlap
```

Do not drop the earliest fold merely to increase the feature count.

Do not add future data to earlier folds.

Do not use a larger feature prefix in later folds.

---

# 7. Holding-horizon sensitivity as a planning diagnostic

The locked primary label remains:

```text
288 active M5 bars
```

During ML-00 only, Codex may produce a sample-mechanics sensitivity table for:

```text
96 active M5 bars
144 active M5 bars
288 active M5 bars — primary
```

The sensitivity may report only:

```text
resolved label count
unresolved label count
median event duration
P95 event duration
purge loss by fold
post-calibration minority count
implied feature budget
```

It must not report:

```text
PF
expectancy
win rate
model score
best threshold
```

This prevents outcome-driven horizon selection.

If the primary 288-bar horizon produces:

```text
global_feature_budget < 5
```

then V1 remains `PIPELINE_ONLY`.

A shorter horizon requires:

```text
a new versioned label contract
a new rationale
a new review
a new SHA256 lock
```

Do not silently shorten V1.

---

# 8. Required tests

## 8.1 Direction asymmetry

```text
test_direction_metrics_are_computed_separately
test_outer_test_does_not_control_same_fold_model_selection
test_asymmetry_gate_requires_inner_oof_predictions
test_asymmetry_gate_sample_minimums
test_asymmetry_gate_fold_consistency
test_interaction_term_exact_formula
test_interaction_counts_against_budget
test_lowest_priority_feature_is_dropped_deterministically
test_symmetric_model_wins_tie
test_second_interaction_is_rejected
```

## 8.2 Feature budget

```text
test_budget_uses_post_calibration_fit_segment
test_purged_rows_do_not_count
test_embargoed_rows_do_not_count
test_unresolved_labels_do_not_count
test_calibration_rows_do_not_count
test_budget_uses_minimum_outer_fold
test_missing_indicator_counts_as_feature
test_interaction_counts_as_feature
test_budget_below_five_blocks_training
test_same_feature_prefix_used_across_folds
```

## 8.3 Diagnostics

```text
test_data_audit_contains_per_fold_purge_counts
test_data_audit_contains_calibration_counts
test_data_audit_names_binding_fold
test_horizon_sensitivity_excludes_outcome_metrics
```

---

# 9. Owner timeline expectation

The ML program is deliberately not a short “train a model this week” task.

Expected sequence:

```text
ML-00 / ML-00A:
  data inventory, label mechanics, slippage, grouping

ML-01:
  contract hash-lock

ML-02–ML-07:
  dataset, splits, deterministic rules, logistic model,
  calibration, thresholding, OOS comparison

ML-13:
  forward checkpoint after >=100 retained trades / >=4 weeks

ML-14:
  forward confirmation after >=300 retained trades / >=12 weeks
  AND adequate MDE/power
```

On one symbol and one signal family:

```text
multi-month evidence accumulation is normal
```

Valid terminal states include:

```text
FAIL
CONTINUE_EVIDENCE
FORWARD_CONFIRMATION_PASS
```

`CONTINUE_EVIDENCE` means:

```text
the implementation is operating correctly
but the sample is still too weak to distinguish edge from noise
```

It is not a project failure and must not trigger threshold relaxation.

No deadline may override:

```text
sample gates
MDE adequacy
confidence bounds
regime coverage
```

---

# 10. Updated ML-00 / ML-00A instructions

## ML-00 — inventory

Codex must produce before training:

```text
exact signal count
fuzzy setup-group count
class balance
direction balance
regime balance
event-duration distribution
per-fold purge estimate
provisional calibration-tail counts
post-calibration minority estimate
provisional feature budget
binding fold
288/144/96 horizon mechanics table
slippage sample adequacy
```

No outcomes may be used to choose the holding horizon.

No model may be trained.

## ML-00A — lock contracts

Add to the lock manifest:

```text
A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md
A3_ML_FEATURE_BUDGET_CONTRACT_V1.md
A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md
```

Verify:

```text
interaction term is exact and singular
minority count is post calibration split
per-fold diagnostic schema is fixed
holding-horizon sensitivity is mechanics-only
```

Then proceed to ML-01.

---

# 11. NO-GO conditions added by this review

```text
Direction asymmetry is ignored.
Separate long/short models are introduced in V1.
Interaction is chosen from outer-test results.
Interaction formula changes after results.
More than one direction interaction is added.
Interaction exceeds the feature budget.
Minority count is measured before calibration carve-out.
Purge or embargo losses are omitted from the audit.
Later folds use more features than early folds.
Earliest fold is removed solely to increase model capacity.
Holding horizon is shortened after viewing PnL.
CONTINUE_EVIDENCE is converted to PASS because of schedule pressure.
```

All prior V1.1 NO-GO conditions remain active.

---

# 12. Final Codex instruction

```text
Do not train yet.

First:
  apply this addendum to the validation and feature-budget contracts;

Second:
  run ML-00 inventory and produce the per-fold budget/purge report;

Third:
  review the resulting post-calibration feature budget;

Fourth:
  hash-lock ML-00A and ML-01 contracts;

Only then:
  build the dataset and train the regularized logistic baseline.
```

---

# 13. Bottom line

The V1.1 architecture is approved.

The remaining changes are narrow:

```text
test the pooled long/short symmetry assumption
and count model capacity from the rows that actually fit coefficients
```

Once those two points are locked, Codex may proceed with ML-00 and ML-01.

A3 remains paused throughout.
