# A1 XAU M5 V7/V8/V11/V13 RR2 Stretch Probe Preregistration

Generated: 2026-07-05

## Objective

Run a small exact-MT5 owner-goal probe on entry families that were not part of the rejected V9/V10 RR2 stretch packet.

Owner core target:

- Signal/trade win rate >= 50%
- Realized average win / average loss >= 2.0
- Daily activity target remains 90%+ active market days worth showing only if the core shape hits

## Boundary

Use exact MT5 Strategy Tester in isolated root `C:\MT5A1M5MomentumBacktest`.

No live/demo runtime attachment is allowed. Python may only compile/run the tester and manually aggregate exported MT5 trade CSVs.

No reviewer token is spent unless exact MT5 reaches WR >= 50% and realized W/L >= 2.0.

## Frozen Variants

Each row inherits the existing frequency-first variant inputs and changes only `InpRiskReward` to `2.00`.

| Probe variant | Base variant | Family |
| --- | --- | --- |
| `v7_pullback_h1_long_rr2p0` | `v7_pullback_h1_long_rr0p6` | M5 EMA20 pullback continuation |
| `v8_compress_h1_long_rr2p0` | `v8_compress_h1_long_rr0p6` | M5 compression expansion |
| `v11_ema_trend_h1_long_rr2p0` | `v11_ema_trend_h1_long_rr0p6` | M5 EMA trend continuation |
| `v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning` | `v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning` | V13 directional EMA trend mask |

## Period

Exact exam window: `2022.07.01 -> 2026.06.30`.

## Acceptance

- `OWNER_GOAL_HIT_REVIEW_REQUIRED`: WR >= 50%, W/L >= 2.0, and active days >= 90%.
- `CORE_SHAPE_HIT_FREQUENCY_GAP`: WR >= 50% and W/L >= 2.0 but active days < 90%.
- Otherwise reject and do not spend reviewer.

## Anti-Overfit Boundary

This is a four-row fixed-family stretch. No optimization, no threshold sweep, no post-result hour/direction filtering.
