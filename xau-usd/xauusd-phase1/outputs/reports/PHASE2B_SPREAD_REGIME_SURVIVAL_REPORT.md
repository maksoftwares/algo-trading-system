# Phase 2B Spread-Regime Survival Report

Overall status: REVIEW_READY_LOW_SAMPLE

Spread regimes are measured from passive rows only and cannot authorize Phase 2 execution.

Passive log: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\paper_observer\passive_cost_observer_log.csv`

## Buckets

| Bucket | Rows | Median cost_R | Median net edge_R | Median stop points | Median spread points | Gate counts |
| --- | --- | --- | --- | --- | --- | --- |
| spread_lte_50 | 227 | 0.1420 | 0.3696 | 278.5900 | 50.0000 | COST_BLOCK=50, COST_OK_ACCEPTABLE=25, COST_OK_STRONG=116, COST_WARN=36 |
| spread_50_to_75 | 42 | 0.1218 | 0.3897 | 616.0900 | 75.0000 | COST_BLOCK=4, COST_OK_ACCEPTABLE=3, COST_OK_STRONG=30, COST_WARN=5 |

## Boundary

This report is passive-observer research evidence only. It cannot make a cost-suspended family execution-eligible.
