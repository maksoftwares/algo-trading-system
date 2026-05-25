# H4 VIX Risk-Off Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: equity-risk implied-volatility / risk-off gold reversal
Entry / decision timeframe: H4 completed-candle decision with daily VIX state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-220
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Risk-off/risk-relief reversal attempts should have frequent small failures and fewer 1.55R wins; reject if the behavior is one-crisis-only, one-broker-only, or needs post-result threshold edits.

## Mechanical Definition

This candidate is a research-only equity-risk implied-volatility hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield proxy, COT positioning, gold-options GVZ implied volatility, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External risk source: FRED `VIXCLS`, the CBOE Volatility Index daily close.
4. No-lookahead rule: VIX daily close features are shifted by one observation before they are merged into H4 bars. An H4 decision can only use prior published VIX closes, not the same-day close.
5. VIX features:
   - daily VIX close
   - 5-business-day VIX log return
   - 252-business-day rolling percentile of VIX close
   - 126-business-day z-score of the 5-business-day VIX return
6. Long risk-off state: shifted VIX percentile is at or above 0.60, and either shifted 5-day VIX return is at least 0.04 or shifted 5-day VIX-return z-score is at least 0.50.
7. Long H4 confirmation: 12-H4 log return is at or below -0.003, the completed H4 candle is bullish, the close is in the upper 45% of the candle range, and the close is not more than 0.75 H4 ATR14 below EMA40.
8. Short risk-relief state: shifted 5-day VIX return is at or below -0.04 with shifted VIX percentile at or below 0.45, or shifted 5-day VIX-return z-score is at or below -0.65.
9. Short H4 confirmation: 12-H4 log return is at or above 0.003, the completed H4 candle is bearish, the close is in the lower 45% of the candle range, and the close is not more than 0.75 H4 ATR14 above EMA40.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.15 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.55R target.
14. Time stop: 288 M5 bars, matching a 24-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if equity-index implied-volatility stress adds information beyond spot-gold price structure and survives across Capital.com, Pepperstone, and Dukascopy windows after costs. It should fail if VIX is too indirect for XAUUSD, only marks crisis clusters, or merely duplicates broad volatility already visible in gold bars.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked VIX state plus H4 reversal confirmation.

## Why This Hypothesis Should Exist

The search has exhausted XAU-only structure, intermarket XAG/FX, learned-state, real-yield macro, futures-positioning COT, and gold-options GVZ lanes without finding an independent EA. VIX is a separate information class: equity-options market-implied risk stress, used here as a cross-asset risk-off/risk-relief proxy rather than another gold-specific input.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one VIX crisis episode, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the VIX thresholds, H4 reversal rule, stop size, target, or frequency rule after seeing this v0 result.
