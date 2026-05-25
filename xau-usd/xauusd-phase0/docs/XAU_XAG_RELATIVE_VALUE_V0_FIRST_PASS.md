# XAU/XAG Relative Value v0 First Pass

Status: `REJECTED_FIRST_PASS`

`xau_xag_relative_value_v0` was registered, hash-locked, unblocked with broker-consistent XAGUSD H1 data, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because it failed the multi-cell PF survival gate. Trade count was adequate, so this is an expectancy failure rather than a data-frequency blocker.

## Data Blocker Resolution

Capital.com XAGUSD H1 data was exported read-only from the existing Capital.com MT5 terminal and normalized before the matrix run.

Readiness result:

```text
xau_xag_relative_value_v0 data readiness: PASS
Ready: 3/3 XAGUSD H1 set(s)
```

Acquisition details are recorded in:

```text
docs/XAU_XAG_RELATIVE_VALUE_V0_DATA_ACQUISITION_LOG.md
```

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 102 to 107 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 6.37%, worst return -3.60% | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | 1 month | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 107 | 0.906 | -2.913 | 5.234 | 36.45% |
| 2 | capital_com | median | 107 | 0.906 | -2.913 | 5.234 | 36.45% |
| 3 | capital_com | p95 | 107 | 0.884 | -3.605 | 5.763 | 36.45% |
| 4 | pepperstone | best_case | 102 | 1.106 | 3.004 | 6.351 | 42.16% |
| 5 | pepperstone | median | 102 | 1.106 | 3.004 | 6.351 | 42.16% |
| 6 | pepperstone | p95 | 102 | 1.093 | 2.657 | 6.372 | 42.16% |
| 7 | dukascopy | best_case | 103 | 1.080 | 2.351 | 4.017 | 39.81% |
| 8 | dukascopy | median | 103 | 1.056 | 1.645 | 4.264 | 39.81% |
| 9 | dukascopy | p95 | 103 | 1.010 | 0.286 | 4.931 | 39.81% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `xau_xag_relative_value_v0` in place. Any future precious-metals relative-value revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was a useful failure. The XAU/XAG data contract is now proven end to end across Capital.com, Pepperstone, and Dukascopy, but the locked v0 mechanic did not produce enough edge across brokers or cost models. The active Phase 1 soak and Phase 2 readiness remain unchanged.
