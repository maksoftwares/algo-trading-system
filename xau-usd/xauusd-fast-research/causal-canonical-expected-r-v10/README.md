# Causal Canonical Expected-R V10

This package tests a family-aware expected-return model on the 3,752-row
canonical candidate dataset. It is a research response to two prior failures:
the pooled Step 4 classifier did not rank candidates, and independent family
models were too sparse outside a few specialists.

V10 shares global effects across all nine specialist families while shrinking
family-specific feature deviations toward zero. It predicts stressed net R,
not market direction. Each family uses a calibration-only threshold that
retains the upper 70% of its predicted-return distribution. Sparse calibration
families use the pooled threshold.

The package produces:

- six purged chronological out-of-time evaluations;
- weekly-block bootstrap confidence intervals;
- a final offline research model fitted through 2025 and calibrated on
  January-June 2026;
- a standalone offline parquet scorer; and
- an independent full refit verifier.

Historical outcomes were already exposed before V10 was defined. A historical
pass therefore requires prospective confirmation and does not authorize ML
shadowing, MT5 attachment, demo/live filtering, sizing, or broker action.

