# A1 XAU R2 Continuation Short V3 Profit Guard Preregistration

Date: 2026-07-09

## Purpose

Run one final profit-first repair pass on the useful V1 R2 continuation short.

The V1 continuation leg added the best recent downtrend coverage:

- `r2_impulse_retest_body45`
- combined book net: +$9,750.48
- combined last 3 months: 88 trades, +$818.35

The V2 geometry repair moved combined WR closer to 50%, but cut recent profit too much. This pass therefore keeps the V1 signal shape and tests only daily damage controls that could run live inside MT5.

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
- no additional H1/H4/D1 structural filter stacked on top of R2.

## Fixed Variants

Run exactly three variants:

1. `r2_impulse_body45_daily_loss7`
   - V1 `r2_impulse_retest_body45`
   - portfolio daily guard enabled for this magic only
   - stop new entries after closed daily P/L <= -$7

2. `r2_impulse_body45_daily_loss10`
   - same, but daily loss stop is -$10

3. `r2_impulse_body45_loss_cooldown240`
   - same V1 signal
   - portfolio daily guard enabled
   - after a closed losing trade, block new entries for 240 minutes

## Report Requirements

Report full-window and recent 3 months for:

- standalone V3 variants;
- each V3 variant added to current R1 plus repaired best R2 pullback.

Include trades, wins, losses, WR, W/L, PF, net, stress net after -$0.30/trade, max closed drawdown, recent 3 months, June 2026, failed checks, and exact-MT5 raw evidence paths.

## Decision

This is profit-first. Prefer a variant only if it:

- improves or closely preserves the V1 recent 3-month profit;
- improves full-window combined quality or drawdown versus V1;
- does not collapse activity;
- remains positive after -$0.30/trade stress.

No demo or forward spec may be drafted from this test without reviewer review.
