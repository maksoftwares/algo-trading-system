# A3 Signal Quality V2 Soft Retest W15 B45 C60 RCM05

Status: `LOCKED_FOR_COST_APPLIED_FRESH_VALIDATION_ONLY`

Date locked: `2026-06-18`

Account scope: `1033669`

Symbol scope: `XAUUSD`

Candidate ID: `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`

## Boundary

This document locks a signal-quality V2 hypothesis candidate only. It does not authorize live trading, demo broker action, MT5 attachment, profile edits, preset arming, order placement, position management, lot changes, SL/TP changes, or account changes.

A3 remains paused until a separate fresh validation window, reviewer approval, and owner authorization pass.

## Source Family

The candidate starts from the same raw `breakout_retest` would-signal event used by the A3 signal-quality sweep.

No round-family promotion is allowed. No session-only filter is allowed. No exit-management change is included. The exit model remains fixed `1.50R`.

## Candidate Rule

At the completed confirmation bar, keep the raw `breakout_retest` signal only when all checks pass:

```text
bars_after_break = retest_index - break_index
1 <= bars_after_break <= 15

retest_atr = average M5 high-low range over the 14 completed bars from the retest bar back through 13 older bars

LONG:
  retest.close >= level_price + 0.05 * retest_atr
  confirmation.close > level_price
  confirmation close location >= 0.60

SHORT:
  retest.close <= level_price - 0.05 * retest_atr
  confirmation.close < level_price
  confirmation close location <= 0.40

confirmation body / confirmation range >= 0.45
```

Close location is `(close - low) / (high - low)` for long signals and `(high - close) / (high - low)` for short signals. The ATR window includes the completed retest bar. If the confirmation range or ATR is unavailable or non-positive, the signal is blocked.

## What This Fix Targets

The previous evidence showed many A3 losses were not just exit-management problems. Too many entries had weak confirmation or retested the breakout level without enough reclaimed structure. This candidate keeps frequency by allowing a 15-bar retest window, but requires:

- the retest bar to close back beyond the level by at least `0.05 ATR`;
- the confirmation candle to have real body participation;
- the confirmation close to finish in the trade direction.

## Discovery Evidence

Report: `outputs/reports/A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_2026_06_18.md`

Threshold provenance: `docs/A3_SIGNAL_QUALITY_V2_SOFT_RETEST_THRESHOLD_PROVENANCE_2026_06_18.md`

Data source: phase0 offline Dukascopy XAUUSD bars, `2025-01-02` through `2025-07-01`.

This is discovery evidence only. It must not be reused as promotion evidence.

PF, expectancy, net R, drawdown, and eligibility are computed on net R after subtracting `cost_r`. This historical Dukascopy source has zero/unavailable spread fields, so the discovery table is not cost-validating edge evidence; it only justifies carrying the candidate into a fresh measured-cost validation window.

The thresholds were selected through a targeted discovery search. Because the selected values were not pre-registered before that search, all discovery and June replay figures are treated as zero promotion evidence.

| Metric | B0 raw one-position baseline | V2 candidate |
| --- | ---: | ---: |
| Accepted signals | 1453 | 586 |
| Signal retention | 100.00% | 40.33% |
| Opened virtual trades | 885 | 490 |
| Trade retention vs B0 | 100.00% | 55.37% |
| Median weekly trade retention | 100.00% | 59.38% |
| Net profit factor | 1.2484 | 1.9186 |
| Net expectancy | +0.1356R | +0.4031R |
| P95 cost_R in source | 0.0000 | 0.0000 |
| Win rate | 45.42% | 56.12% |
| Bad-signal loss share | 50.10% | 35.81% |
| Bad-signal loss share improvement | 0.00% | 28.52% |
| Max consecutive losses | 14 | 6 |
| Max drawdown | 20.5R | 7.5R |
| Weeks with at least 15 trades | 23 | 20 |
| Long / short opened trades | 499 / 386 | 281 / 209 |
| H1 regimes represented | rising and falling | rising and falling |
| Largest winning trade concentration | 1.25% | 0.76% |
| Top-five winning trade concentration | 6.25% | 3.80% |
| Best-day positive contribution | 2.74% | 2.55% |

## Fresh Validation Requirements

The next validation window must be fresh and must not reuse the discovery data above.

Minimum before any reactivation discussion:

```text
closed virtual trades >= 100
calendar coverage >= 20 days
calendar coverage >= 4 weeks
long trades >= 25
short trades >= 25
weeks with >= 15 trades >= 3
signal retention >= 40% of B0
virtual-trade retention >= 35% of B0
median weekly trade retention >= 40% of B0
PF >= 1.30 target, PF >= 1.20 hard floor
expectancy >= +0.15R target, expectancy >= +0.10R hard floor
hard WR >= 45%, target WR >= 50%
P95 cost_R <= 0.15
max consecutive losses <= 8
max drawdown <= 8R
bad-signal loss share materially reduced versus B0
both rising and falling regimes represented
zero duplicate-family events
decision parity >= 99%
accepted-signal parity = 100%
```

If any gate fails, A3 remains paused and this V2 candidate is not promoted.
