# A1 XAU R2 Continuation Short V1 Preregistration

Date: 2026-07-09

## Purpose

Build one additional strict-R2 short specialist to complement the repaired R2 pullback-rejection sniper.

The V2 pullback repair reached the desired quality profile on the best variant, but it is intentionally low frequency:

- `r2_h1_m5_body58_hours05_18`
- 63 trades
- WR 52.38%
- W/L 2.1721
- PF 2.3893
- net +$334.23
- recent 3 months: 4 trades, WR 100%, net +$148.48

This pass tests whether a separate R2 continuation/breakdown-retest specialist can add activity without relaxing the R2 regime router or reducing the 2R objective.

## Runtime Boundary

Research-only exact-MT5 backtest.

No demo, live, forward, broker-action, chart, preset, profile, account, position, or runtime change is authorized.

## Fixed Constraints

All variants must use:

- strict Router V1 R2 only: `InpRegimeRouterMode=2`;
- short only: `InpDirectionMode=2`;
- fixed 2R target: `InpRiskReward=2.00`;
- no breakeven, partial close, trailing, or profit lock;
- no day, month, or blocked-hour masks;
- no R2 router relaxation;
- no H1/H4/D1 structural filters stacked on top of R2.

The strict R2 router is the regime filter. The M5 breakdown/retest signal is responsible for execution quality.

## Fixed Variants

Run exactly three variants:

1. `r2_break_retest_body45`
   - signal mode 15, bear breakdown retest
   - M5 bearish body fraction >= 0.45
   - close location <= 0.30
   - broad activity candidate

2. `r2_impulse_retest_body45`
   - signal mode 19, downside impulse retest
   - M5 bearish body fraction >= 0.45
   - close location <= 0.30
   - impulse break requirement enabled

3. `r2_impulse_retest_q55`
   - signal mode 19, downside impulse retest
   - M5 bearish body fraction >= 0.55
   - close location <= 0.25
   - stronger impulse threshold
   - quality candidate

## Report Requirements

Report full-window and recent 3 months for:

- standalone continuation variants;
- each continuation variant added to the current R1 book plus the repaired best R2 pullback sniper.

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

This is a second R2 specialist diagnostic.

Label a standalone variant `REVIEW_CANDIDATE` only if it reaches:

- WR >= 50%;
- W/L >= 1.90;
- PF >= 1.50;
- net > 0;
- stress net after -$0.30/trade > 0;
- recent 3 months net >= 0;
- top10-removed net > 0;
- top3-days-removed net > 0.

Label the full R2 combination as improved only if adding the continuation specialist to current R1 plus best R2 pullback:

- increases net;
- keeps WR >= 50%;
- keeps PF >= 2.00;
- keeps recent 3 months net >= 0;
- does not worsen max closed drawdown by more than 10%.

No demo or forward spec may be drafted from this test without reviewer review.
