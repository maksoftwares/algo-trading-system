# PHASE0_WAVE2_GATE_SET_V1 — locked before any Wave-2 run

Date: 2026-06-10
Author: Claude (independent technical reviewer, acting researcher under owner direction)
Status: LOCKED (SHA256 sidecar: PHASE0_WAVE2_GATE_SET_V1.sha256.json)

Applies to: the Wave-2 second-EA candidates registered after the 2026-06-10 campaign
(`xau_ny_morning_trend_pullback_v0`, `xau_comex_open_drive_continuation_v0`,
`xau_d1_trend_ny_window_continuation_v0`) and any later wave that references this file,
run on the locked full-per-broker windows (Capital.com and Dukascopy 2016-01-01 through
2025-06-30; Pepperstone owner-accepted partial 2019-2021; true holdout 2025-07-01 onward
untouched).

## Frequency-aware gate selection (locked rule)

Compute median trades per cell across the 9 executed cells.

1. If median trades/cell < 500 ("low-frequency"): apply `PHASE0_LOWFREQ_GATE_SET_V1`
   exactly as locked (G1-G10 including normalized G4, G7 cross-venue floor, G8 modern-era
   integrity, G9B realized measured cost).
2. Otherwise ("high-frequency"): apply the standard phase0.yaml gate set —
   G1 PF >= 1.30 in >= 7/9 cells; G2 >= 40 trades every cell; G3 max-DD/total-return caps;
   G4-ABS absolute concentration (largest trade <= 10% of PnL, top-5 <= 40% of PnL, and
   net_R > 0 in every cell); G5 zero-trade months <= 3; G6 p95-to-best PF ratio >= 0.50 —
   PLUS the venue/era robustness gates carried over from the campaign because their lessons
   are frequency-independent:
   G7 cross-venue floor: mean(Pepperstone PF, Dukascopy PF) >= 1.20 in every cost model;
   G8 modern-era integrity: 2022-2025-06-30 median-cost PF >= 1.10 in at least 2 of 3 brokers;
   G9B realized measured cost: realized median cost_R <= 0.15 preferred, realized p95
   cost_R <= 0.30 absolute.
3. In both branches the normalized concentration values (norm_top, norm_top5) are REPORTED
   for transparency; in the high-frequency branch the ABSOLUTE caps are the binding G4.

## Verdict rule (pre-committed)

All applicable gates PASS -> `PASS_MATRIX_GATES_ADVANCES_TO_DECILES_AND_D2` (deciles, D2
Reality Check with family clustering, intrabar ambiguity, and Gate-9 adversarial review are
still required before `PASS_APPROVED_FUTURE_EXPERT_CANDIDATE`). Any gate FAIL ->
`FAIL_REJECTED_VERSION_FINAL`, final for that version under NO_TUNING_RULES.md. Changing
this file after any Wave-2 result exists invalidates the wave.

## Rationale notes

The campaign's six rejections established: (a) the normalized-G4 calibration fix is correct
but PF persistence is the binding constraint; (b) single-broker and single-era evidence is
unreliable on this book (Capital.com vs Pepperstone disagree by 0.6+ PF on identical 2019-2021
years), so G7/G8 must bind at every frequency; (c) candidates designed outside the funded
NY-morning participation window have failed as a class. Wave 2 therefore targets in-window,
non-breakout mechanics, and this gate set closes the loophole where a high-frequency candidate
would otherwise escape the venue/era gates.
