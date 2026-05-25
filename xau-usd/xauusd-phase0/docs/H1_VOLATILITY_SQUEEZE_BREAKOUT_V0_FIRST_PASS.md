# H1 Volatility Squeeze Breakout v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_volatility_squeeze_breakout_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only the three Dukascopy cells reached PF 1.30 and concentration failed in seven cells.

Hypothesis SHA256: `63f6cc75a1b5be46daf2cf936ac65f248981e46b34d3ae3946086f85920f805e`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 116 to 300 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1, 2, 3, 4, 5, 6, and 9 | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 300 | 1.107 | 7.123 | 5.838 | 43.33% |
| 2 | capital_com | median | 300 | 1.107 | 7.123 | 5.838 | 43.33% |
| 3 | capital_com | p95 | 300 | 1.082 | 5.473 | 6.031 | 43.33% |
| 4 | pepperstone | best_case | 293 | 0.748 | -15.929 | 17.799 | 34.13% |
| 5 | pepperstone | median | 293 | 0.748 | -15.929 | 17.799 | 34.13% |
| 6 | pepperstone | p95 | 293 | 0.735 | -16.808 | 18.411 | 34.13% |
| 7 | dukascopy | best_case | 116 | 1.543 | 11.209 | 3.257 | 47.41% |
| 8 | dukascopy | median | 116 | 1.532 | 10.817 | 3.305 | 47.41% |
| 9 | dukascopy | p95 | 116 | 1.439 | 9.052 | 3.432 | 47.41% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_volatility_squeeze_breakout_v0` in place. Any future H1 volatility-compression attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This tested a middle-timeframe volatility-compression behavior independent of levels, retests, and intermarket proxies. The result is informative because it found another Dukascopy-only pocket, but it failed cross-venue survival and cannot become an EA. The active Phase 1 soak and Phase 2 readiness remain unchanged.
