# V60 Portable Mature Top-Up Prospective V3 Preregistration

## Purpose

Portable Mature Top-Up V2 passed its frozen historical development gates after
removing all Dukascopy-specific microstructure fields. V3 determines whether
that fixed model can be served from completed Capital MT5 M5 bars without
changing the existing deterministic V60 entries.

## Frozen Procedure

1. Recreate the exact seed-0 annual walk-forward sequence and retain the forty
   regressors trained for the 2026 test year. Their training cutoff is
   `2025-12-30T00:00:00Z`; no 2026 outcome may enter model fitting.
2. Reproduce every stored 2026 score and rank before using the serving bundle.
3. Build the thirteen V2 features from completed M5 bars only:
   `atr_ratio`, `rv_1h`, `rv_24h`, `slope_atr`, `ret_1h`, `ret_4h`,
   `ret_24h`, `dist_hi_24h`, `dist_lo_24h`, `hour`, `dow`, `is_long`, and
   `is_core`.
4. Compare Dukascopy and Capital features and model scores on their common
   July 2026 completed bars. Evaluate all four fixed trade contexts:
   long/short by core/add-on. Do not use July trade outcomes.
5. Rank prospective scores against the frozen historical OOS score reference.
   A live implementation must append each newly scored candidate only after
   its decision has been made.

## Frozen Pass Gates

- Stored 2026 score maximum absolute error: at most `1e-10`.
- Stored 2026 rank maximum absolute error: at most `1e-12`.
- At least `3,000` common completed M5 bars and `12,000` context rows.
- Cross-feed score Spearman correlation: at least `0.85`.
- Cross-feed rank Spearman correlation: at least `0.85`.
- Mean absolute cross-feed rank difference: at most `0.08`.
- Top-quintile decision Jaccard agreement: at least `0.60`.
- Capital top-quintile precision and recall against Dukascopy: each at least
  `0.75`.
- No NaN or infinite serving feature may be scored.

Failure of any gate keeps ML broker action disabled. Passing nominates a
fail-closed prospective demo top-up only; it does not authorize live trading.

## Runtime Boundary

The deterministic V60 baseline trade is never rejected, resized downward, or
delayed by ML. A score above the frozen `0.80` rank threshold may request one
additional `0.01` lot only when risk is known and all existing source,
direction, account, drawdown, and duplicate-event controls accept it. Missing
bars, stale bars, model errors, state errors, unknown risk, or failed limits
must produce baseline-only behavior.
