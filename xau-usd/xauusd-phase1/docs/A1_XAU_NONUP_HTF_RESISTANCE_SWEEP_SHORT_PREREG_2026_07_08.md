# A1 XAU Non-Up HTF Resistance Sweep Short Preregistration

Generated: 2026-07-08

## Purpose

Test the reviewer-proposed short specialist that has the best chance of improving short quality: a non-uptrend higher-timeframe resistance sweep/reclaim short.

This is the first short specialist after the router audit showed that strict `R2 DOWNTREND` blocks all V4 short candidates. This pass tests a less strict but still structural short regime:

- D1 is non-up.
- Price sweeps a higher-timeframe resistance.
- M15 confirms bearish reclaim/failure.
- Entry is short with fixed 2R.

This is research-only. It does not authorize demo/live trading.

## Fixed Exact-MT5 Variant

Run exactly one variant:

`nonup_htf_resistance_sweep_short_v1`

Inputs:

- `InpSignalMode = 18` (`SIGNAL_BEAR_HTF_RESISTANCE_SWEEP`)
- short-only
- fixed `2.00R`
- D1 non-up gate: `D1 close <= EMA20 OR EMA20 falling`
- no hour/session/day/month masks
- H4 resistance lookback `30`
- M15 reclaim bars `6`
- H4 ATR sweep buffer `0.10`
- H4 ATR stop buffer `0.10`
- bearish M15 body fraction `>= 0.35`
- bearish M15 close location `<= 0.35`

## Gate

Standalone watchlist requires all:

- trades `>= 100`
- WR `>= 45%`
- W/L `>= 1.90`
- PF `>= 1.20`
- stress PF after `-$0.30/trade` `>= 1.15`
- stress net `> 0`
- 2023+2024 net `>= 0`
- positive year buckets `>= 3`
- top10-removed net `> 0`
- top3-days-removed net `> 0`

Strict pass requires WR `>= 50%` with the same durability gates.

If WR is below `40%`, or stress PF is below `1.15`, or 2023+2024 is negative, stop treating this as a standalone short path.

## Forbidden

- No parameter grid.
- No hour/session/day/month masks.
- No RR tuning after seeing results.
- No adding frequency filler.
- No demo claim.

