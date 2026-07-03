# A1 XAU M5 Momentum Deep Portfolio Forward Draft - 2026-07-02

## Status

```text
PRIMARY_REVIEW_CANDIDATE_NOT_ATTACHED
```

This draft prepares the current best frequency-plus-quality portfolio for independent review. It is not runtime approval.

## Boundary

- Demo only.
- A1 only, account `1025742`.
- XAUUSD only.
- M5 only.
- Fixed lot `0.01`.
- No real capital.
- No canonical Phase 2 approval.
- No MT5 runtime changes from this document alone.
- Runtime attachment requires reviewer acceptance and owner approval.

## Why this replaces sparse RR2 as the main path

The owner clarified that a strategy taking only a few trades in a month does not match the project vision. The desired system needs multiple intraday opportunities while keeping win rate above 50% and staying net positive.

This portfolio was selected because it better matches that shape after same-minute same-direction de-duplication:

| Metric | Value |
|---|---:|
| Deduped trades | 3058 |
| Win rate | 65.73% |
| Net USD | +2156.21 |
| Profit factor | 1.34 |
| Active days | 718 |
| Trades / active day | 4.26 |
| Positive / negative months | 37 / 11 |
| Worst month | -37.02 |
| Top 25 winners removed | +1835.20 |
| Max closed drawdown | 89.04 |
| Raw duplicate-like overlap | 3.15% |

## Portfolio lanes

### Lane 1 - V6 long frequency lane

```text
Variant: v6_freq_v4_rr0p7_max2
Magic: 932220
Comment: A1_XAU_M5_MOM_DP_L1
Direction: LONG only
Signal mode: break-and-run
Risk reward: 0.70
Cost cap: cost_R <= 0.05
Blocked server hours: 2,9,10,11,12,13,17,19,21,23
Max trades/day: 20
Cooldown minutes: 3
One position per magic: false
Max open positions per magic: 2
```

This lane is the strongest frequency-first long engine. It allows up to two own positions, so duplicate/stacking review is mandatory during forward testing.

### Lane 2 - V13 both-direction EMA-trend lane

```text
Variant: v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning
Magic: 932221
Comment: A1_XAU_M5_MOM_DP_B
Direction: BOTH
Signal mode: M5 EMA trend continuation
Risk reward: 0.60
Cost cap: cost_R <= 0.05
Blocked server hours: 0,2,4,9,10,11,12,16,19,20
Blocked LONG hours: 6,7,8
Blocked SHORT hours: 13,14,15,17,18
M5 trend EMA fast/slow: 8 / 21
M5 trend slope bars: 3
M5 trend min slope ATR: 0.03
M5 trend max distance ATR: 1.20
Min range ATR: 0.35
Min body fraction: 0.30
Long close location: 0.58
Short close location: 0.42
Min three-bar move ATR: 0.10
Max trades/day: 24
Cooldown minutes: 0
One position per magic: true
Max open positions per magic: 1
```

This lane increases active-day coverage. It is not strong enough alone to replace V4/V6, but portfolio stress shows it adds useful frequency when de-duplicated.

### Lane 3 - Short companion core

```text
Variant: freq_h1_h4_short_rr0p7_v1_core_1_5_15_19
Magic: 932222
Comment: A1_XAU_M5_MOM_DP_S
Direction: SHORT only
Signal mode: break-and-run
Risk reward: 0.70
Cost cap: cost_R <= 0.05
Allowed server hours: 1,2,3,4,5,15,19
Blocked server hours: 0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23
Max trades/day: 12
Cooldown minutes: 5
One position per magic: true
Max open positions per magic: 1
```

This lane adds short-side exposure but is weak in the older 2022-07 to 2024-06 OOS window when judged alone. It must be monitored as part of the portfolio, not promoted independently.

## Stress-test caveats

Stress report:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.md
```

The candidate survives top-winner removal strongly:

| Removed winners | Remaining net USD |
|---:|---:|
| 10 | +2013.41 |
| 25 | +1835.20 |
| 50 | +1562.40 |
| 100 | +1056.07 |

But the older two-year window is weaker:

| Window | Trades | WR | Net | PF | Active days | T/active |
|---|---:|---:|---:|---:|---:|---:|
| 2022-07 to 2024-06 | 1544 | 63.08% | +374.00 | 1.15 | 390 | 3.96 |
| 2024-07 to 2026-06 | 1514 | 68.43% | +1782.21 | 1.46 | 328 | 4.62 |

This is acceptable for review, but it must be treated as a forward-test risk.

## Forward-test rule

If approved, attach all three lanes together on A1 only at `0.01` lot. Score them as a portfolio after same-minute same-direction de-duplication.

Do not tune:

- signal modes,
- direction modes,
- hour masks,
- RR,
- cost cap,
- max trades/day,
- cooldown,
- max open positions.

## Kill rules

Stop the portfolio experiment if any condition occurs:

- rolling 100 closed deduped trades PF < 1.00,
- rolling 100 closed deduped trades win rate < 55%,
- net negative after 250 deduped trades,
- max closed drawdown exceeds `150 USD` at 0.01 lot,
- any single day contributes more than 30% of total positive net,
- duplicate-like same-minute same-direction overlap exceeds 8% after live forward logs,
- any non-A1 account is touched,
- any symbol other than XAUUSD is traded.

## Pass rules

The portfolio can be considered successful only after:

- at least 500 deduped forward trades,
- at least 8 forward weeks,
- win rate >= 58%,
- PF >= 1.25,
- net positive after removing top 25 winners,
- no single day contributes more than 25% of total net,
- both long and short sides remain non-negative or the weak side is explicitly quarantined by review.

## Required reviewer questions

1. Is the older-window PF 1.15 too weak for a forward test?
2. Is V6 max-two-position exposure acceptable at 0.01 lot, or should it be reduced to one position before forward testing even though that changes the tested candidate?
3. Does V13 add genuine active-day coverage or only dilute V6?
4. Should the short-core lane remain in the forward portfolio even though it is weak as a standalone OOS candidate?
5. Is the low raw duplicate-like overlap of 3.15% enough to say the portfolio is not fake stacking?

