# A1 XAU Hybrid F67 Hour-16 Exact Repair Preregistration

Date: 2026-07-05

## Purpose

Run one tiny exact-MT5 repair on the current best verified frontier:

- Baseline exact replay: `A1_XAU_HYBRID_LH3_10_13_14_EXACT_REPLAY_202207_202606`
- Baseline metrics: `3847` signals, WR `50.09%`, W/L `1.9859`, active weekdays `86.39%`
- Defect: W/L missed `2.0` by `0.0141`; active weekdays remained below `90%`

## Frozen Diagnostic Trigger

The exact kept-ledger diagnostic found only one simple one-cut causal exclusion that crossed the WR/W-L core while retaining at least `85%` active weekdays:

- Exclude `step1_f67_r20_be_tp1` entries at server hour `16`
- Diagnostic result on existing exact kept ledger: `3758` signals, WR `50.11%`, W/L `2.0101`, active weekdays `86.39%`, PF `2.0328`

This diagnostic is not a headline claim. The changed source must be replayed in MT5.

## Exact Replay Scope

Rerun only the three affected f67 exact-MT5 components:

1. `f67_v6_lh`
2. `f67_weak_lh`
3. `f67_v13_lh`

Input changes:

- Preserve existing LH replay inputs, including `InpBlockedLongEntryHoursCsv=3,10,13,14`
- Add server hour `16` to `InpBlockedEntryHoursCsv` for these f67 components only, blocking both directions at that hour

The other seven component ledgers remain unchanged from the prior exact replay:

- `f33_v6_lh`
- `f33_weak_lh`
- `f33_v13_lh`
- `v8_lh`
- `orrev_london_lh`
- `h4_box2_lh`
- `h4_broad_lh`

Period: `2022.07.01` through `2026.06.30`.

Tester: isolated MT5 root `C:\MT5A1M5MomentumBacktest`, Strategy Tester only, `XAUUSD`, `M5`, every tick, USD deposit/currency.

## Composition Rules

Use the exact same composition as the LH3/10/13/14 replay:

1. Collapse split-entry tickets to signal level by `(entry_time, direction)`.
2. Apply Step1 split internal priority within each cell.
3. Build `freq_step3_frontier` from f67 + v8 + opening-range reversal.
4. Treat `freq_step3_frontier` as one source in the final hybrid.
5. Add f33 high-payout and H4/D1 long sources.
6. Apply existing 5-minute same-direction cross-source dedupe.

## Decision Rule

- `EXACT_OWNER_GOAL_HIT_REVIEW_REQUIRED`: WR >= 50%, W/L >= 2.0, active weekdays >= 90%, net > 0.
- `EXACT_CORE_NEAR_ACTIVITY_REVIEW_CANDIDATE`: WR >= 50%, W/L >= 2.0, active weekdays >= 85%, net > 0.
- Anything weaker remains frontier context only.

No demo spec, runtime attach, or live action is allowed from this replay alone.
