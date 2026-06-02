# XAUUSD Phase 0R Separate EA Research Lane

This directory is an isolated research lane for new XAUUSD candidate ideas. It is separate from the current canonical Phase 0 and Phase 1/2 EA logic.

Current status:

- The candidates are draft research hypotheses.
- The candidates are not current canonical EAs.
- The candidates are not execution-authorized.
- The candidates do not modify accepted or rejected experts in the existing Phase 0 package.
- The matching MT5 files are dry-run/passive-observer only.
- No candidate may be considered for future paper mode until it passes every Phase 0R promotion gate.

## Candidates

| candidate_id | status | family | same_family_as_breakout_retest | expected_median_stop_points |
| --- | --- | --- | --- | ---: |
| d1_compression_h4_expansion_v0 | DRAFT | volatility expansion / compression-release | false | 500 |
| h4_trend_pullback_d1_bias_v0 | DRAFT | trend continuation / pullback | false | 375 |
| weekly_level_h4_rejection_v0 | DRAFT | higher-timeframe rejection / mean reversion | false | 425 |

## Commands

From this directory after installing the package, or with `PYTHONPATH=src`:

```powershell
phase0r validate-hypotheses-complete
phase0r hash-hypotheses --register
phase0r run-cost-feasibility --candidate all
phase0r run-matrix --candidate d1_compression_h4_expansion_v0
phase0r run-deciles --candidate d1_compression_h4_expansion_v0
phase0r run-measured-cost-revalidation --candidate d1_compression_h4_expansion_v0
phase0r create-adversarial-packet --candidate d1_compression_h4_expansion_v0
phase0r generate-verdict --candidate all
```

Result-producing commands intentionally block while the hypothesis status is `DRAFT`.
