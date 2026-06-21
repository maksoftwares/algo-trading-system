# A3 ML Feature Budget Contract V1

Status: PRELOCK_CONTRACT

This contract owns post-calibration event count, global feature budget, per-fold diagnostics, binding-fold behavior, and the holding-horizon governance cross-reference.

## Effective Feature Count

Count transformed model columns, not source-field names.

Each of these consumes one effective feature:

- one numeric model column;
- one missingness indicator;
- the conditional direction interaction.

V1 uses numeric features only. No raw lane, magic, day-of-week, raw session one-hot, or raw level-kind one-hot is allowed.

## Post-Calibration Minority Count

For each outer fold, apply operations in this order:

1. Create chronological outer-training block.
2. Remove fuzzy setup groups assigned to outer test.
3. Purge event intervals overlapping outer test.
4. Apply the locked embargo.
5. Remove unresolved or non-trainable labels.
6. Reserve the pre-registered chronological calibration tail.
7. Remaining rows form the model-fit segment.
8. Count positive and negative labels in the model-fit segment.

Define:

```text
minority_events_fit_fold = min(model_fit_positive, model_fit_negative)
minority_events_min = minimum minority_events_fit_fold across all outer folds
global_feature_budget = min(16, floor(minority_events_min / 15))
```

Do not calculate the feature budget from the pre-calibration training block.

## Training Gate

If global_feature_budget < 5:

```text
dataset_status = PIPELINE_ONLY
supervised model training = prohibited
```

Use one global feature prefix across all folds.

Do not drop the earliest fold solely to increase model capacity.

Do not use a larger feature prefix in later folds.

## Ordered Prefix

Select the first N ordered registry features where N = global_feature_budget.

Do not choose features by full-sample correlation, importance, p-value, or model performance.

## Conditional Direction Interaction

The interaction may be evaluated only when ASYMMETRY_DEMONSTRATED by the direction-asymmetry protocol.

It must not exceed global_feature_budget.

If the selected ordered prefix already has N features, replace feature N with h1_slope_direction_interaction.

The base feature removed is always the last feature in the ordered prefix. No performance-based choice of which feature to remove is allowed.

## Per-Fold Diagnostics

Report one row per outer fold with:

- fold_id;
- train_start_utc;
- train_end_utc;
- test_start_utc;
- test_end_utc;
- pre_grouping_rows;
- exact_unique_signals;
- fuzzy_setup_groups;
- outer_train_groups_before_purge;
- purged_overlap_groups;
- purge_loss_pct;
- embargo_excluded_groups;
- unresolved_label_groups;
- eligible_outer_train_groups;
- calibration_groups;
- calibration_positive;
- calibration_negative;
- model_fit_groups;
- model_fit_positive;
- model_fit_negative;
- minority_events_fit_fold;
- feature_budget_fold.

Also report minority_events_min, global_feature_budget, and budget_binding_fold_id.

## Earliest-Fold Starvation

The earliest expanding fold may become the binding fold. This is not automatically a bug.

Report:

- which fold binds the budget;
- how many groups were removed by purging;
- how many groups were reserved for calibration;
- how much the 288-active-bar horizon contributes to overlap.

## Holding-Horizon Cross-Reference

The holding horizon is fixed by the execution label contract and may not be changed to enlarge global_feature_budget. See Holding-Horizon Change Governance in A3_ML_EXECUTION_LABEL_CONTRACT_V1.md.
