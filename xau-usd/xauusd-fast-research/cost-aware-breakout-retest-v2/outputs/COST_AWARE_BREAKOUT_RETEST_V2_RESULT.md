# XAUUSD Cost-Aware Breakout-Retest V2 Result

Decision: **REJECTED_COST_AWARE_BREAKOUT_RETEST_V2**

V1 remains cost-suspended. This V2 result is research-only and receives no diversification credit.

| Stage | Eligible | Trades | Trades/day | Stress PF | Avg stress R | Drawdown R | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| train | True | 160 | 0.129 | 0.698 | -0.210 | 36.072 | FAIL |
| validation | False | 290 | 0.467 | 0.576 | -0.324 | 95.334 | INELIGIBLE |
| internal_test | False | 235 | 0.379 | 0.729 | -0.188 | 57.723 | INELIGIBLE |
| exam | False | 1581 | 2.534 | 0.740 | -0.182 | 296.693 | INELIGIBLE |
| recent_tail | False | 1127 | 3.612 | 0.766 | -0.161 | 189.061 | INELIGIBLE |

## Interpretation

The fixed cost-aware event failed the chronological firewall. V2 is closed without tuning.

A pass would still require exact-tick parity and prospective shadow observation before any execution discussion.
