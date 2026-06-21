# A3 ML Direction Asymmetry Protocol V1

Status: PRELOCK_CONTRACT

This contract owns per-direction diagnostics, the asymmetry gate, the one conditional interaction, sample adequacy, and fold-consistency rules.

## Primary Model

The symmetric pooled long/short model is primary.

Do not train separate long and short models in V1.

Direction-normalized features may assume symmetry. This protocol tests that assumption without using outer-test results for same-fold model selection.

## Outer-Test Diagnostics

For every outer fold, report separately for LONG and SHORT using untouched outer-test predictions:

- labeled setup groups;
- positive labels;
- negative labels;
- retained signals;
- retention rate;
- Brier score;
- log loss;
- ROC-AUC;
- PR-AUC;
- calibration intercept;
- calibration slope;
- mean calibrated probability;
- observed win rate;
- PF under P95-stress labels;
- expectancy per retained trade;
- expectancy per raw base signal;
- BAD_SIGNAL share.

Aggregate LONG minus SHORT differences across outer folds:

- Brier;
- calibration intercept;
- calibration slope;
- expectancy per raw base signal;
- retention.

Use a 5-active-day moving-block bootstrap for aggregate differences.

Outer-test diagnostics are reporting only. They may not retroactively select the model used on that outer fold.

## Inner-Fold Asymmetry Gate

The interaction model may enter selection for an outer fold only when asymmetry is demonstrated using the outer-training block's inner OOF predictions.

Sample adequacy inside the outer-training block:

- LONG labeled setup groups >= 100;
- SHORT labeled setup groups >= 100;
- LONG minority class >= 30;
- SHORT minority class >= 30.

If these fail:

```text
direction_asymmetry_status = INSUFFICIENT_DATA
interaction candidate is not eligible
```

Asymmetry is demonstrated only when all are true:

1. At least one diagnostic exceeds its threshold:
   - absolute LONG/SHORT Brier difference >= 0.020;
   - or absolute calibration-slope difference >= 0.30;
   - or absolute calibration-intercept difference >= 0.25.
2. The sign of the same diagnostic is consistent in at least 2 of the 3 inner expanding folds.
3. The pooled block-bootstrap 90 percent confidence interval for that diagnostic difference excludes zero.
4. Neither direction has calibration status INVALID.

Status values:

- SYMMETRY_NOT_REJECTED;
- ASYMMETRY_DEMONSTRATED;
- INSUFFICIENT_DATA;
- INVALID_CALIBRATION.

## Single Conditional Interaction

Exactly one additional feature is conditionally eligible:

```text
h1_slope_direction_interaction =
  direction_sign * h1_ema20_slope_aligned_atr
```

It consumes one feature-budget slot.

If the budget is full, replace only the last feature in the ordered prefix.

Do not add a second interaction or select a different interaction after seeing results.

## Selection Boundary

Define:

- M1_LOGISTIC_L2_SYMMETRIC;
- M1_LOGISTIC_L2_DIRINT.

M1_LOGISTIC_L2_DIRINT is eligible only when the inner asymmetry gate passes.

Both models use the same C grid, inner folds, calibration procedure, threshold grid, retention gate, and deterministic benchmark.

Tie selects the symmetric model.

Final absolute and incremental gates remain unchanged. See A3_ML_MODEL_SELECTION_PROTOCOL_V1.md.

## NO-GO Conditions

Block the interaction model when any applies:

- sample adequacy fails;
- asymmetry is inconsistent across inner folds;
- bootstrap interval includes zero;
- interaction exceeds feature budget;
- interaction harms one direction by more than 0.02R per raw signal;
- interaction improves only training fit;
- interaction is selected using outer-test results;
- separate long/short models are proposed;
- a second interaction term is added.
