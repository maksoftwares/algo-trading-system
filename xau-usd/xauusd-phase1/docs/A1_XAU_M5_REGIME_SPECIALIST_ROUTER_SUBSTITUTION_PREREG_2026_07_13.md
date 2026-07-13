# A1 XAU M5 Router-Substitution Recovery Preregistration

Date: `2026-07-13`

Status: `FROZEN_BEFORE_ROUTER_SUBSTITUTION_MT5_EXECUTION`

## Why a recovery phase is required

The exact-profile routing phase produced zero trades for all eight candidates.
Order telemetry proved that signals were being blocked by a second, legacy
H1/H4 regime filter after Router V1 had already classified the market. The
stack therefore required two independently defined regime owners to agree and
did not measure the intended M5 profile inside one Router V1 regime.

The zero-trade phase remains preserved as evidence. It is not used as a
profitability verdict.

## Frozen repair

For the same eight named M5 profiles:

- keep the original M5 signal mode and all entry thresholds;
- keep direction, target, stop, cost cap, and hour masks;
- keep fixed `0.01 lot` and one position maximum;
- set only `InpUseH1TrendFilter=false` and `InpUseH4TrendFilter=false`;
- use fail-closed Router V1 as the sole regime owner;
- keep SHOCK permanently no-trade.

No signal threshold is loosened and no result-dependent direction or hour is
removed.

## Frozen candidates and owners

| Regime | Candidates |
|---|---|
| R1 UPTREND | `r1_router_v4_break_run_long`, `r1_router_v13_ema_long` |
| R2 DOWNTREND | `r2_router_v13_ema_short`, `r2_router_v13_feature_loss_short` |
| R3 COMPRESSION | `r3_router_v13_ema_both`, `r3_router_v12_ema_both` |
| R4 CHOP | `r4_router_v13_ema_both`, `r4_router_v12_ema_both` |

## Frozen validation

Five-year screen: `2021-07-01` through `2026-07-01`, XAUUSD M5, every tick,
`$1,000 USD`, native history quality `>=98%`.

Pass every gate:

- trades `>=100`;
- PF `>=1.20`;
- win rate `>=35%`;
- net profit `>0`;
- relative equity drawdown `<=20%`.

A five-year survivor is rerun unchanged over `2016-07-01` through
`2026-07-01`. Only a ten-year pass may be called a found M5 specialist. This
phase is not demo/live or deployment authorization.
