# A1 XAU Weekly90 Progress Status

Date: 2026-07-06

## Current Best Baseline

Current best exact-MT5 hybrid remains `A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606`.

Measured by closed signal P&L grouped on final `exit_time`, not entry date:

| Signals | WR% | W/L | Active% | PF | Net | Max DD | Stress -0.30/ticket W/L | Positive weeks% | Worst week | Rolling 4w+% | June 2026 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1583.72 | 1.9029 | 54.81 | -878.18 | 63.41 | -599.56 |

Status: profitable research frontier, not demo-ready.

## What Improved Today

1. Added exit-time weekly anatomy so weekly results are measured by closed P&L:
   - report: `outputs/reports/A1_XAU_HYBRID_WEEKLY_EXIT_ANATOMY_202207_202606.md`
   - result: weekly shape is worse than entry-date view and H4/D1 dominates both best weeks and worst loss clusters.

2. Added a default-off EA input:
   - `InpStopCapPoints=0`
   - purpose: cap effective stop distance before cost-R, SL/TP, and lot sizing are calculated.
   - default `0` preserves existing behavior.

3. Preregistered and ran six exact-MT5 H4/D1 geometry-v2 cells:
   - report: `outputs/reports/A1_XAU_H4_D1_GEOMETRY_V2_WEEKLY_SHAPE_202207_202606.md`
   - prereg SHA256: `24d0280b250ccc325b3c791340fc8088e3be4336156307dc4db40c6aee379f85`

4. Preregistered and ran four exact-MT5 H4/D1 partial-ladder cells after adding position-ID deal logging:
   - report: `outputs/reports/A1_XAU_H4_D1_PARTIAL_LADDER_EXACT_PROBE_202207_202606.md`
   - best weekly row: `p33_t2_run4_be`, WR `50.08%`, W/L `1.9213`, stress W/L `1.8106`, positive weeks `57.21%`, June 2026 `+164.14`
   - result: `NO_PARTIAL_LADDER_SURVIVOR`

5. Ran a smooth second-book weekly target diagnostic across existing exact-MT5 ledgers, reconstructed causal residual packages, top causal coverage candidates, all 42 loaded exact-MT5 individual variants, and fixed second-book sizing weights from `0.5x` to `10x`:
   - report: `outputs/reports/A1_XAU_SMOOTH_SECOND_BOOK_WEEKLY_TARGET_DIAGNOSTIC_202207_202606.md`
   - best 90% activity blend: `baseline_plus_causal_top01_target75_cooldown10_sized_x0p5`, active weekdays `90.22%`, positive calendar weeks `54.29%`, WR `54.21%`, W/L `1.5950`, stress W/L `1.4897`
   - best standalone weekly ceiling: causal coverage book at `61.90%` positive weeks, but only `52.64%` active weekdays and W/L about `0.68`
   - result: `NO_70_80_WEEKLY_HIT`

6. Ran a causal weekly-state red-week rescue diagnostic using current-week closed baseline P&L, previous red-week state, and risk-off gates:
   - report: `outputs/reports/A1_XAU_WEEKLY_STATE_RED_WEEK_RESCUE_DIAGNOSTIC_202207_202606.md`
   - best row: `baseline_plus_causal_top01_target75_cooldown10_cwdn25_x5p0`, positive calendar weeks `58.10%`, active weekdays `87.63%`, WR `50.99%`, W/L `1.7767`, stress W/L `1.6997`
   - rows tested: `760`; rows reaching `>=70%` positive weeks: `0`; rows reaching `>=90%` activity: `0`
   - non-causal red-week oracle upper bound: best current-pool oracle row reached only `65.24%` positive weeks and `88.59%` active weekdays, so the existing pool lacks enough red-week rescue power even with future knowledge
   - result: `NO_WEEKLY_STATE_RESCUE`

7. Quantified the relaxed weekly target gap:
   - report: `outputs/reports/A1_XAU_WEEKLY_TARGET_GAP_QUANTIFICATION_2026_07_06.md`
   - baseline is `114/210` positive calendar weeks; `70%` requires `147/210`
   - `33` current red weeks must flip for `70%`; `54` must flip for `80%`
   - easiest 33 flips require only `353.53 USD` in hindsight, but the current-pool oracle still failed, proving the missing piece is timing/coverage from a new source

8. Checked built-in signal-mode inventory:
   - report: `outputs/reports/A1_XAU_BUILT_IN_SIGNAL_MODE_INVENTORY_STATUS_2026_07_06.md`
   - all existing `InpSignalMode` values `0-11` have been touched by this owner-goal program or earlier exact-MT5 probes
   - weekly-level H4 rejection is not an untested shortcut; it already failed at `171` trades, WR `31.58%`, W/L `1.9852`, PF `0.9162`

