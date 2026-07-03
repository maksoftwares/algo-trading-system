# A1 XAU M5 Momentum Frequency-First V4 Combo Rank1 Forward Spec - 2026-07-02

Status: `REVIEW_READY_NOT_ATTACHED`

This document defines the latest frequency-first demo candidate for the owner objective: multiple trades on active days, win rate above 50%, and positive expectancy.

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
| Run ID | `A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702` |
| Magic | `932200` if replacing the current RR2 lane; use a new non-colliding magic only if owner explicitly chooses parallel testing |
| Order comment | `A1_XAU_M5_MOM_V4` |

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
InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,21,23
InpUseDirectionalSessionFilter=false

InpProfitProtectionEnabled=false
InpProfitProtectionShadowOnly=true
```

The profit-protection code exists for offline research only. It is not part of this forward candidate.

## Backtest Evidence

Source report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md`

| Window | Trades | Win Rate | Net USD | PF |
|---|---:|---:|---:|---:|
| 2022.07-2024.06 older OOS | 520 | 65.00% | +309.24 | 1.40 |
| 2024.07-2026.06 recent | 612 | 66.67% | +732.83 | 1.47 |
| 2022.07-2026.06 combined | 1132 | 65.90% | +1042.07 | 1.45 |

Frequency:

```text
Active entry days: 383
Average trades per active entry day: 2.96
Positive entry days: 217
Negative entry days: 166
Months with trades: 47
Positive months: 36
Negative months: 11
Top-10 winners removed: still +899.51 USD
```

## Why V4 Blocks These Hours

V4 was selected from a broad all-hours long-only MT5 ledger and then rerun exactly in MT5. It blocks server hours:

```text
2,9,10,11,12,13,17,19,21,23
```

Compared with V3, V4 restores hours `3` and `8`, removes hour `21`, and improves the frequency-first objective:

```text
V3: 925 trades, 66.81% WR, +988.26 USD, PF 1.53, 2.67 trades/active day
V4: 1132 trades, 65.90% WR, +1042.07 USD, PF 1.45, 2.96 trades/active day
```

V3 remains the higher-PF fallback. V4 is the better fit for the owner's desired trade cadence.

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
Average trades per active day < 2.0 after 20 active days
Any safety, account, symbol, magic, or lot violation
Reviewer identifies unfixable overfit or data-quality flaw
```

## Review Questions

1. Does V4's frequency gain justify the lower PF versus V3?
2. Is the hour-combination search too fit to the historical sample, or did the exact OOS/current MT5 reruns reduce that concern enough for a demo forward test?
3. Should V4 replace the currently attached sparse RR2 lane?
4. Should V3 be retained as the fallback if reviewer prioritizes PF over cadence?
5. What exact evidence should be required before this becomes the primary demo lane?

