# Fixed-Notional Cost Report

Overall status: PASS
Generated at UTC: 2026-05-22T06:04:29+00:00
Expert: `breakout_retest`
Fixed risk per trade: `$50.00`

## Reporting Boundary

This report is the primary no-compounding review surface. Compounding dollar PnL remains a diagnostic only and is not an operational target.

## Overall

| Cell | Broker | Cost | Trades | Win % | PF | Avg R | Gross R | Cost R | Net R | Cost % | Flag | Fixed PnL | Fixed Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | ALL | ALL | 66759 | 48.22 | 1.3625 | 0.1888 | 0.5115 | 0.3228 | 0.1888 | 63.0938 | ORANGE | 630178.14 | 2270.67 |

## Matrix Cells

| Cell | Broker | Cost | Trades | Win % | PF | Avg R | Gross R | Cost R | Net R | Cost % | Flag | Fixed PnL | Fixed Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | best_case | 7287 | 48.44 | 1.4092 | 0.2107 | 0.3639 | 0.1533 | 0.2107 | 42.1084 | YELLOW | 76766.47 | 1024.18 |
| 2 | capital_com | median | 7287 | 48.44 | 1.4092 | 0.2107 | 0.5172 | 0.3065 | 0.2107 | 59.2624 | YELLOW | 76766.47 | 1024.18 |
| 3 | capital_com | p95 | 7287 | 48.44 | 1.2745 | 0.1454 | 0.7197 | 0.5743 | 0.1454 | 79.7908 | ORANGE | 52993.03 | 1170.56 |
| 4 | pepperstone | best_case | 7174 | 47.11 | 1.3363 | 0.1776 | 0.2829 | 0.1053 | 0.1776 | 37.2187 | GREEN | 63706.24 | 1894.16 |
| 5 | pepperstone | median | 7174 | 47.11 | 1.3363 | 0.1776 | 0.3882 | 0.2106 | 0.1776 | 54.2473 | YELLOW | 63706.24 | 1894.16 |
| 6 | pepperstone | p95 | 7174 | 47.11 | 1.2464 | 0.1326 | 0.5297 | 0.3971 | 0.1326 | 74.9681 | ORANGE | 47559.39 | 2270.67 |
| 7 | dukascopy | best_case | 7792 | 49.32 | 1.4596 | 0.2324 | 0.4503 | 0.2179 | 0.2324 | 48.3863 | YELLOW | 90543.25 | 1142.13 |
| 8 | dukascopy | median | 7792 | 49.32 | 1.4595 | 0.2324 | 0.6681 | 0.4357 | 0.2324 | 65.2168 | ORANGE | 90542.74 | 1142.13 |
| 9 | dukascopy | p95 | 7792 | 48.47 | 1.3312 | 0.1735 | 0.6617 | 0.4882 | 0.1735 | 73.7811 | ORANGE | 67594.32 | 1314.07 |

## Cost Interpretation

- `gross_expectancy_R` is approximated as net R plus explicit modeled cost R.
- `net_expectancy_R` is the existing trade R after modeled execution and commission effects.
- `cost_edge_consumption_pct` compares mean modeled cost R against gross expectancy R.
- Review #2 requires measured-cost replacement before Phase 2 authorization; this report is the assumed-cost baseline.
