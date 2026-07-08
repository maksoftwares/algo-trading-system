# A1 XAU Chart-Context Long/Short Blend Preregistration

Generated: 2026-07-08

## Purpose

Use the TradingView chart-context finding as a hedge overlay inside the current best long-plus-short book. The standalone short did not reach the user's `50% WR / 2R` objective, but it did show recent-regime defense. This test asks whether the short is useful as part of the combined book.

This is research-only. It does not authorize demo/live trading.

## Execution Boundary

- No live/demo runtime, chart, profile, preset, open order, or broker-state change.
- No new MT5 trading run is needed for the blend itself; all components already come from exact-MT5 tester ledgers.
- Python recomposes exported exact-MT5 ledgers and recomputes metrics manually.
- The V4 downside-impulse short ledgers must come from `A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708`.

## Baseline

Current best combined long book:

`A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_broad_quarantined_KEPT.csv`

This baseline already contains:

- `freq_step3_frontier`,
- `h4_d1_long_best_box2_atr80`,
- the older `short_hedge_v2_breakdown_retest`.

## Fixed Short Overlay Candidates

Use exactly the three already-generated V4 chart-context short ledgers:

- `short_v4_impulse_retest_d1_nonup_h1h4`
- `short_v4_impulse_retest_d1_structural_h1h4`
- `short_v4_impulse_retest_d1_nonup_h1_only`

## Fixed Blend Modes

Run exactly two blend modes for each V4 short:

1. `add`: keep the current baseline, then add the V4 short. Dedupe same-direction overlaps within five minutes using the existing portfolio dedupe rule.
2. `replace_v2`: remove existing `short_hedge_v2_breakdown_retest` rows, then add the V4 short. Dedupe afterward.

Also report `long_book_without_short_v2` as a diagnostic row, not as a candidate.

## Pass Gate

A blend can be a review candidate only if all are true:

- WR `>= 48%`.
- raw W/L `>= 2.00`.
- stress W/L after `-$0.30` per ticket `>= 1.90`.
- net `>= 19000`.
- active weekdays `>= 84%`.
- max closed drawdown `<=` baseline.
- positive closing months `>=` baseline.
- negative closing months `<=` baseline.
- Q2-2026 net `>` baseline Q2-2026 net.
- recent-three-month net `>` baseline recent-three-month net.

## Forbidden

- No hour/session/day/month masks.
- No changing RR after seeing results.
- No replacing the long engine.
- No deleting frequency rows to make the short look better.
- No demo claim from this pass.

## Decision

If a row passes the gate:

- Status: `CHART_CONTEXT_BLEND_REVIEW_CANDIDATE`.
- Keep research-only pending reviewer sign-off.

If no row passes:

- Status: `CHART_CONTEXT_BLEND_NO_SURVIVOR`.
- Use the result to decide whether the chart-context short should remain a hedge clue only.
