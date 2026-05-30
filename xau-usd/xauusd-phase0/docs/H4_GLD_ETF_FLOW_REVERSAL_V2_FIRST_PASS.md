# H4 GLD ETF Flow Reversal v2 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_gld_etf_flow_reversal_v2` without tuning.

This result-informed v2 preserved the original v0 GLD-flow stress thresholds and added only the 08:00 UTC H4 decision slot. It improved trade count versus v0, but did not clear first-pass gates: 6/9 PF cells reached 1.30, only 6/9 cells reached 40 trades, max zero-trade months reached 5, and concentration remained too high.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Single Trade | Top 5 | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 32 | 59.38% | 1.6025 | +3.00% | 1.06% | 5 | 24.75% | 119.75% | FAIL |
| 2 | capital_com | median | 32 | 59.38% | 1.6025 | +3.00% | 1.06% | 5 | 24.75% | 119.75% | FAIL |
| 3 | capital_com | p95 | 32 | 59.38% | 1.5990 | +2.96% | 1.07% | 5 | 25.04% | 121.21% | FAIL |
| 4 | pepperstone | best_case | 51 | 50.98% | 1.2727 | +2.75% | 3.50% | 4 | 27.58% | 134.49% | FAIL |
| 5 | pepperstone | median | 51 | 50.98% | 1.2727 | +2.75% | 3.50% | 4 | 27.58% | 134.49% | FAIL |
| 6 | pepperstone | p95 | 51 | 50.98% | 1.2644 | +2.68% | 3.53% | 4 | 28.27% | 137.85% | FAIL |
| 7 | dukascopy | best_case | 43 | 51.16% | 1.6200 | +4.50% | 2.81% | 5 | 16.82% | 82.40% | FAIL |
| 8 | dukascopy | median | 43 | 51.16% | 1.6010 | +4.39% | 2.85% | 5 | 17.18% | 84.17% | FAIL |
| 9 | dukascopy | p95 | 43 | 51.16% | 1.5637 | +4.12% | 2.85% | 5 | 18.19% | 88.35% | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 6/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 6/9 | 9/9 | FAIL |
| Total matrix trades | 378 | Informational | PASS |
| Max zero-trade months | 5 | <= 3 | FAIL |
| Largest single trade contribution | 28.27% | <= 10% | FAIL |
| Top-5 trade contribution | 137.85% | <= 40% | FAIL |
| P95 cost robustness | PF stayed high where the sample worked, but Pepperstone stayed below threshold | Must remain buildable under P95 | FAIL |

## Interpretation

The v2 timing-only broadened GLD-flow version remains a useful independent lead, but not a selected EA. The positive PF survives in Capital.com and Dukascopy, while Pepperstone remains below threshold and the sample is still too sparse and concentrated. This confirms that the GLD-flow reversal lane has signal but not enough buildable breadth under the current public ETF proxy.

## Next Action

Do not tune v2. Any future GLD-flow revisit needs a new versioned hypothesis with a materially different information source or mechanism, preferably primary futures/options participation data rather than another minor threshold or timing adjustment.