9. Prepared the next-source plan:
   - plan: `docs/A1_XAU_NEXT_RED_WEEK_SOURCE_PLAN_2026_07_06.md`
   - next probe must be a genuinely new weekly-damage reversal/continuation source
   - red-week flips and weeks made worse are first-class metrics before any reviewer spend

10. Executed the weekly-damage H1 source in exact MT5 and froze it:
   - prereg/freeze notes: `docs/A1_XAU_WEEKLY_DAMAGE_H1_V0_PREREG_2026_07_07.md`, `docs/A1_XAU_WEEKLY_DAMAGE_H1_V14_FREEZE_NOTE_2026_07_07.md`
   - V14 exact report: `outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V14_WEEKLY_DAMAGE_H1_202207_202606.md`
   - V14 weekly review: `outputs/reports/A1_XAU_WEEKLY_DAMAGE_H1_V0_EXACT_MT5_REVIEW_202207_202606.md`
   - V14B direction split report: `outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V14B_WEEKLY_DAMAGE_H1_DIRECTION_SPLIT_202207_202606.md`
   - best baseline hybrid weekly result: `56.73%` positive calendar weeks, active weekdays `89.36%`, red weeks touched/flipped/worsened `63/14/24`
   - best standalone quality row: `v14b_weekly_damage_reversal_rr2_move10_long_only`, `146` trades, WR `39.73%`, W/L `2.2024`, PF `1.4516`, net `+435.11 USD`, but only `20.67%` positive weeks
   - best combo on top of the prior weekly-state rescue: positive weeks `59.52%`, active weekdays `90.03%`, WR/W-L `50.00%/1.7708`
   - result: `FREEZE_WEEKLY_DAMAGE_H1_SOURCE_CLASS`; do not continue with hour masks or threshold tuning

11. Executed the prior-day level M5 source in exact MT5 and froze it:
   - prereg/freeze notes: `docs/A1_XAU_PRIOR_DAY_LEVEL_M5_V15_PREREG_2026_07_07.md`, `docs/A1_XAU_PRIOR_DAY_AND_ASIA_RANGE_SOURCE_FREEZE_NOTE_2026_07_07.md`
   - V15 weekly review: `outputs/reports/A1_XAU_PRIOR_DAY_LEVEL_M5_V15_EXACT_MT5_REVIEW_202207_202606.md`
   - V15B direction split review: `outputs/reports/A1_XAU_PRIOR_DAY_LEVEL_M5_V15B_DIRECTION_SPLIT_EXACT_MT5_REVIEW_202207_202606.md`
   - best V15B baseline hybrid weekly result: `57.69%` positive calendar weeks, active weekdays `89.26%`, red weeks touched/flipped/worsened `81/12/36`
   - best combo on top of the prior weekly-state rescue: positive weeks `59.05%`, active weekdays `90.41%`, WR/W-L `49.17%/1.8148`
   - result: `FREEZE_PRIOR_DAY_LEVEL_M5_SOURCE_CLASS`; active, but standalone weak and not enough red-week repair

12. Executed the Asian-range M5 source in exact MT5 and froze it:
   - prereg/freeze notes: `docs/A1_XAU_ASIA_RANGE_M5_V16_PREREG_2026_07_07.md`, `docs/A1_XAU_PRIOR_DAY_AND_ASIA_RANGE_SOURCE_FREEZE_NOTE_2026_07_07.md`
   - V16 exact report: `outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V16_ASIA_RANGE_M5_202207_202606.md`
   - V16 weekly review: `outputs/reports/A1_XAU_ASIA_RANGE_M5_V16_EXACT_MT5_REVIEW_202207_202606.md`
   - best baseline hybrid weekly result: `56.73%` positive calendar weeks, active weekdays `96.84%`, red weeks touched/flipped/worsened `94/15/52`
   - weekly-state combo check: positive weeks fell from `58.10%` to `57.14%` while activity rose to `96.84%`
   - result: `FREEZE_ASIA_RANGE_M5_SOURCE_CLASS`; it buys activity, but damages weekly consistency

13. Ran a post-V16 exact-ledger risk-off premise audit:
   - audit: `docs/A1_XAU_POST_V16_RISK_OFF_PREMISE_AUDIT_2026_07_07.md`
   - red-week anatomy: `51/94` red weeks are frequency-frontier dominated, `43/94` are H4/D1 dominated, and `22/24` large red weeks below `-100 USD` are H4/D1 dominated
   - best single simple block only reached `57.69%` positive weeks while breaking payoff (`block H4/D1` W/L `1.4545`, or block entry hour `08` W/L `1.7890`)
   - best two-block smoother reached `60.58%` positive weeks, but W/L collapsed to `1.3591`
   - result: no simple risk-off block deserves exact-MT5 implementation as a path to the owner target

