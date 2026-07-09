# A1 XAU R2 Continuation Short V2 Repair Preregistration

Date: 2026-07-09

## Purpose

Repair the strict-R2 continuation short specialist from V1.

V1 found useful recent downtrend coverage, but failed the full-window standalone win-rate gate:

- `r2_impulse_retest_body45`: 454 trades, WR 36.34%, W/L 2.5665, PF 1.4653, net +$666.43
- last 3 months: 84 trades, WR 53.57%, W/L 2.2296, PF 2.5726, net +$669.87

The weakness is old-regime leakage: 2022-2024 produced 368 trades at WR 32.61% and PF 1.0240, while 2026 produced 86 trades at WR 52.33% and PF 2.4194.

The diagnostic showed that stronger break geometry was more promising than session filters. Broad liquid-hour filters made the full-window statistics worse, so this pass tests only signal geometry:

- minimum break distance;
- maximum break distance;
- exhaustion cap using existing `InpMaxThreeBarMoveAtr`;
- stricter body/close-location quality.

## Runtime Boundary

Research-only exact-MT5 backtest.

No demo, live, forward, broker-action, chart, preset, profile, account, position, or runtime change is authorized.

## Fixed Constraints

All variants must use:

- strict Router V1 R2 only: `InpRegimeRouterMode=2`;
- short only: `InpDirectionMode=2`;
- fixed 2R target: `InpRiskReward=2.00`;
- signal mode 19, downside impulse retest;
- no breakeven, partial close, trailing, or profit lock;
- no day, month, blocked-hour, or session masks;
- no R2 router relaxation;
- no additional H1/H4/D1 structural filter stacked on top of R2.

## Fixed Variants

Run exactly three variants:

1. `r2_impulse_break20_cap25`
   - body >= 0.45
   - close location <= 0.30
   - `InpMinBreakDistanceAtr=2.00`
   - `InpMaxBreakDistanceAtr=4.00`
   - `InpMaxThreeBarMoveAtr=2.50`

2. `r2_impulse_break15_30_cap20`
   - body >= 0.45
   - close location <= 0.30
   - `InpMinBreakDistanceAtr=1.50`
   - `InpMaxBreakDistanceAtr=3.00`
   - `InpMaxThreeBarMoveAtr=2.00`

3. `r2_impulse_q55_break20_cap25`
   - body >= 0.55
   - close location <= 0.25
   - stronger impulse threshold
   - `InpMinBreakDistanceAtr=2.00`
   - `InpMaxBreakDistanceAtr=4.00`
   - `InpMaxThreeBarMoveAtr=2.50`

## Report Requirements

Report full-window and recent 3 months for:

- standalone V2 repair variants;
- each V2 repair variant added to current R1 plus the repaired best R2 pullback sniper.

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

Label a standalone variant `REVIEW_CANDIDATE` only if it reaches:

- WR >= 50%;
- W/L >= 1.90;
- PF >= 1.50;
- net > 0;
- stress net after -$0.30/trade > 0;
- recent 3 months net >= 0;
- top10-removed net > 0;
- top3-days-removed net > 0.

Label the combined book as improved only if adding the continuation repair to current R1 plus best R2 pullback:

- increases net;
- keeps WR >= 50%;
- keeps PF >= 2.00;
- keeps recent 3 months net >= 0;
- does not worsen max closed drawdown by more than 10%.

No demo or forward spec may be drafted from this test without reviewer review.
