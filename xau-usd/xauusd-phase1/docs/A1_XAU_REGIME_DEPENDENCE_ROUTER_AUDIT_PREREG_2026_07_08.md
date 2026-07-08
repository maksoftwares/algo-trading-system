# A1 XAU Regime-Dependence Router Audit Preregistration

Generated: 2026-07-08

## Purpose

The current combined book has acceptable full-window shape, but the user flagged the real risk: the main long edge may only be a gold-bull harvester, and recent months do not prove that edge still exists.

This pass does not tune entries, stops, targets, hours, sessions, months, or source definitions. It audits whether the current best book is robust across time/source regimes or whether it should be treated only as a research/watchlist router candidate.

This is research-only. It does not authorize demo/live trading.

## Input

Use the current best chart-context blend ledger:

`A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_KEPT.csv`

This ledger is a recomposition of exact-MT5 Strategy Tester trade rows. The audit recomputes PnL and shape manually from the rows; it does not rely on MT5 summary totals.

## Execution Boundary

- No MT5 launch.
- No live/demo runtime attach.
- No chart, preset, profile, order, position, or broker-state change.
- No new signal generation.
- No price-regime label may be invented unless a clean local OHLC source is explicitly used. If no OHLC source is used, regime conclusions must be labeled as source/time inference.

## Fixed Periods

Report source contribution and shape over exactly these periods:

- Full window: `2022-07-01` through `2026-06-30`.
- Pre-2025 window: `2022-07-01` through `2024-12-31`.
- Bull-harvest window: `2025-01-01` through `2026-01-31`.
- 2026 Q1 transition: `2026-01-01` through `2026-03-31`.
- 2026 Q2 recent: `2026-04-01` through `2026-06-30`.
- Last 12 months: `2025-07-01` through `2026-06-30`.

## Fixed Diagnostic Portfolios

Report exactly these source slices:

- `current_blend`: all rows.
- `h4_long_only`: only `h4_d1_long_best_box2_atr80`.
- `freq_only`: only `freq_step3_frontier`.
- `short_v4_only`: only `short_v4_impulse_retest_d1_structural_h1h4`.
- `freq_plus_short_no_h4`: frequency plus V4 short, excluding the H4/D1 long source.

These are diagnostics only, not new candidates.

## Diagnostic Questions

Answer these directly:

1. How much full-window net comes from the H4/D1 long source?
2. How much Q2-2026 net comes from each source?
3. Did the H4/D1 long source contribute to Q2-2026, or is recent survival coming from other sources?
4. Does removing the long source leave a viable standalone book?
5. Is the current book demo-ready, review-only, or shadow-only under this evidence?

## Decision Labels

Use `REGIME_DEPENDENCE_CONFIRMED_SHADOW_ONLY` if all are true:

- H4/D1 long source contributes at least 60% of full-window net.
- H4/D1 long source contributes no positive Q2-2026 net.
- `freq_plus_short_no_h4` fails the full-window core gate of WR `>= 50%`, W/L `>= 2.0`, net `>= 19000`, and active weekdays `>= 84%`.

Use `REGIME_ROUTER_REVIEW_CANDIDATE` only if recent Q2 survival is positive and the report clearly states that the long edge is conditional rather than current all-regime proof.

Use `REGIME_ROUTER_NO_SURVIVOR` if recent Q2 survival is negative or the current blend loses the core full-window shape.

## Forbidden

- No hour/session/day/month masks.
- No post-hoc cutoff becoming a candidate rule.
- No deleting the long source to make recent months look better.
- No claiming a demo-ready strategy from this audit.
- No claiming price-regime causality without local OHLC evidence.

