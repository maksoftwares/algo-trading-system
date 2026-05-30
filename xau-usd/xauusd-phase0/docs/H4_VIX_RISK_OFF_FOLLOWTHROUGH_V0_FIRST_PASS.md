# H4 VIX Risk-Off Followthrough v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_vix_risk_off_followthrough_v0` without tuning.

This candidate produced enough trades in all 9 cells, but the edge did not survive cross-broker validation. Capital.com was mildly positive below the PF threshold, while Pepperstone and Dukascopy were negative after costs. No matrix cell reached PF >= 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 159 | 47.17% | 1.1757 | +6.29% | 2.69% | 0 | FAIL |
| 2 | capital_com | median | 159 | 47.17% | 1.1757 | +6.29% | 2.69% | 0 | FAIL |
| 3 | capital_com | p95 | 159 | 47.17% | 1.1613 | +5.78% | 2.75% | 0 | FAIL |
| 4 | pepperstone | best_case | 149 | 35.57% | 0.7065 | -10.52% | 12.93% | 1 | FAIL |
| 5 | pepperstone | median | 149 | 35.57% | 0.7065 | -10.52% | 12.93% | 1 | FAIL |
| 6 | pepperstone | p95 | 149 | 35.57% | 0.7020 | -10.68% | 13.03% | 1 | FAIL |
| 7 | dukascopy | best_case | 160 | 36.88% | 0.8797 | -4.58% | 8.70% | 0 | FAIL |
| 8 | dukascopy | median | 160 | 36.88% | 0.8717 | -4.87% | 8.81% | 0 | FAIL |
| 9 | dukascopy | p95 | 160 | 36.88% | 0.8496 | -5.73% | 9.27% | 0 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1,404 | Informational | PASS |
| Max zero-trade months | 1 | <= 3 | PASS |
| Cross-broker persistence | Capital.com positive below threshold; Pepperstone/Dukascopy negative | Robust across windows | FAIL |
| Cost sensitivity | P95 cost slightly worsened already weak cells | P95 should not break the edge | FAIL |

## Interpretation

The opposite expression of the rejected VIX reversal idea also fails. Shifted VIX stress can create activity, but it does not produce a robust XAUUSD H4 continuation edge across the broker/time windows. The result argues against revisiting plain VIX-only risk-off mechanics without a materially better signal source or a distinct mechanism.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a different mechanism or with higher-quality primary market data.
