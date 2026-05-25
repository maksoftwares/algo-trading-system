# D1 W1 Momentum H4 Pullback v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: cross-scale higher-timeframe momentum pullback
Entry / decision timeframe: H4 completed-candle trigger inside D1 and weekly-scale D1 momentum state
Expected median hold bars M5-equivalent: 96-576
Expected median hold hours: 8-48
Expected decisions per week: 0-3
Timeframe diversification qualifies: yes
Expected trade count per year: 35-140
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -6R to -16R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Low-frequency trend-pullback losses near -1R, fewer +1.75R continuation wins, and rejection if one broker or one calendar window dominates.

## Mechanical Definition

This candidate is a research-only XAUUSD higher-timeframe momentum-pullback hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, intermarket proxy, calendar-drift, or intraday impulse strategy.

The locked v0 setup is:

1. Market and state timeframe: XAUUSD D1 completed bars.
2. Weekly-scale proxy: D1 20-bar momentum represents the W1-scale direction without requiring a separate W1 feed.
3. Trigger timeframe: H4 completed bars pull back to H4 EMA20 and reclaim in the D1/W1 direction.
4. Long state: D1 close above EMA20 above EMA50, EMA20 slope over 5 D1 bars positive, D1 5-bar momentum at least 0.20 ATR, and D1 20-bar momentum at least 1.00 ATR.
5. Short state: symmetric bearish D1 trend and momentum requirements.
6. Long trigger: completed H4 bar pulls to EMA20, closes back above EMA20, closes above its open and previous H4 close, and has body ratio at least 0.22.
7. Short trigger: symmetric bearish H4 pullback and reclaim.
8. Frequency control: at most one signal per UTC ISO week.
9. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
10. Stop: beyond the H4 pullback extreme plus a 0.25 H4 ATR buffer.
11. Target: fixed 1.75R target.

## Expected Behavior

The candidate should only work if D1 trend plus weekly-scale momentum improves the weaker higher-timeframe pullback attempts already seen in the research bench. It should lose during late-trend exhaustion and choppy weekly transitions.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by D1 trend, D1 20-bar momentum, and H4 pullback mechanics.

## Why This Hypothesis Should Exist

The strongest independent non-level attempts so far were higher-timeframe momentum behaviors, but single-timeframe versions were not robust enough. This hypothesis tests whether requiring both D1 trend structure and a weekly-scale momentum proxy filters out weak pullbacks without becoming a level/retest strategy.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds retest, fixed-level, round-number, session-extreme, cross-symbol, or discretionary news filters after results are known.
