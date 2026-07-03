# A1 XAU M5 Momentum Frequency-First V4 Combo Rank1 Verdict - 2026-07-02

Status: `REVIEW_READY_FREQUENCY_FIRST_V4_CANDIDATE_NOT_PROMOTED`

This tracked document mirrors the generated V4 verdict so reviewers can inspect the candidate from the repository even when `outputs/reports/**` is ignored.

## Candidate

`freq_h1_h4_long_rr0p7_v4_combo_rank1`

Mechanical shape:

- XAUUSD M5 momentum continuation.
- LONG-only.
- H1 and H4 EMA trend alignment required.
- Target: `0.7R`.
- Estimated cost cap: `cost_R <= 0.05`.
- Blocked server hours: `2,9,10,11,12,13,17,19,21,23`.
- Allowed server hours: `0,1,3,4,5,6,7,8,14,15,16,18,20,22`.
- Max trades/day: `12`.
- Cooldown: `5` minutes.

## Exact MT5 Results

| Window | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months | Net after Top 10 Removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022.07-2024.06 older OOS | 520 | 65.00% | +309.24 | 1.40 | 179 | 2.91 | 17 | 6 | +210.19 |
| 2024.07-2026.06 recent | 612 | 66.67% | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 | +604.50 |
| 2022.07-2026.06 combined | 1132 | 65.90% | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | +899.51 |

## Why It Supersedes V3 For Review

| Variant | Trades | Win Rate | Net USD | PF | Active Days | Avg Trades / Active Day | Comment |
|---|---:|---:|---:|---:|---:|---:|---|
| `freq_h1_h4_long_rr0p7_v3_block3_8` | 925 | 66.81% | +988.26 | 1.53 | 346 | 2.67 | Higher PF/win rate, lower cadence |
| `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 1132 | 65.90% | +1042.07 | 1.45 | 383 | 2.96 | Better fit for frequency-first owner objective |

V3 remains a fallback if the reviewer prioritizes PF over cadence. V4 is the primary review target because it more closely matches the owner's desired shape: frequent active-day trades, >50% WR, positive expectancy, and old/current split stability.

## Short-Companion Result

No combined long+short mask cleared the strict split-stability floor. Short-side variants were strong in the recent window but failed the older OOS split. They remain diagnostic-only and should not be attached with V4.

Tracked companion note: `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SHORT_COMPANION_DIAGNOSTIC_2026_07_02.md`.

## Decision

V4 is `REVIEW_READY`, not promoted. Next step:

1. Independent review of source CSVs, hour-mask provenance, and exact MT5 reruns.
2. If accepted, owner-approved minimum-lot demo forward test.
3. If forward tested, replace the sparse RR2 lane rather than stack both lanes.

## Local Generated Artifacts

- Generated verdict: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md`
- OOS V4 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V4_OOS_2022_07_2024_06.md`
- Recent V4 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V4_CURRENT_2024_07_2026_06.md`
- Four-year V4 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V4_FOUR_YEAR_2022_07_2026_06.md`
- Hour-combination search: `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.md`

