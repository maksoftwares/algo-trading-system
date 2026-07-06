# A1 XAU Hybrid Prune-Fill Diagnostic Prereg

Date: 2026-07-05

Purpose: test whether the current exact-ledger core frontier can be improved by pruning weak categorical pockets from the baseline frequency branch while filling activity with the strongest v7/v11 causal-feature activity gates.

Baseline: `A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`.

Allowed baseline prune fields: source, variant name, direction, broker-server entry hour, weekday, month, and variant+hour. No outcome-aware row removal is allowed.

Allowed fill sources: v7/v11 activity gates from `A1_XAU_HYBRID_V7_V11_ANTIPOISON_GATE_DIAGNOSTIC_2026_07_05`, rebuilt from exact MT5 trade/signal CSVs.

Promotion rule: a diagnostic hit must reach full-window WR `>=50%`, realized W/L `>=2.0`, and active weekdays `>=90%`. It is still not demo-ready; a hit only justifies a preregistered exact MT5 replay because ledger pruning/filling cannot prove the one-position path.

Runtime boundary: no live/demo runtime, chart, preset, order, position, or broker state may be touched.
