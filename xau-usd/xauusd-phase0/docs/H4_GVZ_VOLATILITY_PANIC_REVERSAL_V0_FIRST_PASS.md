# H4 GVZ Volatility Panic Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_gvz_volatility_panic_reversal_v0` was registered, hash-locked, unblocked with public FRED `GVZCLS` data for the CBOE Gold ETF Volatility Index, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30, and concentration/activity failed in every cell.

Hypothesis SHA256: `80dffe0cf5073706de6c9f0af144b239991e96905cd164711f3c5c7d6d55960f`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 48 to 60 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 1-9 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 48 | 0.531 | -5.665 | 6.357 | 33.33% |
| 2 | capital_com | median | 48 | 0.531 | -5.665 | 6.357 | 33.33% |
| 3 | capital_com | p95 | 48 | 0.527 | -5.722 | 6.400 | 33.33% |
| 4 | pepperstone | best_case | 55 | 1.173 | 1.688 | 2.362 | 49.09% |
| 5 | pepperstone | median | 55 | 1.173 | 1.688 | 2.362 | 49.09% |
| 6 | pepperstone | p95 | 55 | 1.180 | 1.742 | 2.381 | 49.09% |
| 7 | dukascopy | best_case | 60 | 1.214 | 2.283 | 1.698 | 48.33% |
| 8 | dukascopy | median | 60 | 1.212 | 2.245 | 1.714 | 46.67% |
| 9 | dukascopy | p95 | 60 | 1.182 | 1.955 | 1.752 | 46.67% |

## Data Source

The local ignored raw file is:

```text
data/raw/options/FRED_GVZCLS.csv
```

It was fetched from FRED `GVZCLS`, whose source is the Chicago Board Options Exchange and whose release is CBOE Market Statistics.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_gvz_volatility_panic_reversal_v0` in place. Any future implied-volatility attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested a genuinely different information class: gold listed-options implied volatility. It produced enough trades and mild positive results in the later broker windows, but the edge did not survive PF coverage, was negative in the Capital.com window, and remained too concentrated/inactive. The active Phase 1 soak and Phase 2 readiness remain unchanged.
