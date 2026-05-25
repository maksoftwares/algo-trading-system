# XAU XAG FX Composite Reversion v0 First Pass

Status: `REJECTED_FIRST_PASS`

`xau_xag_fx_composite_reversion_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30.

Hypothesis SHA256: `66210e64a50f9a9fae5e691e603f0c3551c1afc8ada4771bd4ea142016e020`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 506 to 547 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed all cells | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 506 | 1.022 | 3.105 | 13.651 | 41.11% |
| 2 | capital_com | median | 506 | 1.022 | 3.105 | 13.651 | 41.11% |
| 3 | capital_com | p95 | 506 | 0.994 | -0.804 | 13.860 | 41.11% |
| 4 | pepperstone | best_case | 515 | 0.917 | -11.531 | 18.258 | 37.48% |
| 5 | pepperstone | median | 515 | 0.917 | -11.531 | 18.258 | 37.48% |
| 6 | pepperstone | p95 | 515 | 0.902 | -13.400 | 19.536 | 37.48% |
| 7 | dukascopy | best_case | 547 | 0.933 | -10.138 | 13.788 | 38.57% |
| 8 | dukascopy | median | 547 | 0.903 | -14.315 | 16.145 | 38.57% |
| 9 | dukascopy | p95 | 547 | 0.839 | -22.522 | 23.527 | 38.39% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `xau_xag_fx_composite_reversion_v0` in place. Any future intermarket composite attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This cleared the intermarket-data path by combining broker-consistent XAGUSD, EURUSD, and USDJPY proxies, but the composite did not improve over the already rejected single-proxy intermarket lanes. The active Phase 1 soak and Phase 2 readiness remain unchanged.
