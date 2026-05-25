# Gold FX Proxy Divergence v0 First Pass

Status: `REJECTED_FIRST_PASS`

`gold_fx_proxy_divergence_v0` was registered, hash-locked, smoke-tested, unblocked with broker-consistent proxy data, and run through the real 9-cell research matrix without tuning. It is rejected because it failed the multi-cell PF survival gate. Trade count was adequate, so this is an expectancy failure rather than a data-frequency blocker.

## Data Blocker Resolution

The missing Pepperstone and Dukascopy EURUSD/USDJPY H1 proxy data was acquired and normalized before the matrix run.

Readiness result:

```text
gold_fx_proxy_divergence_v0 data readiness: PASS
Ready: 6/6 proxy H1 set(s)
```

Acquisition details are recorded in:

```text
docs/GOLD_FX_PROXY_DIVERGENCE_V0_DATA_ACQUISITION_LOG.md
```

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 99 to 132 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 10.88%, worst return -6.07% | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months <= 3 | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 99 | 0.816 | -5.411 | 10.660 | 39.39% |
| 2 | capital_com | median | 99 | 0.816 | -5.411 | 10.660 | 39.39% |
| 3 | capital_com | p95 | 99 | 0.794 | -6.074 | 10.877 | 39.39% |
| 4 | pepperstone | best_case | 117 | 0.859 | -4.792 | 8.912 | 41.03% |
| 5 | pepperstone | median | 117 | 0.859 | -4.792 | 8.912 | 41.03% |
| 6 | pepperstone | p95 | 117 | 0.846 | -5.232 | 9.237 | 41.03% |
| 7 | dukascopy | best_case | 132 | 1.088 | 3.008 | 6.214 | 42.42% |
| 8 | dukascopy | median | 132 | 1.053 | 1.808 | 6.595 | 42.42% |
| 9 | dukascopy | p95 | 132 | 0.984 | -0.556 | 7.305 | 42.42% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `gold_fx_proxy_divergence_v0` in place. Any future intermarket revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was a useful failure. The intermarket data contract is now proven end to end, but the locked v0 mechanic did not survive cross-broker expectancy gates. The active Phase 1 soak and Phase 2 readiness remain unchanged.
