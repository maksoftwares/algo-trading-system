# A1 XAU Prior-Day Level M5 V15 Preregistration

Date: 2026-07-07

## Goal

Test one distinct exact-MT5 source class after V14 weekly-damage H1 failed to move the relaxed weekly-positive target. This is not a V14 continuation. It uses prior completed D1 high/low levels and completed M5 candles only.

## Source Class

`prior_day_level_m5_v15`

Allowed information:

- prior completed D1 high/low;
- completed M5 decision candle;
- M5 ATR;
- fixed server-hour window `06:00 -> 22:00`.

No optimizer, no hour-mask expansion, no post-result threshold edits.

## Fixed Grid

| Variant | Mode | Main threshold | Target |
|---|---|---:|---:|
| `v15_prior_day_level_cont_rr2_break10` | continuation | 0.10 M5 ATR break | 2.0R |
| `v15_prior_day_level_cont_rr15_break05` | continuation | 0.05 M5 ATR break | 1.5R |
| `v15_prior_day_level_reversal_rr2_reclaim10` | reversal | 0.10 M5 ATR reclaim | 2.0R |
| `v15_prior_day_level_reversal_rr15_reclaim05` | reversal | 0.05 M5 ATR reclaim | 1.5R |

Shared settings: risk-normalized `$10`, max lots `0.05`, cost cap `0.08R`, max trades/day `8`, cooldown `15m`.

## Decision Rule

Freeze this source unless it materially improves hybrid positive weeks beyond V14 while preserving a plausible payoff shape. A standalone profitable row is not enough if it does not move the weekly target.

## V15B Direction-Split Follow-Up

After V15, one bounded failure-anatomy follow-up is permitted: split the two 1.5R rows by direction only.

Allowed V15B cells:

| Variant | Mode | Direction | Target |
|---|---|---|---:|
| `v15b_prior_day_level_cont_rr15_long_only` | continuation | long-only | 1.5R |
| `v15b_prior_day_level_cont_rr15_short_only` | continuation | short-only | 1.5R |
| `v15b_prior_day_level_reversal_rr15_long_only` | reversal | long-only | 1.5R |
| `v15b_prior_day_level_reversal_rr15_short_only` | reversal | short-only | 1.5R |

No additional thresholds, session masks, or feature gates are allowed in this pass.
