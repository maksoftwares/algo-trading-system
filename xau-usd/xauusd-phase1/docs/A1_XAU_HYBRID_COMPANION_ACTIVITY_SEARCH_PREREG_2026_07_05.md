# A1 XAU Hybrid Companion Activity Search Prereg

Date: 2026-07-05

Purpose: diagnose whether the current exact-ledger core frontier can be moved from `86.39%` active weekdays toward the owner's `90%+` activity threshold without breaking signal-level WR `>=50%` and realized average win/loss `>=2.0`.

Baseline: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`.

Allowed inputs: already-realized exact MT5 Strategy Tester trade/signal CSVs loaded by `analyze_a1_owner_goal_step3_portfolio_composition.py`, excluding older Step 1 same-family management cells because the baseline already carries the exact F67-H16 frequency branch.

Allowed filters: component alone, direction, broker-server entry hour, weekday, month, direction+hour, and direction+weekday. This is diagnostic only and is not a promotion rule, because the filters are searched after seeing the ledger.

Promotion rule: only a row with WR `>=50%`, W/L `>=2.0`, and active weekdays `>=90%` may justify a new preregistered exact MT5 rerun. A row that also keeps `+0.30/ticket` stressed W/L `>=2.0` is the only form worth reviewer consideration today.

Runtime boundary: no live/demo terminal, chart, preset, order, position, or broker-action state may be touched. This pass is exact-ledger composition only.
