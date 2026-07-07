# A1 XAU Short Specialist Review Prompt

We need strategic review and direction for building a true XAUUSD short-trade specialist.

## Context

We are trying to build two parallel specialist branches:

1. Long/uptrend specialist
   - This is where we have found real edge.
   - The useful core is the H4/D1 long box/supportive-guard style.
   - Current repaired/supportive baseline:
     - 3645 signals
     - WR 50.40%
     - W/L 2.0895
     - PF 2.1395
     - Net +20701.41 USD
     - Active weekdays 85.71%
     - Stress W/L at -0.30 USD/trade: 1.9720
   - The concentrated long profit engine `h4_d1_long_best_box2_atr80` was much stronger but lower-frequency:
     - 332 trades
     - WR about 57.5%
     - PF about 3.09
     - Net about +15614 USD

2. Short/downtrend specialist
   - This is what we are now trying to build.
   - Goal is not to add random short trades.
   - Goal is a genuine short expert that can run alongside the long expert.
   - Ideally it should replicate as much as possible of the long branch's properties:
     - WR near or above 50%
     - W/L near or above 2.0
     - PF meaningfully above 1.2, ideally much higher
     - enough frequency to improve combined activity
     - no damage to weekly/monthly shape
     - exact-MT5 verified, not Python-only

## What We Tested

We tried several short-only bearish-D1 exact-MT5 variants using the existing A1 framework.

Best initial bearish clue, `down_m5_ema_h1h4_short_rr2`:

- 438 trades
- WR 33.11%
- W/L 2.1595
- PF 1.0687
- Net +137.34 USD
- Recent 3M +258.45 USD
- Problem: low WR, weak PF, poor standalone quality

More-trade / improvement pass:

- Best net/payoff was `bear_break_run_h1h4_rr2`
- 445 trades
- WR 32.13%
- W/L 2.3536
- PF 1.1144
- Net +208.00 USD
- Problem: WR got worse

Quality-first short pass:

- `bear_quality_m5_ema_slope50`: 209 trades, WR 30.14%, W/L 1.9311, net -114.17 USD
- `bear_quality_m5_ema_slope100`: 134 trades, WR 28.36%, W/L 1.8855, net -113.67 USD
- `bear_quality_break_run_tight`: 192 trades, WR 27.60%, W/L 2.0058, net -145.26 USD
- `bear_quality_h4_pullback_d1bias`: 18 trades, WR 33.33%, W/L 2.6756, PF 1.3378, net +51.40 USD, but too sparse
- Verdict: tightening the same short-continuation family reduced trades but did not improve WR

## Current Conclusion

The short side probably should not be a simple mirror of the long/uptrend engine.

Gold shorts may need structurally different logic:

- failed rallies
- lower-high rejection
- breakdown retest
- shorting relief bounces, not chasing extended breakdowns
- avoiding late stretched shorts
- regime-specific bearish behavior
- using H4/D1 context differently than the long branch

## Reviewer Request

Please advise how to design a true XAUUSD short-trade specialist.

Questions:

1. What structural short setup is most likely to produce WR near 50% while keeping W/L near 2.0?
2. Should the short expert be breakdown retest, failed rally/lower-high rejection, H4 resistance rejection, D1/H4 bearish pullback continuation, liquidity sweep above prior highs then bearish reclaim, or something else?
3. What exact preregistered MT5 tests would you run next, limited to 3-5 fixed variants, without grid overfitting?
4. What filters are structurally justified for gold shorts: D1 bearish EMA state, H4 lower-high structure, ATR expansion/contraction, session restrictions, avoiding shorts after large 3-bar selloffs, requiring retest into EMA/resistance?
5. What should the pass/fail gates be for a standalone short expert before combining with the long expert?
6. What should the combined long+short portfolio gates be?
7. Are we wrong to expect the short specialist to match the long branch's WR/PF/frequency, given gold's long-bias behavior?
8. If matching the long branch is unrealistic, what is the best practical role for the short branch: true profit engine, drawdown hedge, red-week repair source, or low-frequency bear-regime add-on?
9. What should we explicitly avoid because it is likely overfit?
10. Please give a concrete next-step plan: exact MT5 only, no live/demo runtime, no post-hoc hour/month tuning.

Important constraint: we want clear direction, not another broad parameter sweep. The next work should be a small, preregistered, structurally defensible short-specialist design that can be audited.
