# EURUSD H4 dual-regime portfolio diagnostic

Status: **HISTORICALLY_ROBUST_DUAL_REGIME_CANDIDATE_REQUIRES_FRESH_CONFIRMATION**

This combines the unchanged chop expert at 1.0 risk with the unchanged compression expert at 0.5 risk. It is a post-selection developmental result, not pristine confirmation and not permission to trade.

## Full history

- 507 trades from 2017-01 through 2026-06
- Win rate: 47.93%
- Payoff ratio: 1.309
- Profit factor: 1.210
- Net: +42.940R
- Maximum closed-trade drawdown: 11.373R
- PF with best 5% of winners removed: 1.051

## Robustness

- +0.5 pip cost PF: 1.155
- +1.0 pip cost PF: 1.102
- 5-minute delayed entry PF: 1.179
- 15-minute delayed entry PF: 1.186
- Trade-block bootstrap PF 5th percentile: 1.034; P(PF <= 1): 2.17%
- Three-calendar-month block bootstrap PF 5th percentile: 1.054; P(PF <= 1): 1.05%

## Recent results

- Latest 12 months: 52 trades, PF 1.535, +9.025R
- Latest 6 months: 23 trades, win rate 47.83%, payoff 1.411, PF 1.294, +2.520R

| Month | Trades | Win rate | PF | Net R |
|---|---:|---:|---:|---:|
| 2026-01 | 2 | 50.0% | 18.287 | +0.679 |
| 2026-02 | 4 | 25.0% | 0.494 | -1.273 |
| 2026-03 | 6 | 33.3% | 0.455 | -2.190 |
| 2026-04 | 3 | 33.3% | 1.236 | +0.238 |
| 2026-05 | 5 | 80.0% | 7.715 | +3.376 |
| 2026-06 | 3 | 66.7% | 4.358 | +1.690 |

All inherited descriptive thresholds passed: True.

This is the strongest honest regime-combination result in the current branch. Because the half-risk allocation was selected after historical inspection, the next valid evidence must come from an untouched/prospective sample.
