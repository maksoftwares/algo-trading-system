# H4 Breakeven Inflation Momentum v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_breakeven_inflation_momentum_v0` was registered, hash-locked, unblocked with public FRED `T5YIE` and `T10YIE` data for 5-year and 10-year breakeven inflation rates, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30 and the concentration gate failed in seven cells.

Hypothesis SHA256: `8190930f93431b31b9ec62b71b2c2eb733d4d57ef869e4de0d4150f9fa1c5a36`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 183 to 273 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1, 2, 3, 4, 5, 6, and 9 | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 183 | 0.947 | -2.484 | 8.879 | 40.98% |
| 2 | capital_com | median | 183 | 0.947 | -2.484 | 8.879 | 40.98% |
| 3 | capital_com | p95 | 183 | 0.936 | -3.013 | 9.055 | 40.98% |
| 4 | pepperstone | best_case | 229 | 1.195 | 10.834 | 5.946 | 44.98% |
| 5 | pepperstone | median | 229 | 1.195 | 10.834 | 5.946 | 44.98% |
| 6 | pepperstone | p95 | 229 | 1.193 | 10.670 | 5.818 | 44.98% |
| 7 | dukascopy | best_case | 273 | 1.214 | 14.081 | 5.731 | 43.59% |
| 8 | dukascopy | median | 273 | 1.198 | 13.038 | 5.794 | 43.59% |
| 9 | dukascopy | p95 | 273 | 1.159 | 10.426 | 5.842 | 43.22% |

## Data Source

The local ignored raw files are:

```text
data/raw/inflation_expectations/FRED_T5YIE.csv
data/raw/inflation_expectations/FRED_T10YIE.csv
```

They were fetched from FRED `T5YIE` and `T10YIE`, the 5-year and 10-year breakeven inflation rates.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_breakeven_inflation_momentum_v0` in place. Any future inflation-expectations attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested a separate market-implied inflation-expectations data class after real-yield, COT, GVZ, VIX, and NFCI/ANFCI lanes. It produced ample trades and positive Pepperstone/Dukascopy returns, but the edge did not meet cross-cell PF survival and remained too concentrated. The active Phase 1 soak and Phase 2 readiness remain unchanged.
