# A1 XAU Event-Reaction New-Class Preregistration

Date: 2026-07-07

Status: `PREREG_ONLY_NO_MT5_RUN_YET`

## Purpose

This is the next admissible research branch after the anti-overfit decision matrix.

It is not another mask over the current A1 XAU trade pool. It is a genuinely different candidate source: trade the post-event GOLD reaction itself.

## Why This Is Different

Closed work already tested:

- current A1 exact-ledger recombinations;
- weekly-state gates;
- V14 weekly-damage H1;
- V15 prior-day levels;
- V16 Asian-range activity;
- simple source/hour/weekday risk-off blocks;
- news hygiene as a blocker over existing trades.

This proposed branch is different because it creates new entries around scheduled macro-event volatility, instead of filtering or resizing the existing A1 entries.

## Hypothesis

Baseline red weeks are often caused by large directional/tail events, especially H4/D1-dominated loss weeks. A post-event reaction source may contribute independent trades during those same volatile weeks.

The source should be judged by red-week complementarity first, not standalone PF alone.

## Calendar Boundary

Acceptance requires a real historical event calendar with provenance.

Calendar provenance update: `A1_XAU_EVENT_REACTION_CALENDAR_202207_202606_PROVENANCE.md` froze an official-provenance calendar for the first implementation pass. BLS NFP/CPI rows are parsed from official BLS release-calendar pages; FOMC rows are parsed from the official Federal Reserve FOMC calendar. Calendar CSV SHA256 is recorded in the manifest.

Allowed for rejection-only smoke design:

- deterministic approximations such as NFP first Friday, CPI second Wednesday, and FOMC scheduled Wednesday windows;
- MT5 broker timestamps treated consistently but disclosed as provisional.

Not allowed for acceptance:

- approximate event dates;
- missing event release time provenance;
- post-hoc event selection after results are known.

Before any demo-forward consideration, the event calendar must be frozen with:

- event name;
- release datetime in UTC;
- source/provenance;
- SHA256 of the calendar CSV;
- timezone conversion rule to broker server time.

## Fixed First-Pass Cells

Only these six cells are admissible for a first exact-MT5 run.

| Cell | Event set | Mode | Entry window | Target | Stop |
|---|---|---|---|---|---|
| `event_impulse_nfp_rr2` | NFP | impulse continuation | 5-60 minutes after release | `2.0R` | event-window swing |
| `event_fade_nfp_rr2` | NFP | first-spike fade | 15-90 minutes after release | `2.0R` | spike extreme + buffer |
| `event_impulse_cpi_rr2` | CPI | impulse continuation | 5-60 minutes after release | `2.0R` | event-window swing |
| `event_fade_cpi_rr2` | CPI | first-spike fade | 15-90 minutes after release | `2.0R` | spike extreme + buffer |
| `event_impulse_fomc_rr2` | FOMC | impulse continuation | 5-90 minutes after release | `2.0R` | event-window swing |
| `event_fade_fomc_rr2` | FOMC | first-spike fade | 30-150 minutes after release | `2.0R` | spike extreme + buffer |

No hour tuning, event-subtype tuning, lower-R tuning, or direction-only split is allowed in the first pass.

## Entry Definitions

Impulse continuation:

1. Wait for the first completed M5 bar after the event.
2. Define the event impulse range as the high/low from release time through the first 15 minutes.
3. Long if a completed M5 bar closes above the impulse high by at least `0.10 * ATR14(M5)`.
4. Short if a completed M5 bar closes below the impulse low by at least `0.10 * ATR14(M5)`.
5. Skip if both directions trigger on the same completed bar.

First-spike fade:

1. Define the event spike range from release time through the first 15 minutes for NFP/CPI, and first 30 minutes for FOMC.
2. Long if price sweeps below the spike low and closes back inside the spike range.
3. Short if price sweeps above the spike high and closes back inside the spike range.
4. Require the reclaim bar body fraction `>=0.35`.
5. Skip if both directions trigger on the same completed bar.

Common rules:

- one trade per event per cell;
- no same-cell re-entry;
- fixed `0.01` lot for tester comparability;
- target `2.0R`;
- no partials, no profit-lock, no current-family portfolio state;
- no use of baseline red-week labels in entry logic.

## Evaluation

Headline evidence must come from exact MT5 Strategy Tester.

Report all of:

- standalone trades, WR, W/L, PF, net USD, max closed drawdown;
- baseline-composed WR, W/L, activity, stress W/L;
- positive calendar weeks;
- baseline red weeks touched;
- baseline red weeks flipped;
- baseline red weeks worsened;
- worst calendar week;
- June 2026;
- top-5, top-10, and top-20 winner removal.

## Kill Rules

Stop the branch after the first pass if:

- no cell has at least `100` trades over `2022-07-01 -> 2026-06-30`;
- no cell is standalone profitable with W/L `>=1.8`;
- composed positive weeks do not exceed `62%`;
- any apparent improvement comes with W/L below `1.8`;
- top-10 winner removal flips the cell materially negative.

Watchlist-only threshold:

- composed positive weeks `>=65%`;
- composed W/L `>=1.8`;
- activity not worse than the current baseline;
- top-10 winner removal stays positive or near-flat;
- event-calendar provenance gap disclosed.

Serious-review threshold:

- composed positive weeks `>=70%`;
- composed W/L `>=1.8`;
- no severe worst-week deterioration;
- real event calendar provenance frozen;
- reviewer signs off before any demo spec.

## Current Decision

Do not code or run this yet if the reviewer token will be used immediately.

If reviewer token is being saved, this is the cleanest next class to implement because it is materially different from the exhausted A1 pool and has a falsifiable first-pass budget. With the official event calendar now frozen, the next engineering step is exact-MT5 implementation of the six fixed cells, not further premise tuning.
