# PHASE0 CPCV VALIDATION

Status: PASS
Generated at UTC: 2026-05-21T23:12:32+00:00
Expert: breakout_retest

## Method

Combinatorial purged cross-validation was run on the fixed Phase 0 matrix trade ledgers. No parameters are selected inside this step; the test only checks whether the already-approved mechanical expert remains profitable when chronological fold combinations are held out.

- Folds: 6
- Held-out folds per path: 2
- Purge window around held-out folds: 1.0 day(s)
- Path gate: OOS PF >= 1.0 and OOS trades >= 40
- Aggregate gate: median OOS PF >= 1.1

## Summary

| Status | Paths | Failing Paths | Cells | Failing Cells | Pass Rate | Min OOS PF | Median OOS PF | Min OOS Trades |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PASS | 135 | 0 | 9 | 0 | 100.0% | 1.135 | 1.379 | 2390 |

## Cell Results

| Cell | Broker | Cost | Status | Paths | Failing | Min OOS PF | Median OOS PF | Min OOS Trades |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | best_case | PASS | 15 | 0 | 1.304 | 1.388 | 2428 |
| 2 | capital_com | median | PASS | 15 | 0 | 1.304 | 1.388 | 2428 |
| 3 | capital_com | p95 | PASS | 15 | 0 | 1.195 | 1.246 | 2428 |
| 4 | pepperstone | best_case | PASS | 15 | 0 | 1.178 | 1.306 | 2390 |
| 5 | pepperstone | median | PASS | 15 | 0 | 1.178 | 1.306 | 2390 |
| 6 | pepperstone | p95 | PASS | 15 | 0 | 1.135 | 1.234 | 2390 |
| 7 | dukascopy | best_case | PASS | 15 | 0 | 1.428 | 1.508 | 2596 |
| 8 | dukascopy | median | PASS | 15 | 0 | 1.428 | 1.508 | 2596 |
| 9 | dukascopy | p95 | PASS | 15 | 0 | 1.258 | 1.396 | 2596 |

## Interpretation

A PASS here supports robustness of the fixed breakout_retest definition across purged chronological partitions. It does not replace the five-trading-day Phase 1 soak or the future paper-trading drift monitor.

Path-level rows are written to `outputs/reports/PHASE0_CPCV_PATHS.csv`.
