# A1 XAU M5 Momentum Broad Portfolio Search Verdict

Generated: 2026-07-02  
Scope: offline analysis of exact MT5 Strategy Tester trade CSVs only. No MT5 runtime, chart, preset, order, or position setting was changed.

## Why this test exists

The owner wants a system that can realistically trade multiple times on active days while keeping win rate above 50% and staying profitable. Single-lane V4 is clean but not active enough on enough days. Some high-frequency lanes are active but too noisy.

This search scans exact four-year MT5 trade CSVs and combines candidate lanes as if each lane had its own magic number. It then rejects combinations that only look good because of duplicate same-minute stacking.

## Source report

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md
```

## Best high-net candidate

```text
rr_2p0_long_only_h1_h4_atr15_no0910
+
v6_freq_v4_rr0p7_max2
```

| Metric | Value |
|---|---:|
| Trades | 2009 |
| Win rate | 56.65% |
| Net USD | +2884.32 |
| PF | 1.49 |
| Active days | 435 |
| Trades / active day | 4.62 |
| Positive / negative months | 36 / 11 |
| Top-25 removed | +1964.06 |
| Max closed DD | 131.65 |
| Duplicate-like trade pct | 26.28% |

Verdict:

```text
STRONG_NUMBERS_BUT_STACKING_REVIEW_REQUIRED
```

This candidate is powerful, but it includes a `max2` lane and has meaningful same-minute overlap. It may still be valid as controlled position scaling, but it is not the cleanest first forward candidate.

## Best clean no-duplicate candidate

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
| Duplicate-like trade pct | 0.00% |

Verdict:

```text
BEST_CLEAN_PORTFOLIO_REVIEW_CANDIDATE
```

This is the most defensible next candidate because it improves active-day coverage without relying on duplicate stacking.

## Mechanical definition of clean candidate

### Long lane: `v5_v4_move12`

```text
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
```

### Short lane: `freq_h1_h4_short_rr0p7_v1_core_1_5_15_19`

```text
Signal mode: SIGNAL_BREAK_AND_RUN
Direction: SHORT only
H1 EMA20/50 trend filter: enabled
H4 EMA20/50 trend filter: enabled
Risk reward: 0.70R
Max estimated cost: 0.05R
Blocked server hours: 0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23
Allowed server hours: 1,2,3,4,5,15,19
Max trades/day: 12
Cooldown: 5 minutes
```

## Why this is better aligned with the owner's goal

Compared with V4 alone:

| Item | V4 only | Clean portfolio |
|---|---:|---:|
| Trades | 1132 | 1317 |
| Win rate | 65.90% | 64.54% |
| Net USD | +1042.07 | +1139.94 |
| PF | 1.45 | 1.43 |
| Active days | 383 | 535 |
| Trades / active day | 2.96 | 2.46 |
| Max closed DD | 88.84 | 59.38 |

The clean portfolio gives more active days, more total trades, and lower drawdown while keeping PF and win rate close to V4.

## Current recommendation

```text
Ask reviewer to inspect the clean no-duplicate portfolio first.
Do not deploy yet.
If approved, build a frozen demo forward spec with two separate magic numbers:
  LONG lane magic 932210
  SHORT lane magic 932211
Both remain XAUUSD M5, 0.01 lot, A1 demo only.
```

This is currently the best answer to the business requirement found in the workspace.

## Implementation readiness

Attach tooling has been prepared, but not executed:

```text
python xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py --variant clean_long_v5_move12
python xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py --variant clean_short_core
```

Important boundary:

```text
No MT5 runtime was touched while preparing this support.
The attach commands require owner/reviewer approval before use.
```
