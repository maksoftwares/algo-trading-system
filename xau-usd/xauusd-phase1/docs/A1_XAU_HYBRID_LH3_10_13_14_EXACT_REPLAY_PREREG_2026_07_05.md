# A1 XAU Hybrid LH3/10/13/14 Exact Replay Preregistration

Date: 2026-07-05

## Purpose

Replay the best current diagnostic hybrid in exact MT5 Strategy Tester before spending reviewer tokens.

The diagnostic frontier was:

- Portfolio: `freq_step3_frontier + split_high_payout_f33_r30_be_never + h4_d1_long_best_box2_atr80 + h4_d1_long_broad_box3_atr60`
- Additional blocked LONG server hours: `3,10,13,14`
- Diagnostic metrics: WR `50.03%`, W/L `2.051`, active weekdays `86.10%`

## Frozen Inputs

Replay these exact component definitions with `InpBlockedLongEntryHoursCsv` unioned with `3,10,13,14`:

1. `goal_split_f67_r20_be_tp1_v6`
2. `goal_split_f67_r20_be_tp1_v13`
3. `goal_split_f67_r20_be_tp1_weak`
4. `v8_compress_h1_long_rr2p0`
5. `orrev_london_firm_stop15`
6. `goal_split_f33_r30_be_never_v6`
7. `goal_split_f33_r30_be_never_v13`
8. `goal_split_f33_r30_be_never_weak`
9. `long_box2_atr80_range150_body035`
10. `long_broad_box3_atr60_range125_body035`

Period: `2022.07.01` through `2026.06.30`.

Tester: isolated MT5 root `C:\MT5A1M5MomentumBacktest`, Strategy Tester only, `XAUUSD`, `M5`, every tick, USD deposit/currency.

## Composition Rules

1. Split-entry variants are collapsed to signal level by `(entry_time, direction)`, summing ticket P&L.
2. Step1 split families keep their original internal priority: `v6` first, `weak` second, `v13` third, using the existing 4-minute within-cell dedupe rule.
3. Build `freq_step3_frontier` from:
   - Step1 `f67_r20_be_tp1`, priority `12`, family `a1_core_management`
   - `v8_compress_h1_long_rr2p0`, priority `101`, family `rr2_trend_stretch`
   - `orrev_london_firm_stop15`, priority `250`, family `opening_range_reversal_exam`
4. Treat the kept `freq_step3_frontier` as one source with priority `10` for final hybrid composition.
5. Add:
   - Step1 `f33_r30_be_never`, priority `11`, family `a1_core_management`
   - `h4_d1_long_best_box2_atr80`, priority `80`, family `h4_d1_core_shape`
   - `h4_d1_long_broad_box3_atr60`, priority `81`, family `h4_d1_core_shape`
6. Final dedupe uses the existing 5-minute same-direction cross-source dedupe from Step3.

## Decision Rule

- `EXACT_OWNER_GOAL_HIT_REVIEW_REQUIRED`: WR >= 50%, W/L >= 2.0, active weekdays >= 90%, net > 0.
- `EXACT_CORE_NEAR_ACTIVITY_REVIEW_CANDIDATE`: WR >= 50%, W/L >= 2.0, active weekdays >= 85%, net > 0.
- Anything weaker remains frontier context only and should not consume reviewer tokens.

No demo spec, runtime attach, or live action is allowed from this replay alone.
