# H4 VIX Risk-Off Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_vix_risk_off_reversal_v0` was registered, hash-locked, unblocked with public FRED `VIXCLS` data for the CBOE Volatility Index, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only 3 of 9 matrix cells reached PF 1.30, all successful cells were Pepperstone, and concentration failed in every cell.

Hypothesis SHA256: `088a3af6dda5d3dd9369f9c645e72411d2fbb6503fa9de4218007c0c6dea8651`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 47 to 61 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 60 | 0.878 | -1.714 | 4.492 | 45.00% |
| 2 | capital_com | median | 60 | 0.878 | -1.714 | 4.492 | 45.00% |
| 3 | capital_com | p95 | 60 | 0.871 | -1.812 | 4.576 | 43.33% |
| 4 | pepperstone | best_case | 61 | 1.373 | 4.023 | 1.476 | 50.82% |
| 5 | pepperstone | median | 61 | 1.373 | 4.023 | 1.476 | 50.82% |
| 6 | pepperstone | p95 | 61 | 1.360 | 3.900 | 1.493 | 50.82% |
| 7 | dukascopy | best_case | 47 | 1.198 | 1.740 | 2.372 | 48.94% |
| 8 | dukascopy | median | 47 | 1.218 | 1.871 | 2.246 | 48.94% |
| 9 | dukascopy | p95 | 47 | 1.169 | 1.459 | 2.283 | 48.94% |

## Data Source

The local ignored raw file is:

```text
data/raw/risk/FRED_VIXCLS.csv
```

It was fetched from FRED `VIXCLS`, whose source is the Chicago Board Options Exchange and whose release is CBOE Market Statistics.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_vix_risk_off_reversal_v0` in place. Any future equity-risk/VIX attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested a separate cross-asset information class: equity-options implied volatility. It produced enough trades and some Pepperstone strength, but it did not survive cross-broker PF coverage and was too concentrated. The active Phase 1 soak and Phase 2 readiness remain unchanged.
