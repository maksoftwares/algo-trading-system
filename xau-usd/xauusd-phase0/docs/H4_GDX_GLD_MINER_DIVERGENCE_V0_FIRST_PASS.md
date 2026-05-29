# H4 GDX/GLD Miner Divergence v0 First Pass

Generated: 2026-05-29
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_gdx_gld_miner_divergence_v0` without tuning. The GDX/GLD miner-divergence reversal idea did not pass the first-pass matrix. It produced too few trades, 0/9 cells reached PF >= 1.30, and concentration/activity gates failed.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Zero months | Single trade % | Top 5 % |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | capital_com | best_case | 10 | 40.00% | 0.7673 | -0.65% | 12 | 100.00% | 100.00% |
| 2 | capital_com | median | 10 | 40.00% | 0.7673 | -0.65% | 12 | 100.00% | 100.00% |
| 3 | capital_com | p95 | 10 | 40.00% | 0.7336 | -0.75% | 12 | 100.00% | 100.00% |
| 4 | pepperstone | best_case | 17 | 52.94% | 1.2877 | 1.04% | 5 | 67.20% | 327.29% |
| 5 | pepperstone | median | 17 | 52.94% | 1.2877 | 1.04% | 5 | 67.20% | 327.29% |
| 6 | pepperstone | p95 | 17 | 52.94% | 1.2769 | 1.01% | 5 | 69.23% | 337.41% |
| 7 | dukascopy | best_case | 28 | 46.43% | 1.0924 | 0.54% | 3 | 136.25% | 656.20% |
| 8 | dukascopy | median | 28 | 46.43% | 1.0879 | 0.52% | 3 | 143.32% | 688.80% |
| 9 | dukascopy | p95 | 28 | 46.43% | 1.0284 | 0.17% | 3 | 434.04% | 2010.00% |

## Gate Snapshot

| Gate | Result |
|---|---|
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 12 |
| Concentration | FAIL |
| Cost sensitivity | Not promoted to deeper review |

## Next Action

Do not tune v0. The broader GDX/GLD data lane was kept open for a separate trend-confirmation hypothesis.
