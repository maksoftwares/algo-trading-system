# Candidate Research Backlog

Last updated: 2026-05-23

## Planning Rule

The long-term research bench targets 10 mechanical candidate hypotheses. This does not mean 10 EAs will be built. Candidates only become future EAs after passing the full Phase 0 process.

Expected path:

| Stage | Target Count | Meaning |
| --- | ---: | --- |
| Research backlog | 10 | Mechanical hypotheses worth pre-registering or rejecting. |
| Active Phase 0 candidates | 1-3 at a time | Candidates under current validation. |
| Approved future experts | 3-5 over time | Only candidates that survive all gates. |
| Live-capable EAs | Later phase only | Requires dry-run, paper-mode, and owner approval. |

## Current Backlog

| # | Candidate | Status | Next Action |
| ---: | --- | --- | --- |
| 1 | `breakout_retest` | APPROVED_FUTURE_EXPERT | Keep in Phase 1 dry-run observation only. |
| 2 | `trend_pullback` | REJECTED_V1 | Do not tune under the same name. |
| 3 | `range_mr` | REJECTED_V1 | Do not tune under the same name. |
| 4 | `squeeze_breakout_long_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 5 | `post_spike_short_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 6 | `emr_inactivity_long_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1 and trade-count gate; do not tune v0. |
| 7 | `ny_failed_london_reversal_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 8 | `london_fix_continuation_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 9 | `extreme_activity_mean_reversion_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 10 | `compression_retest_continuation_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix trade-count gate; do not tune v0. |
| 11 | `asia_range_london_breakout_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 12 | `previous_day_extreme_retest_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 13 | `ny_am_pullback_continuation_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 14 | `weekly_level_reclaim_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 15 | `asia_range_london_failed_break_reversal_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 16 | `session_vwap_reclaim_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 17 | `swing_breakout_retest_v0` | APPROVED_FUTURE_EXPERT_CANDIDATE | Passed 9-cell, decile, multisymbol, intrabar, and Gate 9 manual adversarial checks; same-family with `breakout_retest`. |
| 18 | `ny_london_overlap_compression_break_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix PF coverage and trade-count gate; do not tune v0. |
| 19 | `opening_drive_failed_continuation_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 20 | `liquidity_sweep_reversal_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; do not tune v0. |
| 21 | `daily_pivot_reclaim_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; adequate trade count but 0/9 PF cells reached 1.30, so do not tune v0. |
| 22 | `m15_inside_bar_breakout_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; adequate trade count but 0/9 PF cells reached 1.30, so do not tune v0. |
| 23 | `m5_impulse_continuation_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; high trade count but 0/9 PF cells reached 1.30, so do not tune v0. |
| 24 | `round_number_retest_v0` | PROVISIONAL_PASS_PENDING_GATE9 | Passed 9-cell matrix, deciles, low intrabar ambiguity, and XAU-specific multisymbol note; manual adversarial review still required. |
| 25 | `symbol_normalized_round_retest_v0` | PROVISIONAL_PASS_PENDING_GATE9 | Passed 9-cell matrix, deciles, low intrabar ambiguity, and non-zero EURUSD/USDJPY multisymbol transfer; manual adversarial review still required. |
| 26 | `symbol_round_sweep_reversal_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; adequate trade count but 0/9 PF cells reached 1.30 and drawdown was too high, so do not tune v0. |
| 27 | `liquidity_sweep_continuation_v0` | REJECTED_FIRST_PASS | Failed 9-cell matrix Gate 1; adequate trade count but 0/9 PF cells reached 1.30, so do not tune v0. |
| 28 | `session_extreme_retest_v0` | PROVISIONAL_PASS_PENDING_GATE9 | Passed 9-cell matrix, deciles, multisymbol, and intrabar checks; same-family level-and-pullback, so not diversification and Gate 9 remains pending. |
| 29 | `d1_momentum_h4_pullback_v0` | REJECTED_FIRST_PASS | First true H4/D1 decision-timing candidate; 3/9 PF cells reached 1.30, trade count passed, concentration failed; do not tune v0. |
| 30 | `d1_volatility_expansion_reversal_v0` | REJECTED_FIRST_PASS | Second true H4/D1 decision-timing candidate; 0/9 PF cells reached 1.30, trade-count and concentration gates failed; do not tune v0. |
| 31 | `d1_compression_h4_expansion_v0` | REJECTED_FIRST_PASS | Third true H4/D1 decision-timing candidate; 0/9 PF cells reached 1.30, trade count passed, concentration failed; do not tune v0. |
| 32 | `h4_real_yield_proxy_momentum_v0` | BLOCKED_MISSING_MACRO_DATA | Macro-proxy attempt deferred until real-yield, DXY, Treasury, or approved proxy series exists locally; do not fake it with XAU-only data. |
| 33 | `d1_multi_day_exhaustion_reversion_v0` | REJECTED_FIRST_PASS | Fourth true H4/D1 decision-timing candidate; 0/9 PF cells reached 1.30, trade-count/activity/concentration failed; do not tune v0. |
| 34 | `h4_d1_momentum_expansion_continuation_v0` | REJECTED_FIRST_PASS | Fifth true H4/D1 decision-timing candidate; 3/9 PF cells reached 1.30, all in Dukascopy, concentration failed; do not tune v0. |
| 35 | `h4_inside_bar_d1_momentum_breakout_v0` | REJECTED_FIRST_PASS | Sixth H4/D1 decision-timing candidate; 2/9 PF cells reached 1.30, trade count passed, concentration failed; do not tune v0. |
| 36 | `w1_d1_momentum_continuation_v0` | REJECTED_FIRST_PASS | First W1/D1-scale candidate; 3/9 PF cells reached 1.30, all cells positive, but concentration failed; do not tune v0. |

