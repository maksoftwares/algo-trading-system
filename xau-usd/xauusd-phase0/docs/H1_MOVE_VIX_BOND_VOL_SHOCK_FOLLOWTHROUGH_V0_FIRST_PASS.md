# H1 MOVE/VIX Bond-Vol Shock Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_move_vix_bond_vol_shock_followthrough_v0` without tuning.

This candidate tested whether shifted MOVE/VIX bond-volatility stress supports H1 XAUUSD directional follow-through after local XAU has already moved in the same direction. It failed PF persistence, trade-count coverage, and activity.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 32 | 43.75% | 1.0439 | +0.36% | 3.64% | 8 | FAIL |
| 2 | capital_com | median | 32 | 43.75% | 1.0439 | +0.36% | 3.64% | 8 | FAIL |
| 3 | capital_com | p95 | 32 | 43.75% | 1.0196 | +0.16% | 3.68% | 8 | FAIL |
| 4 | pepperstone | best_case | 122 | 38.52% | 0.9314 | -2.41% | 8.60% | 11 | FAIL |
| 5 | pepperstone | median | 122 | 38.52% | 0.9314 | -2.41% | 8.60% | 11 | FAIL |
| 6 | pepperstone | p95 | 122 | 38.52% | 0.9130 | -3.07% | 8.80% | 11 | FAIL |
| 7 | dukascopy | best_case | 133 | 31.58% | 0.6140 | -14.52% | 14.54% | 5 | FAIL |
| 8 | dukascopy | median | 133 | 30.83% | 0.6005 | -15.05% | 15.07% | 5 | FAIL |
| 9 | dukascopy | p95 | 133 | 30.08% | 0.5750 | -16.01% | 16.01% | 5 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 6/9 | 9/9 | FAIL |
| Total matrix trades | 861 | Informational | PASS |
| Max zero-trade months | 11 | <= 3 | FAIL |
| Cross-broker persistence | Capital.com weak positive below threshold; Pepperstone/Dukascopy negative | Robust positive edge | FAIL |
| Best observed PF | 1.0439 | >= 1.30 in most cells | FAIL |

## Interpretation

The follow-through expression does not rescue the MOVE/VIX bond-volatility shock lane. Capital.com was only slightly positive and below threshold, Pepperstone was negative, and Dukascopy was materially negative. The effect is too sparse and too weak for Phase 0.

## Next Action

Do not tune v0. Treat the paired MOVE/VIX bond-volatility follow-through expression as rejected. Better future work requires a materially different data class, not another threshold edit to this daily MOVE/VIX proxy.
