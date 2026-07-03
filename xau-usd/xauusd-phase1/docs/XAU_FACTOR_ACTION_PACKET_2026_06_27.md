# XAU Factor Action Packet

Date: 2026-06-27

## Decision

Do not deploy a runtime filter yet.

Do approve a shadow-only forward test for the XAU evening trend-alignment
hypothesis if the owner/reviewer accepts the evidence boundary.

## Why

The broker-joined analysis matched 148 of 161 realized XAU breakout fills to
available factor rows using account, direction, and time proximity.

The proposed evening + trend-aligned slice is positive, but the historical
sample is only 8 realized fills:

| Slice | Trades | Win rate | PnL AED | PF |
|---|---:|---:|---:|---:|
| All joined breakout fills | 148 | 43.2% | +729.45 | 1.34 |
| Evening only | 56 | 51.8% | +794.88 | 2.10 |
| Trend aligned only | 9 | 44.4% | +112.27 | 1.79 |
| Evening + trend aligned | 8 | 50.0% | +157.79 | 2.62 |

The strict slice is too small to deploy. It is large enough to justify a
forward-test tag.

## Owner-Action Choice

Record one of these:

```text
APPROVE_SHADOW_FORWARD_TEST
DECLINE_SHADOW_FORWARD_TEST
```

Approval does not authorize any MT5 runtime change.

## Forward-Test Rule

For future XAUUSD breakout-retest-family would-signals, mark `TAKE` only when:

```text
Dubai time: 16:00-19:59
d1_trend_score_aligned >= 0.25
h1_ema20_slope_aligned_atr >= 0.35
```

All other signals are marked `SKIP`.

## How To Score It

Refresh the read-only C02 data, rebuild labels/features, then rerun:

```powershell
.\.venv\Scripts\python.exe scripts\broker_join_factor_action_plan.py
```

If the venv is not active, use the bundled Python path already used by Codex.

Primary files:

```text
outputs/reports/BROKER_JOINED_FACTOR_ACTION_PLAN_2026_06_27.md
outputs/reports/BROKER_JOINED_XAU_FACTOR_ROWS_2026_06_27.csv
docs/XAU_EVENING_TREND_ALIGNMENT_FORWARD_TEST_V0_2026_06_27.md
```

## Pass Criteria

Do not judge before at least:

```text
150 broker-joined forward trades
or 6 full weeks,
whichever comes later.
```

Promotion requires:

```text
PF >= 1.25
positive after removing top 3 winners
no single day > 35% of net profit
both A1 and clean-control evidence not materially conflicting
```

## Kill Criteria

Stop the hypothesis if any of these happens:

```text
rolling 50-trade PF < 0.90
any single day > 50% of cumulative net
second-half PF more than 0.30 below first-half PF
only A1 works while A2/A3 or clean-control remains negative
```

## What This Lets Us Act On

We can now act without guessing:

1. Keep current runtime unchanged.
2. Start scoring the exact trend-aligned evening hypothesis in shadow.
3. Use broker-joined realized fills as the judge.
4. Reject or promote later from forward evidence, not from the same historical
   sample that produced the idea.

