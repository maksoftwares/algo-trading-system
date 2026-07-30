# EURUSD H4 confirmation uniform-risk backtest result

Status: **BACKTEST GATES PASSED — PROSPECTIVE CONFIRMATION STILL REQUIRED**

The exact portfolio contains the protected H4/M15 first-break core plus
next-close and four-bar retest confirmations in the H4 chop and compression
regimes. All entries are SHORT. The portfolio keeps the parent 1,288 trades
and scales every sleeve uniformly to a maximum aggregate initial-risk budget
of 1.5R.

## Frozen-gate result

All 16 preregistered gates passed:

- 1,288 trades across 2,476 FX days, or 0.520 trades per FX day;
- 45.73% wins and 1.413 realized R-payoff;
- full-history R-profit factor 1.190;
- 0.5-pip stressed PF 1.136 and 1.0-pip stressed PF 1.084;
- PF above 1 in all four chronological blocks;
- latest-12-month PF 1.620 and latest-six-month PF 1.929;
- best-5%-removed PF 1.037;
- maximum drawdown 17.924 portfolio R against the 18R limit;
- trade-block bootstrap PF 5th percentile 1.054, with 1.03% probability
  of PF at or below 1;
- calendar-block bootstrap PF 5th percentile 1.070, with 0.275%
  probability of PF at or below 1.

## Chronological results

The USD column is a fixed nominal 0.1-lot equivalent after the same uniform
75% portfolio scaling. The strategy contract itself is risk-budgeted, so the
R metrics are the admission metrics.

| Window | Trades | Win rate | R-payoff | R-PF | Fixed-lot cash PF | 0.1-lot-equivalent P&L |
|---|---:|---:|---:|---:|---:|---:|
| 2017-2019 | 411 | 44.04% | 1.478 | 1.163 | 1.137 | +$352.22 |
| 2020-2022 H1 | 370 | 45.68% | 1.402 | 1.179 | 1.207 | +$489.69 |
| 2022 H2-2024 H1 | 274 | 44.89% | 1.283 | 1.045 | 0.988 | -$24.47 |
| 2024 H2-2026 H1 | 233 | 49.79% | 1.493 | 1.480 | 1.423 | +$544.19 |
| Latest 12 months | 135 | 51.11% | 1.550 | 1.620 | 1.636 | +$398.56 |
| Latest 6 months | 53 | 58.49% | 1.369 | 1.929 | 1.846 | +$220.26 |
| Full 2017-2026 | 1,288 | 45.73% | 1.413 | 1.190 | 1.164 | +$1,361.63 |

The 2022 H2-2024 H1 block is positive under constant-risk sizing but slightly
negative under fixed nominal lots because its losing trades had larger price
stops. This is why the accepted portfolio must use risk-based sizing rather
than a fixed lot on every trade.

## Latest six months

| Month | Trades | Win rate | Fixed-lot cash PF | 0.1-lot-equivalent P&L |
|---|---:|---:|---:|---:|
| 2026-01 | 9 | 55.56% | 1.305 | +$11.56 |
| 2026-02 | 9 | 33.33% | 0.856 | -$7.25 |
| 2026-03 | 12 | 50.00% | 1.394 | +$40.76 |
| 2026-04 | 7 | 28.57% | 0.478 | -$32.40 |
| 2026-05 | 10 | 90.00% | 18.500 | +$118.30 |
| 2026-06 | 6 | 100.00% | infinite (no losses) | +$89.29 |
| **Total** | **53** | **58.49%** | **1.846** | **+$220.26** |

## Boundary

This is the strongest honest EURUSD backtest candidate in the current
campaign. It improves the protected baseline from 0.271 to 0.520 trades per FX
day while preserving its edge.

It is not yet demo-ready evidence because the experiment is adaptive
historical research, not a pristine unseen holdout. Frequency also remains
below the desired one trade per day, and the latest six months contain only
53 trades with two losing months. The prospective observer remains paused
until the user explicitly moves the campaign beyond backtest work.
