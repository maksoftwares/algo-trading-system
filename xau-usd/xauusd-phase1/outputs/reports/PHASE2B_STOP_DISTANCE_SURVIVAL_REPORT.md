# Phase 2B Stop-Distance Survival Report

Overall status: REVIEW_READY_LOW_SAMPLE

Wider stop-distance buckets should reduce cost_R pressure. This report is passive evidence only.

Passive log: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\paper_observer\passive_cost_observer_log.csv`

## Buckets

| Bucket | Rows | Median cost_R | Median net edge_R | Median stop points | Median spread points | Gate counts |
| --- | --- | --- | --- | --- | --- | --- |
| 0_to_249 | 115 | 0.2858 | 0.2258 | 31.0100 | 7.0000 | COST_BLOCK=54, COST_OK_ACCEPTABLE=15, COST_OK_STRONG=10, COST_WARN=36 |
| 250_to_499 | 48 | 0.1348 | 0.3768 | 380.4700 | 50.0000 | COST_OK_ACCEPTABLE=13, COST_OK_STRONG=30, COST_WARN=5 |
| 500_to_749 | 49 | 0.0958 | 0.4158 | 557.0000 | 50.0000 | COST_OK_STRONG=49 |
| 750_plus | 57 | 0.0601 | 0.4515 | 940.7800 | 50.0000 | COST_OK_STRONG=57 |

## Boundary

This report is passive-observer research evidence only. It cannot make a cost-suspended family execution-eligible.
