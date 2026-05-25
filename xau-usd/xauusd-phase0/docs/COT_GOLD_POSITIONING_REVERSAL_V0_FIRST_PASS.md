# COT Gold Positioning Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`cot_gold_positioning_reversal_v0` was registered, hash-locked, unblocked with official CFTC disaggregated futures-only COT data for gold, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30, every cell had fewer than 40 trades, and concentration/activity failed in every cell.

Hypothesis SHA256: `24e5eba2cbc0bc4214cfca556084dd06bc46a6fe19ecf2c9b06965ae746e4c1a`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 5 to 24 trades; failed cells 1-9 | FAIL |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 1-9 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 13 | 0.945 | -0.183 | 2.380 | 38.46% |
| 2 | capital_com | median | 13 | 0.945 | -0.183 | 2.380 | 38.46% |
| 3 | capital_com | p95 | 13 | 0.946 | -0.181 | 2.350 | 38.46% |
| 4 | pepperstone | best_case | 5 | 1.125 | 0.180 | 0.495 | 40.00% |
| 5 | pepperstone | median | 5 | 1.125 | 0.180 | 0.495 | 40.00% |
| 6 | pepperstone | p95 | 5 | 1.112 | 0.162 | 0.500 | 40.00% |
| 7 | dukascopy | best_case | 24 | 0.948 | -0.357 | 2.056 | 37.50% |
| 8 | dukascopy | median | 24 | 0.942 | -0.395 | 2.100 | 37.50% |
| 9 | dukascopy | p95 | 24 | 0.907 | -0.636 | 2.136 | 37.50% |

## Data Source

The local compact reference file is:

```text
data/reference/cot/gold_disaggregated_futures_only_2016_2024.csv
```

It was built from official CFTC historical compressed disaggregated futures-only annual files for GOLD - COMMODITY EXCHANGE INC., CFTC contract market code `088691`.

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `cot_gold_positioning_reversal_v0` in place. Any future COT attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane tested a genuinely different information class: weekly futures-positioning behavior. The result is still not an EA. The signal was too sparse, did not clear PF survival, and failed concentration/activity gates across every broker window. The active Phase 1 soak and Phase 2 readiness remain unchanged.
