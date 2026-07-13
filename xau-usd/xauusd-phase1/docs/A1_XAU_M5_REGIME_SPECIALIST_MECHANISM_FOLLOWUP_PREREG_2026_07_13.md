# A1 XAU M5 Missing-Regime Mechanism Follow-up Preregistration

Date: `2026-07-13`

Status: `FROZEN_BEFORE_MECHANISM_FOLLOWUP_MT5_EXECUTION`

## Evidence entering this phase

- R2/DOWNTREND has two ten-year screen passes and is excluded.
- R1/UPTREND has profitable, controlled-DD M5 profiles but best PF is `1.17`,
  below the frozen `1.20` gate.
- R3/COMPRESSION rejects high-frequency EMA-trend continuation.
- R4/CHOP rejects EMA-trend continuation with unacceptable losses and DD.
- SHOCK remains capital-protection/no-trade.

## Frozen candidates

All rows use Router V1 as the sole regime owner and copy every signal, exit,
direction, threshold, and hour mask from a named profile selected before this
regime campaign.

| Regime | Candidate | Pre-existing mechanism/profile |
|---|---|---|
| R1 | `r1_router_v3_break_run_long` | higher-PF V3 break/run: `freq_h1_h4_long_rr0p7_v3_block3_8` |
| R1 | `r1_router_v13_rr0p7_long` | 0.7R V13 trend: `v13_ema_trend_h1h4_both_rr0p7_no_weak_short` |
| R3 | `r3_router_v8_compression_long` | true M5 compression expansion: `v8_compress_h1_long_rr0p6` |
| R3 | `r3_router_v4_break_run_long` | M5 break/run release: `freq_h1_h4_long_rr0p7_v4_combo_rank1` |
| R4 | `r4_router_v9_sweep_long` | M5 sweep/reclaim: `v9_sweep_h1_long_rr0p6` |
| R4 | `r4_router_v9_sweep_v4mask_long` | masked M5 sweep/reclaim: `v9_sweep_h1h4_long_rr0p6_v4mask` |

## Frozen validation

Five-year window `2021-07-01` through `2026-07-01`; XAUUSD M5; MT5 every
tick; `$1,000 USD`; fixed `0.01 lot`; one position; native quality `>=98%`.

Pass every gate: trades `>=100`, PF `>=1.20`, win rate `>=35%`, net `>0`,
and relative equity drawdown `<=20%`.

Any survivor is rerun unchanged on `2016-07-01` through `2026-07-01`. This is
research evidence only, not demo/live or deployment authorization.
