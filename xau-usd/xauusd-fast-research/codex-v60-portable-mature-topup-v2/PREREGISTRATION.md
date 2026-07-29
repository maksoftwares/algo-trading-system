# V60 Portable Mature Top-Up V2 Preregistration

## Purpose

The exposed full-feature development diagnostic improved V60 by adding a second
`0.01` lot to causal-score ranks above the 80th percentile from 2024 onward.
That policy cannot be served faithfully from MT5 because five model inputs are
Dukascopy-feed-specific microstructure measurements.

V2 tests one portability correction before opening its result: remove exactly
those five fields and change nothing else.

## Frozen Experiment

- Retain every deterministic V60 baseline trade.
- Use completed-bar features only.
- Use `atr_ratio`, `rv_1h`, `rv_24h`, `slope_atr`, `ret_1h`, `ret_4h`,
  `ret_24h`, `dist_hi_24h`, `dist_lo_24h`, `hour`, `dow`, `is_long`, and
  `is_core`.
- Keep the original purged annual walk-forward regression, target, model
  parameters, 40 bags, rank construction, and seeds.
- Before 2024, never top up.
- From 2024 onward, propose one additional `0.01` lot only when the causal rank
  is strictly above `0.80`.
- Let the existing source, account, direction, add-on, unknown-risk, and
  position controls reject unsafe top-ups.
- Never skip a baseline trade.

The five removed fields are `ms_flow`, `ms_imb`, `ms_eff`,
`ms_spread_per_risk`, and `ms_activity`. No alternate feature subset,
threshold, maturity date, model, or risk limit may be tried in this version.

## Interpretation

All historical V60 outcomes were already exposed. A pass is development
evidence and may only nominate a bounded, fail-closed prospective demo test.
It is not independent proof and cannot authorize live trading.

