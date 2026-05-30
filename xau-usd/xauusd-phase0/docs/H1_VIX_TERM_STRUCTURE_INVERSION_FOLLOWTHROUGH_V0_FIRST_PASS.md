# H1 VIX Term-Structure Inversion Followthrough v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_vix_term_structure_inversion_followthrough_v0` without tuning.

This candidate produced enough trades in all 9 cells, but no cell reached PF >= 1.30. The best cell was only PF 1.0207, and Pepperstone was materially negative across all cost cases. The result rejects the paired followthrough reading of the same shifted VIX/VXV inversion feature that also failed in reversal form.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 110 | 42.73% | 0.9823 | -0.52% | 5.68% | 1 | FAIL |
| 2 | capital_com | median | 110 | 42.73% | 0.9823 | -0.52% | 5.68% | 1 | FAIL |
| 3 | capital_com | p95 | 110 | 42.73% | 0.9550 | -1.33% | 5.87% | 1 | FAIL |
| 4 | pepperstone | best_case | 103 | 33.98% | 0.7332 | -7.90% | 10.95% | 1 | FAIL |
| 5 | pepperstone | median | 103 | 33.98% | 0.7332 | -7.90% | 10.95% | 1 | FAIL |
| 6 | pepperstone | p95 | 103 | 33.98% | 0.7191 | -8.36% | 11.27% | 1 | FAIL |
| 7 | dukascopy | best_case | 86 | 39.53% | 1.0207 | +0.46% | 4.94% | 2 | FAIL |
| 8 | dukascopy | median | 86 | 39.53% | 0.9806 | -0.43% | 5.32% | 2 | FAIL |
| 9 | dukascopy | p95 | 86 | 39.53% | 0.9236 | -1.70% | 5.87% | 2 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 897 | Informational | PASS |
| Max zero-trade months | 2 | <= 3 | PASS |
| Cross-broker persistence | Capital.com/Dukascopy near flat, Pepperstone negative | Robust across windows | FAIL |
| Best observed PF | 1.0207 | >= 1.30 in most cells | FAIL |

## Interpretation

The VIX/VXV inversion feature has now been tested in both H1 reversal and H1 followthrough forms. Neither expression produced a persistent edge after costs. The followthrough version solved sample size and activity but did not produce meaningful PF strength.

## Next Action

Do not tune this v0 candidate. Treat this as another rejected independent volatility-term-structure lane. Future volatility research should require a genuinely new data source or feature family, such as gold options skew, intraday futures/order-flow, or realized/implied volatility spread data.
