# A1 XAU Hybrid Long-Hour Payout Repair Diagnostic Preregistration

Generated UTC: `2026-07-05`

## Purpose

Test whether the current closest high-cadence Gold frontier can cross realized W/L `2.0` using an exact-MT5-implementable long-hour block list.

## Boundary

- Source evidence: existing exact MT5 Strategy Tester trade/signal CSVs only.
- No MT5 launch in this diagnostic.
- No live/demo runtime attach.
- No broker state changes.
- Any hit remains diagnostic until affected exact MT5 components are rerun with the same `InpBlockedLongEntryHoursCsv` settings.

## Fixed Portfolio

`wr_rank16` from the hybrid frontier:

- `freq_step3_frontier`
- `split_high_payout_f33_r30_be_never`
- `h4_d1_long_best_box2_atr80`
- `h4_d1_long_broad_box3_atr60`

## Fixed Repair Search

Use only the MT5-supported `InpBlockedLongEntryHoursCsv` idea. The diagnostic blocks LONG entries by server hour before signal-level dedupe.

Seed sets come from the prior categorical diagnostic:

- `{3, 13}`
- `{3, 14}`

For each seed, add zero, one, or two extra LONG-blocked hours from the remaining server-hour set. Maximum total blocked LONG hours: `4`.

No PnL, future, drawdown, or outcome-derived field is allowed as a gate input.

## Floors And Decisions

Minimum retained signals: `3500`.

- `DIAGNOSTIC_OWNER_HIT_EXACT_REPLAY_REQUIRED`: WR >= 50%, W/L >= 2.0, active weekdays >= 90%, PF >= 1.30, net > 0.
- `DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED`: WR >= 50%, W/L >= 2.0, active weekdays >= 85%, PF >= 1.30, net > 0.
- `DIAGNOSTIC_NEAR_PAYOUT_NO_REVIEW`: WR >= 50%, W/L >= 1.95, active weekdays >= 85%, PF >= 1.30, net > 0.
- Otherwise reject this repair branch.

Report last-12-month metrics and +$0.10/+$0.30 per-ticket stress for the top rows.
