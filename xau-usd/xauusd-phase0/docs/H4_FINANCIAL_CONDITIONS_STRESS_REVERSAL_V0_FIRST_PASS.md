# H4 Financial Conditions Stress Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_financial_conditions_stress_reversal_v0` was registered, hash-locked, unblocked with public FRED `NFCI` and `ANFCI` data for Chicago Fed financial conditions, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30, every broker window was negative, and concentration/activity failed in every cell.

Hypothesis SHA256: `014e7abb9dcd9ddc77f48f848f40f43a7d9ac39558e2502d2a41ac5ed7483ea3`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 46 to 61 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 1-9 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 46 | 0.845 | -1.732 | 5.139 | 45.65% |
| 2 | capital_com | median | 46 | 0.845 | -1.732 | 5.139 | 45.65% |
| 3 | capital_com | p95 | 46 | 0.840 | -1.791 | 5.154 | 45.65% |
| 4 | pepperstone | best_case | 54 | 0.963 | -0.391 | 3.303 | 44.44% |
| 5 | pepperstone | median | 54 | 0.963 | -0.391 | 3.303 | 44.44% |
| 6 | pepperstone | p95 | 54 | 0.954 | -0.492 | 3.326 | 44.44% |
| 7 | dukascopy | best_case | 61 | 0.864 | -1.833 | 3.593 | 36.07% |
| 8 | dukascopy | median | 61 | 0.837 | -2.200 | 3.765 | 36.07% |
| 9 | dukascopy | p95 | 61 | 0.797 | -2.748 | 3.914 | 34.43% |

## Data Source

The local ignored raw files are:

```text
data/raw/financial_conditions/FRED_NFCI.csv
data/raw/financial_conditions/FRED_ANFCI.csv
```

They were fetched from FRED `NFCI` and `ANFCI`, the Chicago Fed National Financial Conditions Index and adjusted index.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_financial_conditions_stress_reversal_v0` in place. Any future financial-conditions attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested a broad weekly financial-conditions data class. It produced enough trades, but the signal had no cross-broker edge and was too concentrated/inactive. The active Phase 1 soak and Phase 2 readiness remain unchanged.
