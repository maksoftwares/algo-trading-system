# A1 XAU R2 Continuation Short V4 Volatility Gate Preregistration

Date: 2026-07-09

## Purpose

Add one more layer to the R2 continuation short before moving to a separate chop specialist.

The V1 R2 continuation short was profitable and useful in the last three months, but May 2026 exposed a specific weakness: valid-looking R2 breakdown/retest trades fired inside lower-volatility failed-breakdown conditions. June 2026 worked because the same signal fired during stronger downside participation.

This pass tests a simple pre-entry volatility participation gate:

- keep the V1 downside impulse/retest signal shape;
- keep strict R2 downtrend router;
- require M5 ATR to be high enough before entry;
- optionally combine the best ATR gate with the V3 daily loss guard.

## Runtime Boundary

Research-only exact-MT5 backtest.

No demo, live, forward, broker-action, chart, preset, profile, account, position, or runtime change is authorized.

## Fixed Constraints

All variants must use:

- strict Router V1 R2 only: `InpRegimeRouterMode=2`;
- short only: `InpDirectionMode=2`;
- fixed 2R target: `InpRiskReward=2.00`;
- signal mode 19, downside impulse retest;
- V1 body45 signal geometry;
- no breakeven, partial close, trailing, or profit lock;
- no day, month, blocked-hour, or session masks;
- no R2 router relaxation;
- no additional D1/H4/H1 trend-stack filter;
- the ATR floor must be enforced by `InpMinAtrAbsoluteForEntry`, before order send.

## Fixed Variants

Run exactly three variants:

1. `r2_impulse_body45_atr45`
   - V1 `r2_impulse_retest_body45`
   - `InpMinAtrAbsoluteForEntry=4.50`

2. `r2_impulse_body45_atr50`
   - V1 `r2_impulse_retest_body45`
   - `InpMinAtrAbsoluteForEntry=5.00`

3. `r2_impulse_body45_atr45_daily_loss10`
   - V1 `r2_impulse_retest_body45`
   - `InpMinAtrAbsoluteForEntry=4.50`
   - portfolio daily loss stop `InpPortfolioDailyLossStopUsd=10.00`

## Report Requirements

Report full-window and recent three months for:

- standalone V4 variants;
- each V4 variant added to current R1 plus repaired best R2 pullback.

Include trades, wins, losses, WR, W/L, PF, net, stress net after -$0.30/trade, max closed drawdown, April/May/June 2026, failed checks, exact-MT5 raw evidence paths, and guard counts for `atr_below_entry_floor`.

## Decision

This is a profit-first R2 repair layer. Prefer a variant only if it:

- preserves meaningful June/downtrend profit;
- reduces or neutralizes May-style failed-breakdown damage;
- keeps full-window standalone net positive after -$0.30/trade stress;
- improves combined book quality without hiding a large profit loss;
- remains research-only until reviewed.

If the layer merely improves win rate while reducing profit too much, reject it and move to a separate chop specialist/router.
