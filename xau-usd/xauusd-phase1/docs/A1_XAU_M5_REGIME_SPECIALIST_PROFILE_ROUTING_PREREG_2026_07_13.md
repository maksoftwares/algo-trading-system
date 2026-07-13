# A1 XAU M5 Pre-existing Profile Routing Preregistration

Date: `2026-07-13`

Status: `FROZEN_BEFORE_TERTIARY_MT5_EXECUTION`

## Purpose

The first two frozen regime campaigns found no candidate that met every
five-year screen gate. This bounded phase tests whether the strongest M5
profiles selected by the earlier V4, V12, and V13 studies retain their edge
when they are assigned to one strict Router V1 regime.

No setting below was derived from the first or second regime-campaign results.
Each signal, direction, exit, hour mask, and entry threshold is copied from a
pre-existing named profile. The only new input is the fail-closed regime owner.

## Frozen common contract

- Symbol/timeframe: `XAUUSD / M5`
- Screen window: `2021-07-01` through `2026-07-01`
- MT5 model: every tick; native history quality required `>=98%`
- Deposit/currency: `$1,000 USD`
- Size: fixed `0.01 lot`
- One same-magic position maximum
- Profile-specific target, hour mask, daily cap, and cooldown are preserved
- Maximum spread: `75 points`
- Router data failure is no-trade; SHOCK is always no-trade

## Frozen candidates

| Regime | Candidate | Exact pre-existing source profile |
|---|---|---|
| R1 UPTREND | `r1_v4_break_run_long` | `freq_h1_h4_long_rr0p7_v4_combo_rank1` |
| R1 UPTREND | `r1_v13_ema_long` | `v13_ema_trend_h1h4_long_rr0p6_no_morning` |
| R2 DOWNTREND | `r2_v13_ema_short` | `v13_ema_trend_h1h4_short_rr0p6_core` |
| R2 DOWNTREND | `r2_v13_feature_loss_short` | `v13_feature_loss_short_extreme_rr0p6` |
| R3 COMPRESSION | `r3_v13_ema_both` | `v13_ema_trend_h1h4_both_rr0p7_no_weak_short` |
| R3 COMPRESSION | `r3_v12_ema_both` | `v12_ema_trend_h1h4_both_rr0p6_block_bad_hours` |
| R4 CHOP | `r4_v13_ema_both` | `v13_ema_trend_h1h4_both_rr0p7_no_weak_short` |
| R4 CHOP | `r4_v12_ema_both` | `v12_ema_trend_h1h4_both_rr0p6_block_bad_hours` |

## Frozen five-year screen gates

- Trades `>=100`
- Profit factor `>=1.20`
- Win rate `>=35%`
- Net profit `>0`
- MT5 relative equity drawdown `<=20%`
- History quality `>=98%`

Every five-year survivor must be rerun unchanged on `2016-07-01` through
`2026-07-01`. A regime is only called found if that untouched ten-year result
also passes the same gates. SHOCK is considered successfully handled only by
the capital-protection/no-trade policy.

This is research authorization only, not demo/live or deployment authorization.
