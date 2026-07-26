# Action V3 F2026 Drift Audit Preregistration

This audit asks why the fixed Action V3 policies failed during F2026. It does
not train a model, search a threshold, alter a candidate mechanic, or authorize
runtime use. The aggregate F2026 outcomes are already exposed. The diagnostic
definitions below are frozen before the row-level drift analysis is run.

## Comparison

For each disjoint lane, replay its already chosen F2026 model and threshold on:

1. `REFERENCE`: F2026 calibration, 2024-07-01 through 2025-07-01;
2. `CURRENT`: F2026 test, 2025-07-01 through 2026-07-01.

Only causally available resolved actions are scored. `UNSAFE_SHOCK` remains
excluded. Structural weights preserve one unit of evidence per 30-minute
episode. Each event keeps the highest-scored action using the original locked
action tie order.

## Outcome-Blind Drift

The 58 locked model features are compared with weighted standardized mean
difference, population stability index, and IQR-normalized Wasserstein
distance. Reference weighted deciles define PSI bins. Feature drift is severe
at absolute SMD >= 0.50 or PSI >= 0.25, and moderate at absolute SMD >= 0.25
or PSI >= 0.10.

Regime, fixed UTC session, direction, available-action pattern, and chosen
action are compared with weighted total variation, Jensen-Shannon divergence,
and categorical PSI. Total variation >= 0.20 or PSI >= 0.25 is severe.

Model-score drift, threshold coverage, action choice, and score-decile
occupancy are measured before outcomes are used.

## Explanatory Outcome Diagnostics

After outcome-blind drift is measured, the audit compares stressed R, win
rate, profit factor, MFE, MAE, and weighted AUC. It reports monthly behavior,
fixed-action economics, and selected-event economics by regime, session,
direction, availability, and chosen action.

For every categorical dimension, the selected-mean-R change is decomposed as:

`composition = sum((p_current - p_reference) * mean_reference)`

`within = sum(p_current * (mean_current - mean_reference))`

Missing-period categories use their observed-period mean for both periods, so
their change is assigned to composition and the identity remains exact.

## Fixed Failure Flags

- coverage drift: absolute selected-fraction change >= 0.15;
- ranking collapse: current AUC < 0.50 and AUC drop >= 0.05;
- outcome collapse: selected mean R falls by at least 0.15R and selected win
  rate falls by at least 0.08, or reference mean is positive and current mean
  is negative;
- within-stratum deterioration: decomposition within effect <= -0.10R;
- absent base edge: selected mean R is nonpositive in both periods;
- broad covariate drift: at least five severe model features, or severe regime
  or session drift.

These flags diagnose failure. They are not acceptance gates for V4 and cannot
be used to optimize V3 retrospectively.

## Authorization

All outputs remain research-only. No model, threshold, MT5 terminal, EA,
shadow process, demo/live setting, account, position, or risk limit may change.
F2026 remains exposed development history after this audit.
