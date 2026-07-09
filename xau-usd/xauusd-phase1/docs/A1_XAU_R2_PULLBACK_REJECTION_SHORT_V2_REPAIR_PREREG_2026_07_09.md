# A1 XAU R2 Pullback-Rejection Short V2 Repair Preregistration

Date: 2026-07-09

## Purpose

Repair the strict R2 H1 pullback-rejection short specialist by addressing the specific weakness found in V1 diagnostics:

- weak M5 execution candles after the H1 rejection;
- poor night-session performance;
- low standalone win rate despite acceptable payoff.

This V2 test does not relax the strict R2 router. It does not retune the downtrend definition. It only tests a default-off M5 execution-body quality filter, with one broad liquid-hours variant.

## Baseline

V1 H1 confirmation baseline:

- trades: 211
- WR: 39.34%
- W/L: 2.2504
- PF: 1.4592
- net: +$426.88
- recent 3 months: 11 trades, WR 54.55%, net +$139.13

Diagnostic weakness:

- night trades: 65 trades, 32.31% WR, PF 0.63, net -$133.38
- Friday trades: 21 trades, 19.05% WR, net -$98.44
- M5 body-strength filter improved WR materially in diagnostics

## Runtime Boundary

Research-only exact-MT5 backtest.

No demo, live, forward, broker-action, chart, preset, profile, account, position, or runtime change is authorized.

## EA Change

Add default-off inputs:

- `InpR2PullbackM5ExecutionBodyFilterEnabled=false`
- `InpR2PullbackM5MinBodyFraction=0.00`

When enabled, the R2 signal must require the latest completed M5 execution candle to have:

- `abs(close-open)/(high-low) >= InpR2PullbackM5MinBodyFraction`

The filter must use completed M5 bar `[1]` only. No bar 0 is allowed.

## Fixed Variants

Run exactly two variants:

1. `r2_h1_m5_body58`
   - strict R2 router
   - H1 confirmation
   - H1 pullback lookback 3
   - M5 execution body >= 0.58
   - no session filter

2. `r2_h1_m5_body58_hours05_18`
   - same as variant 1
   - broad short-entry liquid-hours filter only
   - `InpUseDirectionalSessionFilter=true`
   - `InpShortSessionStartHour=5`
   - `InpShortSessionEndHour=19`

The hour window means server hours 05 through 18 inclusive.

## Forbidden Work

Do not run:

- extra body thresholds;
- Friday-only exclusion;
- night-only exclusion;
- hour grids;
- day/month filters;
- R2 router relaxation;
- RR changes;
- breakeven, partial close, trailing, or profit lock;
- M15 confirmation repair;
- combined portfolio optimization.

## Report Requirements

Report full-window and recent 3 months for:

- standalone V2 variants;
- each V2 variant combined with the current R1 book.

Include:

- trades, wins, losses, WR, W/L, PF, net;
- stress W/L and stress PF after -$0.30/trade;
- max closed drawdown;
- top10-removed net;
- top3-days-removed net;
- best-month share;
- recent 3 months trades, WR, PF, net;
- June 2026 trades, WR, PF, net;
- failed checks;
- exact-MT5 raw component evidence paths.

## Decision

This is a repair diagnostic.

- If a variant reaches WR >= 50%, W/L >= 1.90, PF >= 2.00, net > 0, and recent 3 months net >= 0 but trades < 80, label it `R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_SHADOW_LOW_SAMPLE`.
- If a variant reaches the same metrics with trades >= 80, label it `R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_REVIEW_CANDIDATE`.
- Otherwise label it `R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_NO_SURVIVOR`.

No demo or forward spec may be drafted from this repair without reviewer review.
