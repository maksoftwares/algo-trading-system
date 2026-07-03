# A1 XAU M5 Momentum Frequency-First V2 Block13/19 Forward Spec - 2026-07-02

Status: `REVIEW_READY_NOT_ATTACHED`

This document defines the preferred forward-demo candidate for the owner objective: multiple trades on active days, win rate above 50%, and positive expectancy.

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
| Run ID | `A1_XAU_M5_MOMENTUM_FREQ_FIRST_V2_BLOCK13_19_20260702` |
| Magic | `932200` if replacing the current RR2 lane; use a new non-colliding magic only if owner explicitly chooses parallel testing |
| Order comment | `A1_XAU_M5_MOM_V2` |

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
InpBlockedEntryHoursCsv=2,9,10,11,12,13,17,19,22,23
InpUseDirectionalSessionFilter=false

InpProfitProtectionEnabled=false
InpProfitProtectionShadowOnly=true
```

The profit-protection code exists for offline research only. It is not part of this forward candidate.

## Backtest Evidence

Source report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V2_BLOCK13_19_VERDICT_2026_07_02.md`

| Window | Trades | Win Rate | Net USD | PF |
|---|---:|---:|---:|---:|
| 2022.07-2024.06 older OOS | 497 | 65.19% | +305.23 | 1.42 |
| 2024.07-2026.06 recent | 580 | 66.72% | +719.84 | 1.48 |
| 2022.07-2026.06 combined | 1077 | 66.02% | +1025.07 | 1.46 |

Frequency:

```text
Active entry days: 360
Average trades per active entry day: 2.99
Positive entry days: 205
Negative entry days: 155
Months with trades: 47
Positive months: 35
Negative months: 12
Top-10 winners removed: still +882.51 USD
```

## Why V2 Blocks These Hours

The V1 candidate already blocked hours `2,9,10,11,12,17,22,23`. V2 additionally blocks `13` and `19` because the V1 source ledger showed these hours were marginal. The added block improves PF from `1.38` to `1.46` while retaining `1077` four-year trades and almost three trades per active entry day.

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

1. Is the V2 hour block justified by the four-year frequency-first evidence?
2. Is the trade-count reduction acceptable given the PF and win-rate lift?
3. Does this look robust enough for a minimum-lot demo replacement of sparse RR2?
4. Should the current RR2 lane be replaced rather than stacked?
5. What exact evidence should be required before this becomes the primary demo lane?