## Discipline

- Rejected candidates are not tuned in place.
- Any revisit uses a new versioned hypothesis.
- No candidate enters the active EA roadmap until Phase 0 verdict is PASS.
- `phase0 run-matrix --expert all` must remain reserved for the active approved/legacy Phase 0 set, not experimental backlog candidates.
- Original 10-candidate bench is now fully resolved: 1 approved future expert and 9 rejected v0 candidates.
- Extended bench status: `swing_breakout_retest_v0` is an approved future expert candidate, but it is same-family with `breakout_retest`; `ny_london_overlap_compression_break_v0` and `opening_drive_failed_continuation_v0` were rejected first-pass. Continue searching for a more independent second behavior.
- Latest independent candidate result: `daily_pivot_reclaim_v0` was rejected first-pass. It produced enough trades, but 0/9 cells reached PF >= 1.30.
- Latest independent candidate result: `m5_impulse_continuation_v0` was rejected first-pass. It produced high trade count, but 0/9 cells reached PF >= 1.30.
- Latest candidate result: `round_number_retest_v0` is a provisional same-family pass pending Gate 9 manual adversarial review.
- Latest candidate result: `symbol_normalized_round_retest_v0` is a stronger provisional same-family pass than `round_number_retest_v0` because it preserves XAU matrix strength while producing EURUSD PF 1.298 and USDJPY PF 1.559 in multisymbol transfer. Gate 9 remains pending with 0/120 sampled losing trades reviewed.
- Latest independent reversal candidate result: `symbol_round_sweep_reversal_v0` was rejected first-pass. It produced enough trades, but 0/9 cells reached PF >= 1.30 and max drawdown reached 50.46%.
- Latest independent continuation candidate result: `liquidity_sweep_continuation_v0` was rejected first-pass. It produced enough trades, but 0/9 cells reached PF >= 1.30.
- Latest same-family provisional result: `session_extreme_retest_v0` passed automated research gates, but remains Gate 9 pending and does not diversify the breakout-retest family.
- Review #5 forcing-function result: `d1_momentum_h4_pullback_v0` was registered, hash-locked, implemented, smoke-tested, and run through a real 9-cell first pass before any new same-family candidate was authored. It was rejected with 3/9 PF cells >= 1.30 and a failed concentration gate.
- Latest H4/D1 diversification result: `d1_compression_h4_expansion_v0` was rejected first-pass. It produced 68-122 trades per cell, 0/9 PF cells >= 1.30, passed trade count, and failed concentration.
- Latest H4/D1 diversification result: `d1_multi_day_exhaustion_reversion_v0` was rejected first-pass. It produced 24-41 trades per cell, 0/9 PF cells >= 1.30, and failed trade-count, activity, and concentration gates.
- Latest H4/D1 diversification result: `h4_d1_momentum_expansion_continuation_v0` was rejected first-pass. It produced 81-83 trades per cell and 3/9 PF cells >= 1.30, but strength was Dukascopy-only and concentration failed.
- Latest H4/D1 breakout result: `h4_inside_bar_d1_momentum_breakout_v0` was rejected first-pass. It produced 71-100 trades per cell and 2/9 PF cells >= 1.30, with small positive returns but inadequate cross-venue strength and failed concentration.
- Latest W1/D1 result: `w1_d1_momentum_continuation_v0` was rejected first-pass. It produced 48-68 trades per cell and 3/9 PF cells >= 1.30; all cells were positive, but concentration failed and cross-venue PF strength was insufficient.
- Continue searching for a genuinely independent non-level behavior family; no rejected v0 candidate may be tuned in place.
- `h4_real_yield_proxy_momentum_v0` is blocked because no real-yield, DXY, Treasury, or macro-proxy series is present in `data/` or `reference/`; move to `d1_multi_day_exhaustion_reversion_v0` rather than inventing macro inputs.
- Review #6 plan before Phase 2: pre-register and test at least three additional non-level H4/D1 concepts (`d1_compression_h4_expansion_v0`, `h4_real_yield_proxy_momentum_v0`, `d1_multi_day_exhaustion_reversion_v0`) unless the project owner explicitly defers them in writing.

## Timeframe Coverage

Classify by entry / decision timeframe, not by the source of the reference level.

```yaml
hypothesis_timeframe_coverage:
  M5_M15: 28
  M30_H1: 0
  H4_D1: 6
  W1_plus: 1
  planned_next_H4_D1: []
  blocked_H4_D1:
    - h4_real_yield_proxy_momentum_v0
```

`daily_pivot_reclaim_v0` and `weekly_level_reclaim_v0` used slower reference levels, but both had M5 entries, so they do not count as H4/D1 diversification.

`d1_momentum_h4_pullback_v0`, `d1_volatility_expansion_reversal_v0`, `d1_compression_h4_expansion_v0`, `d1_multi_day_exhaustion_reversion_v0`, `h4_d1_momentum_expansion_continuation_v0`, and `h4_inside_bar_d1_momentum_breakout_v0` count as H4/D1 diversification attempts by timing, but all are rejected and none becomes an approved expert.
