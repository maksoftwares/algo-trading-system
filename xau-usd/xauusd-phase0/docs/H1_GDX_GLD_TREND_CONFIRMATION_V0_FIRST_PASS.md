# H1 GDX/GLD Trend Confirmation v0 First Pass

Generated: 2026-05-29
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_gdx_gld_trend_confirmation_v0` without tuning. It generated enough trades in all matrix cells, but no cell reached PF >= 1.30. Dukascopy was modestly positive, while Capital.com and Pepperstone were clearly negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Zero months | Single trade % | Top 5 % |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | capital_com | best_case | 78 | 35.90% | 0.7125 | -6.49% | 2 | 100.00% | 100.00% |
| 2 | capital_com | median | 78 | 35.90% | 0.7125 | -6.49% | 2 | 100.00% | 100.00% |
| 3 | capital_com | p95 | 78 | 35.90% | 0.6975 | -6.84% | 2 | 100.00% | 100.00% |
| 4 | pepperstone | best_case | 84 | 34.52% | 0.7974 | -4.66% | 2 | 100.00% | 100.00% |
| 5 | pepperstone | median | 84 | 34.52% | 0.7974 | -4.66% | 2 | 100.00% | 100.00% |
| 6 | pepperstone | p95 | 84 | 34.52% | 0.7899 | -4.83% | 2 | 100.00% | 100.00% |
| 7 | dukascopy | best_case | 81 | 45.68% | 1.1051 | 1.99% | 2 | 37.46% | 181.79% |
| 8 | dukascopy | median | 81 | 45.68% | 1.0858 | 1.61% | 2 | 45.87% | 221.16% |
| 9 | dukascopy | p95 | 81 | 44.44% | 1.0164 | 0.31% | 2 | 220.27% | 1090.06% |

## Gate Snapshot

| Gate | Result |
|---|---|
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | PASS, max 2 |
| Concentration | FAIL |
| Cost sensitivity | Not promoted to deeper review |

## Next Action

Do not tune v0. The candidate is useful evidence that the GDX/GLD trend-confirmation lane does not produce a buildable independent EA under the locked first-pass thresholds.
