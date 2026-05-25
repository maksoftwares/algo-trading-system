# H4 Real Yield Proxy Momentum v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_real_yield_proxy_momentum_v0` was registered, hash-locked, unblocked with public FRED `DFII10` and `DTWEXBGS` macro data, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only the three Dukascopy cells reached PF 1.30, Capital.com and Pepperstone had fewer than 40 trades per cell, and concentration failed in every cell.

Hypothesis SHA256: `0855f404350f5f32fd8e3ba59368344134fa5753b5fcaaf03092062e54c44d6a`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 18 to 64 trades; failed cells 1-6 | FAIL |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 1-6 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 18 | 1.087 | 0.386 | 2.117 | 33.33% |
| 2 | capital_com | median | 18 | 1.087 | 0.386 | 2.117 | 33.33% |
| 3 | capital_com | p95 | 18 | 1.076 | 0.340 | 2.145 | 33.33% |
| 4 | pepperstone | best_case | 20 | 0.958 | -0.230 | 2.351 | 35.00% |
| 5 | pepperstone | median | 20 | 0.958 | -0.230 | 2.351 | 35.00% |
| 6 | pepperstone | p95 | 20 | 0.953 | -0.258 | 2.365 | 35.00% |
| 7 | dukascopy | best_case | 64 | 1.552 | 9.015 | 3.097 | 48.44% |
| 8 | dukascopy | median | 64 | 1.515 | 8.411 | 3.179 | 48.44% |
| 9 | dukascopy | p95 | 64 | 1.477 | 7.775 | 3.202 | 48.44% |

## Data Source

- `data/raw/macro/FRED_DFII10.csv`: FRED 10-year real-yield series.
- `data/raw/macro/FRED_DTWEXBGS.csv`: FRED broad nominal dollar-index series.

The data path fixes the previous missing-macro blocker without substituting XAU-only price behavior for macro inputs.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_real_yield_proxy_momentum_v0` in place. Any future macro-regime attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was the cleanest blocker fix available for the real-yield lane. The result is useful because it shows the macro state can generate a Dukascopy-positive pocket, but it fails the cross-venue, sample-size, concentration, and activity requirements. The active Phase 1 soak and Phase 2 readiness remain unchanged.
