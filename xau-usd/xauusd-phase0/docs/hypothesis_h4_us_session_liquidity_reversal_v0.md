# H4 US Session Liquidity Reversal v0 Hypothesis

Hypothesis date: 2026-05-27
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: US-session H4 volatility-exhaustion reversal
Entry / decision timeframe: H4 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 96-576
Expected median hold hours: 8-48
Expected decisions per week: 0-5
Timeframe diversification qualifies: yes
Expected trade count per year: 30-160
Expected cost-adjusted PF: 1.00-1.40
Expected losing-month percentage: 45%-85%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small losses and time stops with occasional 1.35R reversals after unusually stretched US-session H4 candles; reject if the behavior is one-broker-only, one-window-only, or needs post-result changes to session hours or thresholds.

## Mechanical Definition

This candidate is a research-only US-session H4 liquidity-run reversal hypothesis. It is not a breakout-retest, swing retest, round-number retest, previous-day extreme retest, VWAP reclaim, trend-pullback, range mean-reversion, squeeze breakout, macro-proxy, XAU/XAG relative-value, FX-divergence, learned-state, scheduled event, or same-family breakout continuation strategy.

The locked v0 setup is:

1. Market: XAUUSD.
2. Decision timeframe: completed H4 candles.
3. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
4. Session filter: the H4 candle must close at 16:00 UTC or 20:00 UTC, a fixed approximation of the US cash/NY active session. No DST optimization is allowed in v0.
5. ATR filter: H4 true range must be at least 1.35 x H4 ATR14 at the completed H4 candle.
6. Upside liquidity run: current H4 high must exceed the previous 20 completed H4 highs by at least 0.05 x H4 ATR14.
7. Downside liquidity run: current H4 low must undercut the previous 20 completed H4 lows by at least 0.05 x H4 ATR14.
8. Short reversal trigger: upside liquidity run, bearish H4 close, close position at or below 35% of the candle range, and upper-wick ratio at or above 35%.
9. Long reversal trigger: downside liquidity run, bullish H4 close, close position at or above 65% of the candle range, and lower-wick ratio at or above 35%.
10. Frequency control: maximum one signal per UTC day.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: beyond the H4 liquidity-run extreme plus 0.15 x H4 ATR14.
13. Target: fixed 1.35R target.
14. Time stop: 12 H4 bars, implemented as 576 M5 execution bars.
15. No news filter, no router filter, no spread-adaptive threshold, and no post-result parameter changes are allowed in v0.

## Expected Behavior

The candidate should only pass if US-session H4 liquidity shocks have a repeatable exhaustion component that is different from the approved breakout-retest family. It should fail if the apparent edge is only a thin high-frequency artifact, a single broker/window effect, or a re-labeled level-retest behavior.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell if the frequency is sufficient.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked US-session H4 range expansion, extreme sweep, close-back-inside, fixed stop, fixed target, and fixed time-stop rules.

## Why This Hypothesis Should Exist

Gold often reprices sharply during US liquidity windows. Some large H4 session candles may represent late forced flow or stop-seeking behavior that exhausts once the candle closes back inside its own range. This hypothesis tests whether that exhaustion is repeatable without using a retest entry, a continuation thesis, or external macro data.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has insufficient trade count under the existing Phase 0 gate.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one matrix window, one UTC hour, or one isolated market episode.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the session hours, ATR multiple, sweep threshold, close-back fraction, wick threshold, stop buffer, target, time stop, or one-trade-per-day rule after seeing this v0 result.
