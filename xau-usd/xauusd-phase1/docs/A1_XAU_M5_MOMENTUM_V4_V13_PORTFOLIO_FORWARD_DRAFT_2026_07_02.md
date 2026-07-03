# A1 XAU M5 Momentum V4 + V13 Portfolio Forward Draft

Status: `DRAFT_READY_FOR_REVIEW_NOT_LOCKED`  
Generated: 2026-07-02  
Scope: proposed demo forward-test specification only. No MT5 runtime, chart, preset, order, or position setting was changed.

## Purpose

The owner clarified that the target system must create multiple intraday opportunities, not only a small number of clean trades per month.

The best current single-lane candidate is V4. It has strong quality but limited active-day coverage. V13 creates more activity but is weaker alone. This draft tests whether the two can work as a small, controlled portfolio:

```text
V4 = primary quality lane
V13 = companion frequency lane
```

## Evidence Basis

Source report:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.md
```

Four-year exact MT5 trade-CSV portfolio result:

| Portfolio | Trades | WR % | Net USD | PF | Active days | Trades / active day | Multi-trade days | +M | -M | Max closed DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V4 only | 1132 | 65.90 | +1042.07 | 1.45 | 383 | 2.96 | 258 | 36 | 11 | 88.84 |
| V13 leading only | 1786 | 61.53 | +862.93 | 1.20 | 668 | 2.67 | 435 | 25 | 23 | 192.51 |
| V4 + V13 leading raw | 2918 | 63.23 | +1905.00 | 1.29 | 692 | 4.22 | 518 | 33 | 15 | 132.63 |

Interpretation:

```text
V4 alone is cleaner.
V4 + V13 better matches the activity goal.
The portfolio has lower PF and higher drawdown than V4 alone, so it must be tested small and separately.
```

## Proposed Demo Scope

```text
Account: A1 only, 1025742 / Capital.ComMena-Demo
Symbol: XAUUSD only
Timeframe: M5
Lot: 0.01 fixed per lane
Canonical Phase 2: unchanged
Live/real capital: not authorized
Existing 920101 breakout-retest lanes: unchanged by this draft
```

## Lane A: V4 Primary

```text
EA: A1XauM5MomentumContinuationExecutor
Magic: 932200
Order comment: A1_XAU_M5_MOM_V4
Signal mode: SIGNAL_BREAK_AND_RUN
Direction: LONG only
H1 EMA20/50 trend filter: enabled
H4 EMA20/50 trend filter: enabled
Risk reward: 0.70R
Max estimated cost: 0.05R
Blocked server hours: 2,9,10,11,12,13,17,19,21,23
Max trades/day: 12
Cooldown: 5 minutes
One own position per magic: true
```

## Lane B: V13 Companion

```text
EA: A1XauM5MomentumContinuationExecutor
Magic: 932201
Order comment: A1_XAU_M5_MOM_V13
Signal mode: SIGNAL_M5_EMA_TREND_CONTINUATION
Direction: both
H1 EMA20/50 trend filter: enabled
H4 EMA20/50 trend filter: enabled
Risk reward: 0.70R
Max estimated cost: 0.05R
General blocked server hours: 0,2,4,9,10,11,12,16,19,20
Short-only blocked server hours: 13,14,15,17,18
Long-only blocked server hours: none
M5 EMA fast/slow: 8/21
M5 EMA slope bars: 3
Minimum EMA slope: 0.03 ATR
Max distance from fast EMA: 1.20 ATR
Minimum range: 0.35 ATR
Minimum body fraction: 0.30
Long close location: >= 0.58
Short close location: <= 0.42
Minimum 3-bar move: 0.10 ATR
One own position per magic: true
```

## Portfolio Risk Rules

```text
Both lanes stay at 0.01 lot.
No martingale, grid, recovery, lot increase, or additional symbols.
No new V13 tuning during the test.
Do not add more companion lanes until this portfolio window closes.
Keep lane attribution separated by magic/order comment.
Treat V4 and V13 as one family for review and daily risk, even though they use separate magic numbers.
```

Recommended portfolio-level guard:

```text
Daily portfolio loss stop: -100 AED across magic 932200 + 932201
Daily soft profit checkpoint: +50 AED
Daily full profit checkpoint: +100 AED
Rolling kill: portfolio PF < 0.90 over latest 80 trades
Hard kill: portfolio net negative after 150 closed trades
Hard kill: V13 companion net negative after 100 closed V13 trades
Hard kill: any safety/governance mismatch
```

## Forward-Test Acceptance

Minimum evidence before judging:

```text
At least 4 full trading weeks
At least 150 combined closed trades
At least 75 V13 companion closed trades
At least 20 active trading days
No mid-test parameter changes
```

Pass only if:

```text
Combined portfolio PF >= 1.25
Combined win rate >= 55%
Combined net positive
V13 companion net positive
No single day contributes more than 30% of net
Top-10 winners removed remains positive
No unresolved runtime identity drift
```

Reject or revise if:

```text
V13 increases trade count but reduces combined PF below 1.20
V13 produces negative net after 100 closed V13 trades
Daily loss stop is repeatedly hit
Portfolio drawdown materially exceeds V4-only expectation
Reviewer finds duplicate/stacking inflation rather than real diversification
```

## Implementation Note

Current attach tooling supports V4 (`--variant freq_v4`) but does not yet deploy the V13 companion as a separate `932201` lane.

If this draft is approved, the implementation step is:

```text
Add attach-script support for --variant freq_v13_companion.
Deploy V4 and V13 with separate magic/order comments.
Regenerate runtime inventory and startup/order-log proof.
```

No attachment is authorized by this draft.

