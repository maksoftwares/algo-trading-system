# XAU XAG FX Composite Reversion v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: intermarket composite relative-value reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-288
Expected median hold hours: 3-24
Expected decisions per week: 2-20
Timeframe diversification qualifies: yes
Expected trade count per year: 80-600
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small failed reversion entries, fewer +1.55R winners, and rejection if the edge only exists in one broker/date window.

## Mechanical Definition

This candidate is a research-only H1 intermarket composite reversion hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Required proxy inputs: broker-consistent XAGUSD H1 bars plus broker-consistent EURUSD and USDJPY H1 bars for the same Phase 0 cell.
4. XAU/XAG features: 24-hour XAU and XAG log returns, rolling XAU-vs-XAG beta residual, XAU/XAG log-ratio z-score, and 3-hour ratio-z change.
5. FX proxy features: 24-hour USD proxy return defined as the average of negative EURUSD return and USDJPY return, plus rolling USD-proxy z-score.
6. Long setup: XAU is cheap versus XAG by residual or ratio z-score, USD proxy pressure is weak or negative, the current H1 candle is bullish, and XAU is not deeply below its H1 EMA20.
7. Short setup: XAU is rich versus XAG by residual or ratio z-score, USD proxy pressure is strong or positive, the current H1 candle is bearish, and XAU is not deeply above its H1 EMA20.
8. Frequency control: at most one signal per UTC day and direction.
9. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
10. Stop: 1.05 H1 ATR from estimated entry.
11. Target: fixed 1.55R target.
12. Time stop: 288 M5 bars, matching a 24-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if combining silver relative value with a dollar-pressure filter improves cross-venue robustness over the individually rejected `xau_xag_relative_value_v0` and `gold_fx_proxy_divergence_v0` candidates. It should fail if the composite is merely a narrower version of either rejected single-proxy idea.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked XAU/XAG and FX-proxy composite rule.

## Why This Hypothesis Should Exist

The project needs a genuinely independent non-level behavior family. The two existing intermarket candidates each tested a single proxy lane and failed. This hypothesis tests whether a stricter composite signal, requiring both relative-value dislocation and dollar-pressure confirmation, can produce a more robust edge without touching active Phase 1 runtime code.

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
- Any future improvement changes the proxy set, thresholds, stop size, target, or frequency rule after seeing this v0 result.
