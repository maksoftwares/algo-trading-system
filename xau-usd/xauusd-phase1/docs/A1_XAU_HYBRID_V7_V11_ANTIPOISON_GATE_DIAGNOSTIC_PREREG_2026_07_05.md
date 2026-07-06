# A1 XAU Hybrid V7/V11 Antipoison Gate Diagnostic Prereg

Date: 2026-07-05

Purpose: the current exact-ledger frontier clears WR and realized W/L but misses active weekdays. Exact-ledger companion search showed that the v7/v11 activity sources can push active days above 90%, but they pull WR down to about 46%. This diagnostic asks whether causal MT5 signal features can filter those activity sources before composition.

Baseline: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`.

Candidate sources: exact MT5 Strategy Tester v7/v11 RR2 trade CSVs and their matching tab-separated signal CSVs from `a1_momentum_variants_owner_goal_v7_v8_v11_v13_rr2_202207_202606_20260701`.

Allowed causal fields: broker-server hour, weekday, `spread_points`, `atr`, `body_fraction`, `close_location`, `three_bar_move_atr`, `break_distance_atr`, and `estimated_cost_r`. These are logged at signal time before trade outcome.

Design/validation split: gates are ranked on the older design slice `2022-07-01` through `2024-06-30` and then reported on full `2022-07-01` through `2026-06-30`, validation `2024-07-01` through `2026-06-30`, and last 12 months.

Allowed search: single-feature thresholds and bands, plus small combinations of top single gates across distinct sources. This is diagnostic only because filtering a realized trade ledger cannot prove the exact MT5 one-position path after skipped trades. Any hit requires a new preregistered exact MT5 replay.

Promotion rule: only a row with full-window WR `>=50%`, W/L `>=2.0`, active weekdays `>=90%`, and validation not materially broken is eligible for exact MT5 replay consideration. Reviewer is preserved unless exact replay confirms the row.

Runtime boundary: no live/demo runtime, chart, preset, order, position, or broker state may be touched.
