# A1 XAU M5 Momentum Clean Long/Short Portfolio Forward Draft

Status: `DRAFT_READY_FOR_REVIEW_NOT_LOCKED`  
Generated: 2026-07-02  
Scope: proposed demo forward-test specification only. No MT5 runtime, chart, preset, order, or position setting was changed.

## Purpose

The owner wants an intraday system that can produce multiple opportunities on active days while keeping win rate above 50% and remaining profitable. The broad portfolio search found a clean no-duplicate two-lane candidate that better matches that objective than the sparse RR2 lane.

## Evidence Basis

Source reports:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md
```

Four-year exact MT5 trade-CSV result for the clean candidate:

```text
v5_v4_move12
+
freq_h1_h4_short_rr0p7_v1_core_1_5_15_19
```

| Metric | Value |
|---|---:|
| Trades | 1317 |
| Win rate | 64.54% |
| Net USD | +1139.94 |
| PF | 1.43 |
| Active days | 535 |
| Trades / active day | 2.46 |
| Multi-trade days | 321 |
| Positive / negative months | 37 / 11 |
| Worst month | -22.58 |
| Top-25 removed | +824.07 |
| Max closed DD | 59.38 |
| Duplicate-like same-minute overlap | 0.00% |

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

## Lane A: Clean Long

```text
EA: A1XauM5MomentumContinuationExecutor
Magic: 932210
Order comment: A1_XAU_M5_MOM_CLN_L
Signal mode: SIGNAL_BREAK_AND_RUN
Direction: LONG only
H1 EMA20/50 trend filter: enabled
H4 EMA20/50 trend filter: enabled
Risk reward: 0.70R
Max estimated cost: 0.05R
Blocked server hours: 2,9,10,11,12,13,17,19,21,23
Minimum 3-bar move: 1.20 ATR
Max trades/day: 12
Cooldown: 5 minutes
One own position per magic: true
```

## Lane B: Clean Short Core

```text
EA: A1XauM5MomentumContinuationExecutor
Magic: 932211
Order comment: A1_XAU_M5_MOM_CLN_S
Signal mode: SIGNAL_BREAK_AND_RUN
Direction: SHORT only
H1 EMA20/50 trend filter: enabled
H4 EMA20/50 trend filter: enabled
Risk reward: 0.70R
Max estimated cost: 0.05R
Allowed server hours: 1,2,3,4,5,15,19
Blocked server hours: 0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23
Max trades/day: 12
Cooldown: 5 minutes
One own position per magic: true
```

## Portfolio Risk Rules

```text
Both lanes stay at 0.01 lot.
No martingale, grid, recovery, lot increase, or additional symbols.
No extra companion lane during the test.
No mid-test hour-mask or RR changes.
Keep lane attribution separated by magic and order comment.
Treat both lanes as one family for portfolio-level risk review.
```

Suggested portfolio-level controls:

```text
Daily portfolio loss stop: -100 AED across magic 932210 + 932211
Daily soft profit checkpoint: +50 AED
Daily full profit checkpoint: +100 AED
Rolling kill: portfolio PF < 0.90 over latest 80 trades
Hard kill: portfolio net negative after 150 closed trades
Hard kill: either lane net negative after 100 closed trades in that lane
Hard kill: any runtime identity or safety mismatch
```

## Forward-Test Acceptance

Minimum evidence before judging:

```text
At least 4 full trading weeks
At least 150 combined closed trades
At least 40 closed trades per lane
At least 20 active trading days
No mid-test parameter changes
```

Pass only if:

```text
Combined portfolio PF >= 1.25
Combined win rate >= 55%
Combined net positive
Both lanes net non-negative
No single day contributes more than 30% of net
Top-10 winners removed remains positive
No unresolved runtime identity drift
```

Reject or revise if:

```text
Combined PF drops below 1.20
Either lane becomes a persistent drag
Daily loss stop is repeatedly hit
Forward result depends on 1-2 exceptional days
Reviewer finds the hour masks too overfit for forward testing
```

## Implementation Note

Attach tooling now has planned variant keys:

```text
clean_long_v5_move12
clean_short_core
```

This draft does not authorize attachment. If owner/reviewer approves, run the attach script separately for each lane and capture runtime inventory plus startup/order-log evidence.

