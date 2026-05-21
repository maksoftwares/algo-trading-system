# PHASE0 REALITY CHECK

Status: PASS
Generated at UTC: 2026-05-21T23:15:11+00:00
Approved expert under test: breakout_retest

## Method

This report applies a White Reality Check and SPA-style pairwise bootstrap to monthly trade-ledger returns for the Phase 0 expert family. Each expert's monthly value is the average monthly PnL across its matrix trade ledgers, which keeps cost/broker cells from turning into separate optimized candidates.

- Bootstrap iterations: 5000
- Circular block length: 3 month(s)
- Maximum accepted p-value: 0.1
- Months in panel: 108

## White Reality Check

| Winner | White p | q90 | q95 | q99 |
| --- | --- | --- | --- | --- |
| breakout_retest | 0.0200 | 120986.58 | 160688.48 | 250328.73 |

## Expert Means

| Expert | Mean Monthly PnL | Total PnL | Role |
| --- | --- | --- | --- |
| breakout_retest | 209752.17 | 22653234.48 | approved |
| range_mr | -1.86 | -200.75 | alternative |
| trend_pullback | -51.37 | -5547.92 | alternative |

## SPA-Style Pairwise Checks

| Alternative | Status | Mean Edge | SPA p | Bootstrap q95 |
| --- | --- | --- | --- | --- |
| range_mr | PASS | 209754.03 | 0.0234 | 166857.40 |
| trend_pullback | PASS | 209803.54 | 0.0208 | 166361.63 |

## Interpretation

A PASS means breakout_retest remains the family winner after a block-bootstrap adjustment for multiple tested expert candidates. This is statistical support only; it does not remove the need for Phase 1 soak completion, Phase 2 paper trading, or live drift monitoring.

Summary rows are written to `outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv`.
