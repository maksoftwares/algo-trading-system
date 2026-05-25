# H4 Treasury Curve Stress Momentum v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_treasury_curve_stress_momentum_v0` was registered, hash-locked, unblocked with public FRED `DGS2`, `DGS10`, and `T10Y2Y` data for nominal Treasury yields and the 10-year minus 2-year curve spread, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only 3 of 9 cells reached PF 1.30, all passing cells were Pepperstone-only, concentration failed in every cell, and activity failed in six cells.

Hypothesis SHA256: `b9753121ef8f4524362af59f499d4c5f7f7fc22bc20b3971be98481c2eddbc60`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 55 to 207 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 1-6 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 63 | 0.986 | -0.227 | 6.495 | 39.68% |
| 2 | capital_com | median | 63 | 0.986 | -0.227 | 6.495 | 39.68% |
| 3 | capital_com | p95 | 63 | 0.969 | -0.522 | 6.527 | 39.68% |
| 4 | pepperstone | best_case | 55 | 1.536 | 6.036 | 1.809 | 50.91% |
| 5 | pepperstone | median | 55 | 1.536 | 6.036 | 1.809 | 50.91% |
| 6 | pepperstone | p95 | 55 | 1.537 | 6.028 | 1.818 | 50.91% |
| 7 | dukascopy | best_case | 207 | 1.064 | 3.391 | 8.936 | 41.06% |
| 8 | dukascopy | median | 207 | 1.058 | 3.040 | 8.976 | 41.06% |
| 9 | dukascopy | p95 | 207 | 1.025 | 1.330 | 9.431 | 40.58% |

## Data Source

The local ignored raw files are:

```text
data/raw/treasury_curve/FRED_DGS2.csv
data/raw/treasury_curve/FRED_DGS10.csv
data/raw/treasury_curve/FRED_T10Y2Y.csv
```

They were fetched from FRED `DGS2`, `DGS10`, and `T10Y2Y`.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_treasury_curve_stress_momentum_v0` in place. Any future Treasury-rate or curve-shape attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested nominal-rate and curve-shape stress separately from real yields, breakevens, and broad financial conditions. The result showed isolated Pepperstone strength, but it failed cross-venue survival and was too concentrated/inactive. The active Phase 1 soak and Phase 2 readiness remain unchanged.
