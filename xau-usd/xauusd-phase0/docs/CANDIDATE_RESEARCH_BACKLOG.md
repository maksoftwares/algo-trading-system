# Candidate Research Backlog

Last updated: 2026-05-22

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
| 16 | `session_vwap_reclaim_v0` | NEXT_RESEARCH_CANDIDATE | Needs VWAP/proxy implementation and reclaim definition. |
| 17 | `ny_london_overlap_compression_break_v0` | BACKLOG | Needs overlap compression and expansion definition. |

## Discipline

- Rejected candidates are not tuned in place.
- Any revisit uses a new versioned hypothesis.
- No candidate enters the active EA roadmap until Phase 0 verdict is PASS.
- `phase0 run-matrix --expert all` must remain reserved for the active approved/legacy Phase 0 set, not experimental backlog candidates.
- Original 10-candidate bench is now fully resolved: 1 approved future expert and 9 rejected v0 candidates.
