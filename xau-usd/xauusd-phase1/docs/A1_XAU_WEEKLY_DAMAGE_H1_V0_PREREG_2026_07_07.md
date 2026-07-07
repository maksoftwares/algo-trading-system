# A1 XAU Weekly-Damage H1 V0 Preregistration

Date: 2026-07-07

## Goal

Test one new exact-MT5 source class intended to help the relaxed weekly-positive target. The prior diagnostics showed the current pool cannot reach 70% positive calendar weeks even with non-causal red-week selection, so this pass must be a genuinely new signal source rather than another weighting or gate over existing ledgers.

## Source Class

`weekly_damage_h1_v0`

The EA makes decisions only on completed H1 bars. It may use:

- previous completed W1 high/low;
- current broker-week H1 open/high/low up to the completed decision bar;
- Monday H1 range known by the decision bar;
- previous completed D1 ATR;
- the completed H1 decision candle.

It must not use future week labels, future weekly P&L, MT5 optimization, or post-result threshold edits.

## Fixed Variant Grid

Six cells only:

| Variant | Mode | Weekly extension | Target |
|---|---|---:|---:|
| `v14_weekly_damage_reversal_rr2_move10` | reversal | 1.0 D1 ATR | 2.0R |
| `v14_weekly_damage_reversal_rr15_move08` | reversal | 0.8 D1 ATR | 1.5R |
| `v14_weekly_damage_reversal_rr2_move12` | reversal | 1.2 D1 ATR | 2.0R |
| `v14_weekly_damage_continuation_rr2_move10` | continuation | 1.0 D1 ATR | 2.0R |
| `v14_weekly_damage_continuation_rr15_move08` | continuation | 0.8 D1 ATR | 1.5R |
| `v14_weekly_damage_continuation_rr2_move12` | continuation | 1.2 D1 ATR | 2.0R |

Shared settings: Wednesday-Friday only, H1 decision cadence, `MaxTradesPerDay=4`, `CooldownMinutes=60`, cost cap `0.08R`, risk-normalized `$10` per trade, max lots `0.05`.

## Evaluation

Run exact MT5 Strategy Tester on XAUUSD M5 from 2022-07-01 through 2026-06-30. After export, compute metrics from parsed deals/trade rows, not copied MT5 summary values.

Primary read:

- standalone WR, W/L, PF, net, active weekday %, positive calendar week %;
- overlap with current baseline red weeks;
- number of baseline-red weeks touched, flipped positive, and made worse;
- hybrid effect against the current best baseline, without retuning weights.

## Promotion Boundary

This pass cannot create a demo-ready strategy. Best possible outcome is a watchlist source if it materially improves positive weeks toward 70% without collapsing payoff. Reviewer token is reserved unless a result is near the owner target or reveals a methodology issue.

## V14B Failure-Anatomy Follow-Up

After the six-cell V14 pass, one bounded diagnostic follow-up is permitted: split the reversal source by direction only. This is not a promotion grid and must not add hour masks, new thresholds, or continuation variants.

Allowed V14B cells:

| Variant | Mode | Direction | Weekly extension | Target |
|---|---|---|---:|---:|
| `v14b_weekly_damage_reversal_rr2_move10_long_only` | reversal | long-only | 1.0 D1 ATR | 2.0R |
| `v14b_weekly_damage_reversal_rr2_move10_short_only` | reversal | short-only | 1.0 D1 ATR | 2.0R |
| `v14b_weekly_damage_reversal_rr15_move08_long_only` | reversal | long-only | 0.8 D1 ATR | 1.5R |
| `v14b_weekly_damage_reversal_rr15_move08_short_only` | reversal | short-only | 0.8 D1 ATR | 1.5R |

Decision rule: if the direction split does not materially improve hybrid positive calendar weeks beyond V14 while reducing red-week worsening, freeze the weekly-damage H1 source class.
