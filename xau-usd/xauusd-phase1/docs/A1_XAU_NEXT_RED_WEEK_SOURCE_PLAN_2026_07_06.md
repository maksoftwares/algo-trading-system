# A1 XAU Next Red-Week Source Plan

Date: 2026-07-06

Status: `NEXT_ITERATION_PLAN_NO_REVIEWER_SPEND`

## Current Evidence

The current exact-ledger frontier is profitable but not demo-ready:

- WR `50.23%`
- W/L `2.0002`
- active weekdays `86.39%`
- positive calendar weeks `54.29%`
- stress `-0.30/ticket` W/L `1.9029`

The relaxed weekly target is still far away:

- `70%` positive weeks requires `147/210` positive weeks.
- Current baseline has `114/210`.
- Required flip count for `70%`: `33` red weeks.
- Required flip count for `80%`: `54` red weeks.

## Closed Paths

Do not spend more time on these without a genuinely new reviewer idea:

- more H4/D1 stop caps, early-adverse exits, or partial ladders;
- weighting the current smooth second-book archive;
- current-week closed-P&L add-on gates over the current pool;
- previous-red-week add-on gates over the current pool;
- baseline risk-off gates over the current pool;
- existing `InpSignalMode` inventory `0-11` as a source of an untouched shortcut.

The current-pool red-week oracle is the key proof: even with future knowledge of baseline red weeks, it topped out at `65.24%` positive weeks and `88.59%` active weekdays. That means we are not missing only a classifier; the current trade pool itself lacks enough correctly timed red-week rescue power.

## Next Source Requirements

The next candidate must be a genuinely new source, not a recombination of the current pool.

Hard requirements for a useful first pass:

- It must overlap baseline red weeks enough to plausibly flip at least `33` weeks.
- It must not rely on low-R filler that drags portfolio W/L below `2.0`.
- It must be expressible as exact MT5 Strategy Tester logic before review.
- It must be evaluated against the existing baseline by exit-time calendar weeks.
- It should report red-week overlap directly: baseline-red weeks touched, baseline-red weeks flipped, and weeks made worse.

## Proposed Next Probe

Build one small, preregistered exact-MT5 source focused on red-week timing rather than broad activity:

`weekly_damage_reversal_or_continuation_v0`

Fixed design idea:

- Decision cadence: completed H1 or M30 bars, not M5 noise.
- Trade window: Wednesday-Friday only, where most week outcome rescue is still possible.
- Market state: current week must have meaningful directional extension from Monday open or prior-week level.
- Entry premise: rejection/reclaim of prior week high/low, Monday range edge, or current-week extreme after an H1/M30 rejection candle.
- Target shape: fixed `2.0R` first; only test lower R after the 2R source fails explicitly.
- Anti-overfit boundary: no hour/session tuning in first pass; at most 6 fixed cells covering direction and one structural threshold.

The first pass should be judged by:

- standalone WR/W-L/PF/sample;
- baseline-composed WR/W-L/activity;
- positive calendar weeks;
- red-week flips and red-week worsening;
- top-winner removal;
- June 2026 and worst-week behavior.

## Reviewer Use

Do not spend the daily reviewer token before the first exact-MT5 result. Ask for review only if a new source reaches one of these:

- `>=65%` positive calendar weeks with no severe W/L dilution;
- or `>=70%` positive calendar weeks in a diagnostic/exact result;
- or a genuinely new methodology question appears before running the exact probe.
