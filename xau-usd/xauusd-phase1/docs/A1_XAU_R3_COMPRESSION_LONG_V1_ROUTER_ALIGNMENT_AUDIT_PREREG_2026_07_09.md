# A1 XAU R3 Compression Long V1 Router-Alignment Audit Preregistration

Date: 2026-07-09

## Purpose

Audit whether `r3_compression_long_v1_broad_box3_atr60_range125_body035` is truly an R3 compression-regime specialist or a mixed-regime long expansion source.

This is an audit and verification package only. It is not a new parameter search and does not authorize demo/live use.

## Fixed Inputs

R3 source under audit:

`A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_r3_compression_long_v1_broad_box3_atr60_range125_body035_NORMALIZED_TRADES.csv`

Current baseline:

`A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv`

Exact-MT5 snapshot source:

- run the existing EA with `InpRegimeSnapshotLogEnabled=true`
- use `InpRegimeRouterMode=0`
- no order-generation changes
- no live/demo runtime state changes
- period: 2022-07-01 through 2026-06-30

Each R3 trade is attributed to the latest completed MT5 router snapshot at or before entry time.

## Forbidden Changes

- No new R3 threshold.
- No second R3 variant.
- No R3 session filter.
- No R3 direction change.
- No stop, RR, cost, or management change.
- No R4 repair.
- No portfolio optimization grid.

## Outputs

Required report artifacts:

- router-state rows by R3 trade
- R3 PnL by EA-router regime
- compression-only diagnostic sub-book
- non-compression diagnostic sub-book
- current R1+R2 baseline
- current R1+R2 plus all R3
- current R1+R2 plus compression-only R3
- current R1+R2 plus non-compression R3
- monthly and yearly robustness
- concentration and drawdown checks

The compression-only and non-compression sub-books are diagnostic only. They are not deployable filters.

## Decision Rules

### True Compression Specialist

`R3_TRUE_COMPRESSION_SPECIALIST` requires:

- EA-router compression trades >= 100
- compression-only WR >= 50%
- compression-only W/L >= 2.00
- compression-only PF >= 2.00
- compression-only stress PF >= 1.50
- compression-only net > 0
- compression-only top10-removed net > 0
- compression-only top3-days-removed net > 0
- compression-only 2023+2024 net >= 0
- compression-only max DD <= current R1+R2 max DD

### Mixed-Regime Long Expansion Shadow

`R3_MIXED_REGIME_LONG_EXPANSION_SHADOW` applies when full R3 remains strong but either:

- compression-only trades < 100, or
- non-compression net > compression net.

Full R3 strong means:

- trades >= 150
- WR >= 50%
- W/L >= 2.00
- PF >= 2.50
- stress PF >= 2.00
- top10-removed net > 0
- top3-days-removed net > 0

### Freeze

`R3_COMPRESSION_LONG_V1_FREEZE` applies if:

- top10-removed net <= 0, or
- top3-days-removed net <= 0, or
- 2023+2024 net < 0, or
- current R1+R2+R3 all max DD > 125% of current R1+R2 max DD, or
- current R1+R2+R3 all WR < 50%, or
- current R1+R2+R3 all PF < 2.00.

### Portfolio Review Candidate

`R3_PORTFOLIO_REVIEW_CANDIDATE` requires current R1+R2+R3 all to satisfy:

- net > current R1+R2 net
- stress net > current R1+R2 stress net
- WR >= 50%
- W/L >= 2.00
- PF >= 2.00
- max DD <= 115% of current R1+R2 max DD
- recent3 net >= current R1+R2 recent3 net - $100
- top10-removed net > 0
- top3-days-removed net > 0
- best-month share <= 35%

If R3 improves full-window net but fails regime purity or drawdown/recent gates, it remains shadow-only.

