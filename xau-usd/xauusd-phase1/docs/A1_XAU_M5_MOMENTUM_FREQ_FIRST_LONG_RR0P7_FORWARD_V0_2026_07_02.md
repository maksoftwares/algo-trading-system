# A1 XAU M5 Momentum Frequency-First Long RR0.7 Forward V0 - 2026-07-02

Status: `REVIEW_READY_NOT_ATTACHED`

This document defines the forward-demo candidate that matches the owner objective better than the currently attached sparse RR2 lane: multiple trades on active days, win rate above 50%, and positive expectancy.

## Boundary

- Demo only.
- No live trading.
- No real capital.
- No canonical Phase 2 approval.
- No runtime attachment is authorized by this document alone.
- This candidate must not be attached until owner approval is recorded after independent review.
- If attached, it should replace/supersede the sparse RR2 A1 momentum lane rather than stack with it.

## Candidate

| Field | Value |
|---|---|
| EA | `A1XauM5MomentumContinuationExecutor.mq5` |
| Symbol | `XAUUSD` |
| Timeframe | `M5` |
| Account | A1 / `1025742` only |
| Lot | `0.01` fixed |
| Direction mode | `MOMENTUM_LONG_ONLY` |
| Run ID | `A1_XAU_M5_MOMENTUM_FREQ_FIRST_LONG_RR0P7_FORWARD_V0_20260702` |
| Magic | `932200` if replacing the current RR2 lane; use a new non-colliding magic only if owner explicitly chooses parallel testing |
| Order comment | `A1_XAU_M5_MOM_FREQ07` |

## Frozen Inputs

```text
InpAllowDemoTrading=true
InpAllowNonDemoAccounts=false
InpAllowedAccountLogin=1025742
InpExpectedServerMarker=Demo
InpTargetSymbol=XAUUSD
InpFixedLots=0.01
InpMaxSpreadPoints=75
InpMaxEstimatedCostR=0.05
InpMaxTradesPerDay=12
InpCooldownMinutes=5
InpOnePositionPerMagic=true
InpMaxOpenPositionsPerMagic=1

InpDirectionMode=1
InpUseH1TrendFilter=true
InpH1TrendApplyToLong=true
InpH1TrendApplyToShort=true
InpH1TrendMinSlopePoints=0
InpUseH4TrendFilter=true
InpH4TrendApplyToLong=true
InpH4TrendApplyToShort=true
InpH4TrendMinSlopePoints=0

InpRiskReward=0.70
InpBlockedEntryHoursCsv=9,10,22,23
InpUseDirectionalSessionFilter=false

InpProfitProtectionEnabled=false
InpProfitProtectionShadowOnly=true
```

The profit-protection code exists for offline research only. It is not part of this forward candidate.

## Backtest Evidence

Source report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_DIRECTION_REPAIR_VERDICT_2026_07_02.md`

| Window | Trades | Win Rate | Net USD | PF |
|---|---:|---:|---:|---:|
| 2022.07-2024.06 older OOS | 735 | 62.72% | +281.92 | 1.24 |
| 2024.07-2026.06 recent | 853 | 64.13% | +847.31 | 1.35 |
| 2022.07-2026.06 combined | 1588 | 63.48% | +1129.23 | 1.31 |

Frequency:

```text
Active trading days: 405
Average trades per active day: 3.92
Positive months: 35 / 48
Top-10 winners removed: still +876.39 USD
```

## Known Weak Spots To Monitor

These are not additional filters in V0. They are forward-test diagnostics:

| Weak area | Backtest evidence |
|---|---|
| Hour 2 | 68 trades, 52.94% WR, -58.53 USD, PF 0.75 |
| Hour 11 | 74 trades, 56.76% WR, -36.77 USD, PF 0.81 |
| Hour 12 | 136 trades, 55.88% WR, -36.03 USD, PF 0.90 |
| Hour 17 | 62 trades, 48.39% WR, -44.20 USD, PF 0.74 |
| 15-30 minute exits | 312 trades, 59.29% WR, -46.40 USD, PF 0.95 |
| 30-60 minute exits | 342 trades, 59.36% WR, +10.80 USD, PF 1.01 |
| 0.8-1.2 ATR three-bar momentum | 222 trades, 58.56% WR, -6.02 USD, PF 0.99 |

Do not add these filters mid-test. They are only for deciding the next V1 after V0 forward evidence exists.

## Forward Test Rule

Minimum observation before judgment:

```text
At least 100 closed forward trades
At least 4 active trading weeks
At least 20 active trading days
No input changes during the window
No lot-size change
No added filters
No manual trade intervention counted as strategy evidence
```

Pass candidate:

```text
WR >= 55%
PF >= 1.25
Net positive
Average trades per active day >= 2.0
No single day contributes more than 35% of net profit
Positive after removing top 5 winners
No runtime/broker-action violation
```

Kill or revise:

```text
Net negative after 60 closed trades
Rolling 40-trade PF < 0.90
WR < 50% after 80 closed trades
Equity drawdown > 15% for this lane
Any safety, account, symbol, magic, or lot violation
Reviewer identifies unfixable overfit or data-quality flaw
```

## Review Questions

1. Is the older split PF `1.24` acceptable for a tiny demo forward test, given that WR and frequency are strong?
2. Does the long-only direction choice look like robust edge selection or overfit?
3. Should V0 remain exactly as above, or should weak hours `2,11,12,17` be filtered before forward testing?
4. Is replacing the sparse RR2 lane preferable to running a parallel magic?
5. What evidence should be required before this becomes the primary demo lane?
