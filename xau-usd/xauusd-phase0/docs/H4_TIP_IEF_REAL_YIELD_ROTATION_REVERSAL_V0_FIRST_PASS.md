# H4 TIP/IEF Real-Yield Rotation Reversal v0 First Pass

Generated: 2026-06-01
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_tip_ief_real_yield_rotation_reversal_v0` without tuning.

The candidate was SHA256-locked before the run and passed synthetic smoke. The real matrix found a useful Pepperstone/Capital.com clue, but it did not clear the hard gates and did not transfer to Dukascopy.

## Summary

- Total cost-cell trades: 351
- PF cells >= 1.30: 3/9
- Trade-count cells >= 40: 6/9
- Best PF: 1.3450
- Best cell: cell 4 / pepperstone / best_case
- Main failure: cross-broker persistence failed. Pepperstone passed PF in all three cost cells, Capital.com stayed below threshold and under trade count, and Dukascopy was negative.

## Matrix

| Cell | Broker | Cost | Trades | Win rate | PF | Avg R | PnL USD | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 27 | 48.15% | 1.2513 | 0.1153 | 152.86 | 5 |
| 2 | capital_com | median | 27 | 48.15% | 1.2513 | 0.1153 | 152.86 | 5 |
| 3 | capital_com | p95 | 27 | 48.15% | 1.2460 | 0.1129 | 149.49 | 5 |
| 4 | pepperstone | best_case | 47 | 53.19% | 1.3450 | 0.1240 | 290.49 | 3 |
| 5 | pepperstone | median | 47 | 53.19% | 1.3450 | 0.1240 | 290.49 | 3 |
| 6 | pepperstone | p95 | 47 | 53.19% | 1.3414 | 0.1225 | 286.92 | 3 |
| 7 | dukascopy | best_case | 43 | 39.53% | 0.7965 | -0.0976 | -212.46 | 1 |
| 8 | dukascopy | median | 43 | 39.53% | 0.7863 | -0.1034 | -224.71 | 1 |
| 9 | dukascopy | p95 | 43 | 39.53% | 0.7796 | -0.1064 | -230.92 | 1 |

## Interpretation

This is a stronger clue than most independent macro/ETF lanes because Pepperstone passed the PF threshold under best, median, and P95 costs. It still fails Phase 0 because the strength was venue-specific, Capital.com did not reach the PF or activity gates, and Dukascopy was materially negative. No decile, multisymbol, or Gate 9 work is justified for v0.

Do not tune v0 thresholds. Any future TIP/IEF real-yield rotation revisit needs a new versioned hypothesis and fresh SHA256 registration, preferably with a materially different mechanism rather than a threshold edit.
