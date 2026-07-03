# A1 XAU M5 Momentum Frequency-First Weak-Hour V1 Forward Spec - 2026-07-02

Status: `REVIEW_READY_NOT_ATTACHED`

This document defines the forward-demo candidate that matches the owner objective better than the sparse RR2 lane: multiple trades on active days, win rate above 50%, and positive expectancy.

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
| Run ID | `A1_XAU_M5_MOMENTUM_FREQ_FIRST_WEAK_HOUR_V1_20260702` |
| Magic | `932200` if replacing the current RR2 lane; use a new non-colliding magic only if owner explicitly chooses parallel testing |
| Order comment | `A1_XAU_M5_MOM_V1` |

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
InpBlockedEntryHoursCsv=2,9,10,11,12,17,22,23
InpUseDirectionalSessionFilter=false

InpProfitProtectionEnabled=false
InpProfitProtectionShadowOnly=true
```

The profit-protection code exists for offline research only. It is not part of this forward candidate.

## Backtest Evidence

Source report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_WEAK_HOUR_V1_VERDICT_2026_07_02.md`

| Window | Trades | Win Rate | Net USD | PF |
|---|---:|---:|---:|---:|
| 2022.07-2024.06 older OOS | 566 | 65.19% | +339.43 | 1.39 |
| 2024.07-2026.06 recent | 681 | 65.49% | +710.92 | 1.38 |
| 2022.07-2026.06 combined | 1247 | 65.36% | +1050.35 | 1.38 |

Frequency:

```text
Active entry days: 379
Average trades per active entry day: 3.29
Positive entry days: 214
Negative entry days: 165
Months with trades: 47
Positive months: 35
Negative months: 12
Top-10 winners removed: still +907.79 USD
```

## Why V1 Blocks These Hours

The prior frequency-first candidate showed weak or unstable performance in server hours `2`, `9`, `10`, `11`, `12`, `17`, `22`, and `23`. V1 blocks those hours before forward testing instead of attaching a sparse RR2 lane.

This is still a hypothesis. Do not add more filters mid-test.

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

1. Is the weak-hour V1 filter justified by the four-year frequency-first evidence?
2. Does the long-only direction choice look like robust edge selection or overfit?
3. Is blocking hour `2` worth the lower trade count, or should the slightly higher-frequency `midday17` variant be preferred?
4. Is replacing the sparse RR2 lane preferable to running a parallel magic?
5. What evidence should be required before this becomes the primary demo lane?
