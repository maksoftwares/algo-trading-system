# H1 GVZ Realized Vol Spread Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_gvz_realized_vol_spread_reversal_v0` without tuning.

This candidate tested whether shifted GVZ gold implied volatility that is rich versus recent H1 realized XAU volatility identifies short-term exhaustion/reversal. It found a Dukascopy-only positive pocket, but failed sample size in Capital.com/Pepperstone, failed activity, and failed cross-cell PF persistence.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 21 | 28.57% | 0.5615 | -3.12% | 3.97% | 12 | FAIL |
| 2 | capital_com | median | 21 | 28.57% | 0.5615 | -3.12% | 3.97% | 12 | FAIL |
| 3 | capital_com | p95 | 21 | 28.57% | 0.5450 | -3.27% | 4.07% | 12 | FAIL |
| 4 | pepperstone | best_case | 30 | 26.67% | 0.5579 | -4.37% | 6.98% | 13 | FAIL |
| 5 | pepperstone | median | 30 | 26.67% | 0.5579 | -4.37% | 6.98% | 13 | FAIL |
| 6 | pepperstone | p95 | 30 | 26.67% | 0.5538 | -4.37% | 6.91% | 13 | FAIL |
| 7 | dukascopy | best_case | 52 | 48.08% | 1.3098 | +4.06% | 2.78% | 5 | FAIL |
| 8 | dukascopy | median | 52 | 48.08% | 1.2778 | +3.66% | 2.88% | 5 | FAIL |
| 9 | dukascopy | p95 | 52 | 48.08% | 1.2577 | +3.36% | 2.80% | 5 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 1/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 3/9 | 9/9 | FAIL |
| Total matrix trades | 309 | Informational | PASS |
| Max zero-trade months | 13 | <= 3 | FAIL |
| Cross-broker persistence | Dukascopy-only positive pocket | Robust across windows | FAIL |
| Best observed PF | 1.3098 | >= 1.30 in most cells | FAIL |

## Interpretation

The GVZ-versus-realized-volatility spread did not produce a robust independent EA. It is a cleaner options-volatility expression than raw GVZ panic, but its apparent strength was narrow and did not survive broker/cost coverage.

## Next Action

Do not tune v0. A future options lane should require a genuinely richer data source, such as gold options skew, term structure, or primary futures/options order-flow, not another threshold variation of daily GVZ.