14. Recorded the 12:20 deadline audit:
   - audit: `docs/A1_XAU_1220_DEADLINE_GOAL_AUDIT_2026_07_07.md`
   - verdict: `DEADLINE_MISSED_NO_DEMO_READY_OWNER_GOAL_STRATEGY`
   - best serious frontier remains weekly-state + V14 weekly-damage add-on at `59.52%` positive weeks and `90.03%` activity, with W/L `1.7708`
   - result: no demo spec; next action requires a genuinely different strategy class, explicit target relaxation, or reviewer challenge

## Geometry V2 Result

No cell survived. Best raw weekly-shape row was `cap9000`, but it broke core W/L and stress gates.

| Variant | WR% | W/L | Stress -0.30/ticket W/L | Positive weeks% | Worst week | June 2026 | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 50.23 | 2.0002 | 1.9029 | 54.81 | -878.18 | -599.56 | research frontier |
| `cap9000` | 50.19 | 1.9709 | 1.8716 | 54.33 | -635.21 | -166.91 | reject: W/L < 2.0 |
| `cap6000_eae240_r060` | 48.46 | 1.7652 | 1.6603 | 52.88 | -215.85 | 188.78 | reject: WR/W-L broken |
| `p33_t2_run4_be` partial ladder | 50.08 | 1.9213 | 1.8106 | 57.21 | -867.90 | 164.14 | reject: W/L/stress broken |

Interpretation: stop caps, early-adverse exits, and the tested partial ladders can improve isolated weekly/monthly pain points, but they do it by cutting payout below the required shape. This is not a path to demo-readiness.

## Frozen Paths

Do not continue these without a materially new reviewer idea:

- H4/D1 stop-ceiling filters.
- H4/D1 stop-cap-only grids.
- H4/D1 early-adverse close grids.
- H4/D1 partial-ladder subset tested on 2026-07-06.
- Current smooth second-book archive and fixed sizing sweeps of residual packages, top causal coverage rows, and loaded exact-MT5 individual variants as a path to 70-80% positive weeks.
- Current-week closed-P&L state gates, previous-red-week add-on gates, and current-pool red-week oracle selection as a path to 70-80% positive weeks.
- Weekly-damage H1 V14/V14B source class as a path to 70-80% positive weeks.
- Prior-day level M5 V15/V15B source class as a path to 70-80% positive weeks.
- Asian-range M5 V16 source class as a path to 70-80% positive weeks.
- Weekly overlays as primary repair.
- Partial ladders using unnormalized fixed `0.01` split-entry exposure tricks.

## Remaining Blockers

- Owner target is 90% positive trade weeks; current best is 54.81% by exit-time closed P&L.
- Current best fails the +0.30/ticket stress W/L gate: 1.9029.
- Active weekday coverage is 86.39%, below the original 90% activity target.
- A diagnostic blend can reach `90.22%` active weekdays, but positive calendar weeks stay at only `54.29%` and W/L falls to `1.5950`.
- The best standalone smoother book reaches `61.90%` positive calendar weeks, but activity and W/L are unusable for the owner target.
- Weekly-state rescue improved the best causal row to only `58.10%` positive weeks and `87.63%` active weekdays; even the non-causal current-pool oracle topped out at `65.24%` positive weeks and `88.59%` active weekdays.
- The exact-MT5 weekly-damage H1 source improved the best baseline hybrid only to `56.73%` positive weeks and the best weekly-state combo only to `59.52%`, so the first new red-week source class also failed.
- The exact-MT5 prior-day level and Asian-range M5 sources bought activity, but not weekly repair: V15B topped at `57.69%` baseline-hybrid positive weeks and V16 topped at `56.73%`; V16 pushed activity to `96.84%` while worsening the weekly-state positive-week score to `57.14%`.
- Post-V16 simple risk-off blocks do not solve it either: best pair reaches `60.58%` positive weeks only by dropping W/L to `1.3591`.
- H4/D1 contributes most of the profit but creates too much weekly concentration.
- M5 frequency filler does not repair H4/D1 loss clusters.

## Next Direction

Stop trying to polish the current H4/D1 component. The next useful iteration should search for a different high-frequency, low-tail component with:

- WR >= 50%;
- W/L >= 2.0 before and after +0.30/ticket stress;
- more uniform week-by-week contribution than H4/D1;
- active-weekday contribution that raises the hybrid above 90% without depending on rare large winners;
- closed-P&L positive weeks improving materially from 54.81%.

The smooth second-book, weekly-state, prior-day level, Asian-range, and post-V16 risk-off diagnostics say weighting/gating the current archive, adding broad active range/level trades, or applying simple global blocks is not enough. To move toward the relaxed `70-80%` weekly target, the next search needs a genuinely new complementary source that wins specifically during baseline red weeks, not another gate over the same pool.

The 12:20 deadline audit confirms that no such component appeared inside the current family. The honest conclusion is that the current XAU owner target is not reachable from this family without changing the strategy class, relaxing the weekly condition further, or getting a reviewer to challenge the exhaustion conclusion with a materially new premise.
