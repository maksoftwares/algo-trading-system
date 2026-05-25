# H4 Credit Spread Stress Momentum v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_credit_spread_stress_momentum_v0` was registered, hash-locked, unblocked with public FRED `BAA10Y` and `AAA10Y` data for Moody's corporate credit spreads versus the 10-year Treasury, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30, concentration failed in every cell, and activity failed in six cells.

Hypothesis SHA256: `b006f6f309374f1f11f20b39cacca8a87ab18e5d8001c99426d60d22103df7c6`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 153 to 211 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 4-9 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 199 | 0.894 | -5.750 | 13.478 | 38.19% |
| 2 | capital_com | median | 199 | 0.894 | -5.750 | 13.478 | 38.19% |
| 3 | capital_com | p95 | 199 | 0.883 | -6.349 | 13.700 | 38.19% |
| 4 | pepperstone | best_case | 153 | 1.060 | 2.158 | 7.043 | 42.48% |
| 5 | pepperstone | median | 153 | 1.060 | 2.158 | 7.043 | 42.48% |
| 6 | pepperstone | p95 | 153 | 1.046 | 1.665 | 7.151 | 42.48% |
| 7 | dukascopy | best_case | 211 | 0.901 | -5.217 | 8.169 | 36.49% |
| 8 | dukascopy | median | 211 | 0.895 | -5.482 | 8.325 | 36.49% |
| 9 | dukascopy | p95 | 211 | 0.867 | -6.954 | 9.141 | 36.02% |

## Data Source

The local ignored raw files are:

```text
data/raw/credit_spread/FRED_BAA10Y.csv
data/raw/credit_spread/FRED_AAA10Y.csv
```

They were fetched from FRED `BAA10Y` and `AAA10Y`.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_credit_spread_stress_momentum_v0` in place. Any future credit-spread attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested corporate credit stress separately from VIX, financial conditions, Treasury curve stress, and inflation/rate inputs. It produced enough trades, but no cross-broker PF edge and too much concentration/inactivity. The active Phase 1 soak and Phase 2 readiness remain unchanged.
