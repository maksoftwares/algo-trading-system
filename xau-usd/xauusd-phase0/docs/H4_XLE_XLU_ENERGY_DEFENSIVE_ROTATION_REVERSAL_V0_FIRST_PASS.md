# H4 XLE/XLU Energy-Defensive Rotation Reversal v0 First-Pass Result

Expert: `h4_xle_xlu_energy_defensive_rotation_reversal_v0`
Hypothesis: `docs/hypothesis_h4_xle_xlu_energy_defensive_rotation_reversal_v0.md`
Hypothesis SHA256: `5914340f8d6f75959d6fac431c511033419eee210d39f5710578b5cb6aa03e04`
Status: `REJECTED_FIRST_PASS`

## Summary

`h4_xle_xlu_energy_defensive_rotation_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether shifted public XLE/XLU energy-versus-defensive sector rotation can identify H4 XAU reversal opportunities after a completed rejection candle.

The candidate is rejected first-pass. It produced enough trades in every cell and had a Pepperstone-only positive pocket, but it failed cross-broker persistence: 3/9 PF cells reached PF >= 1.30, all three were Pepperstone cells, and Capital.com plus Dukascopy were negative across cost cases. Concentration also failed.

## Gate Snapshot

| Metric | Observed | Required | Result |
|---|---:|---:|---|
| Total cost-cell trades | 453 | n/a | Review only |
| Trade-count cells | 9/9 | 7/9 | PASS |
| PF >= 1.30 cells | 3/9 | 7/9 | FAIL |
| Positive-PnL cells | 3/9 | n/a | Broker-specific |
| Best PF | 1.3610 | >= 1.30 | Pepperstone only |
| Max zero-trade months | 3 | <= 3 | PASS |
| Largest single trade concentration | 21.1%-100.0% | <= 10% | FAIL |
| Top-5 trade concentration | 100.0%-111.4% | <= 40% | FAIL |

## Cell Results

| Cell | Broker | Cost | Trades | PF | Total PnL % | Win Rate | Max Zero Months |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Capital.com | best_case | 44 | 0.8728 | -1.30% | 40.91% | 3 |
| 2 | Capital.com | median | 44 | 0.8728 | -1.30% | 40.91% | 3 |
| 3 | Capital.com | p95 | 44 | 0.8557 | -1.47% | 40.91% | 3 |
| 4 | Pepperstone | best_case | 58 | 1.3610 | 3.73% | 53.45% | 2 |
| 5 | Pepperstone | median | 58 | 1.3610 | 3.73% | 53.45% | 2 |
| 6 | Pepperstone | p95 | 58 | 1.3291 | 3.42% | 53.45% | 2 |
| 7 | Dukascopy | best_case | 49 | 0.9442 | -0.61% | 38.78% | 2 |
| 8 | Dukascopy | median | 49 | 0.9317 | -0.75% | 38.78% | 2 |
| 9 | Dukascopy | p95 | 49 | 0.8920 | -1.21% | 38.78% | 2 |

## Decision

Reject v0. Do not tune this candidate in place. The Pepperstone pocket is useful as a clue, but it is not enough to count as an independent higher-timeframe EA.
