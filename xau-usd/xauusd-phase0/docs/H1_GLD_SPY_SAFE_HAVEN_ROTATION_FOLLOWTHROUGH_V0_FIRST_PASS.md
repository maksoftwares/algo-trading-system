# H1 GLD/SPY Safe-Haven Rotation Followthrough v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_gld_spy_safe_haven_rotation_followthrough_v0` without tuning.

This candidate produced enough trades in all 9 cells and kept max zero-trade months low, but its expectancy was too thin. No matrix cell reached PF >= 1.30, and Dukascopy P95 became negative after costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 196 | 45.92% | 1.1445 | +7.42% | 5.49% | 1 | FAIL |
| 2 | capital_com | median | 196 | 45.92% | 1.1445 | +7.42% | 5.49% | 1 | FAIL |
| 3 | capital_com | p95 | 196 | 45.92% | 1.1128 | +5.81% | 5.70% | 1 | FAIL |
| 4 | pepperstone | best_case | 161 | 42.86% | 1.1077 | +4.71% | 8.64% | 1 | FAIL |
| 5 | pepperstone | median | 161 | 42.86% | 1.1077 | +4.71% | 8.64% | 1 | FAIL |
| 6 | pepperstone | p95 | 161 | 42.86% | 1.0813 | +3.57% | 8.83% | 1 | FAIL |
| 7 | dukascopy | best_case | 175 | 43.43% | 1.0636 | +2.74% | 5.95% | 1 | FAIL |
| 8 | dukascopy | median | 175 | 43.43% | 1.0278 | +1.20% | 7.03% | 1 | FAIL |
| 9 | dukascopy | p95 | 175 | 42.86% | 0.9672 | -1.40% | 8.71% | 1 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1,596 | Informational | PASS |
| Max zero-trade months | 1 | <= 3 | PASS |
| Cost sensitivity | P95 cost pushed Dukascopy below PF 1.0 | P95 should not break the edge | FAIL |
| Cross-broker persistence | All cells below threshold | Robust across windows | FAIL |

## Interpretation

The GLD/SPY safe-haven relative-strength idea appears directionally sensible but not buildable. It produces broad activity and mostly positive returns, but the edge is too thin after costs and does not approach the required PF threshold.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a different mechanism or with a higher-quality gold-specific data source.
