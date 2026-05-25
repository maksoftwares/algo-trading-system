# H4 Macro Composite Risk State v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_macro_composite_risk_state_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only 6 of 9 cells reached PF 1.30, Capital.com cells missed the 40-trade sample-size gate, concentration failed in every cell, and activity failed in every cell.

Hypothesis SHA256: `896dbb38f73e803a2033ff7d321f401fa0d7f240d779328f3eeccadcbf1545a7`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 6 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | Failed cells 1-3 with 34 trades | FAIL |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 1-9 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 34 | 1.103 | 0.849 | 2.185 | 44.12% |
| 2 | capital_com | median | 34 | 1.103 | 0.849 | 2.185 | 44.12% |
| 3 | capital_com | p95 | 34 | 1.081 | 0.674 | 2.204 | 44.12% |
| 4 | pepperstone | best_case | 40 | 1.461 | 4.019 | 1.557 | 45.00% |
| 5 | pepperstone | median | 40 | 1.461 | 4.019 | 1.557 | 45.00% |
| 6 | pepperstone | p95 | 40 | 1.446 | 3.904 | 1.564 | 45.00% |
| 7 | dukascopy | best_case | 98 | 1.362 | 7.918 | 2.827 | 46.94% |
| 8 | dukascopy | median | 98 | 1.330 | 7.276 | 2.945 | 46.94% |
| 9 | dukascopy | p95 | 98 | 1.307 | 6.779 | 3.045 | 46.94% |

## Data Source

This candidate used already-acquired ignored public FRED raw files for `DFII10`, `DTWEXBGS`, `T5YIE`, `T10YIE`, `DGS2`, `DGS10`, `T10Y2Y`, `BAA10Y`, `AAA10Y`, `VIXCLS`, `GVZCLS`, `NFCI`, and `ANFCI`.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_macro_composite_risk_state_v0` in place. Any future macro-composite attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This is the first independent macro lane with material cross-cell signal evidence: six cells reached PF >= 1.30 and all cells were positive. It is still not a new EA because sample size, concentration, activity, and the 7-of-9 survival gate failed. The active Phase 1 soak and Phase 2 readiness remain unchanged.
