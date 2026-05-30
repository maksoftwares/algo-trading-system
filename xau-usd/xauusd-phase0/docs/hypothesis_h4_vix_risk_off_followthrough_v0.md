# H4 VIX Risk-Off Followthrough v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: VIX equity-risk implied-volatility followthrough
Entry / decision timeframe: H4 completed-candle decision with daily VIX state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-144
Expected median hold hours: 6-12
Expected decisions per week: 0-5
Timeframe diversification qualifies: yes
Expected trade count per year: 40-250
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 35%-65%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, a smaller set of 1.50R continuation wins, and some time stops around flat-to-small loss. Reject if results require changing VIX thresholds, H4 momentum rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Pre-Registration Statement

This candidate is a research-only equity-risk implied-volatility followthrough hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield/dollar proxy, COT positioning, GVZ premium, financial-conditions, price-only squeeze, calendar-drift, or learned-state strategy.

The prior `h4_vix_risk_off_reversal_v0` attempt is rejected. This v0 followthrough candidate does not tune that rejected reversal after seeing the result; it tests the distinct opposite mechanism: when broad equity-risk implied volatility is already stressed and H4 gold momentum confirms safe-haven demand, does XAUUSD continue rather than reverse?

## Mechanical Definition

1. Use XAUUSD H4 completed candles for decisions.
2. Use M5 bars only for execution simulation after a signal.
3. External risk source: FRED `VIXCLS`, the CBOE Volatility Index daily close.
4. No-lookahead rule: VIX daily close features are shifted by one observation before merging into H4 bars.
5. VIX features:
   - daily VIX close
   - 5-business-day VIX log return
   - 252-business-day rolling percentile of VIX close
   - 126-business-day z-score of the 5-business-day VIX return
6. Long risk-off state:
   - shifted VIX percentile >= 0.60
   - and shifted 5-day VIX return >= 0.04 or shifted 5-day VIX-return z-score >= 0.50
7. Long price confirmation:
   - 12-H4-bar XAU log return >= 0.003
   - completed H4 candle closes above its open
   - close location within the H4 candle range >= 0.58
   - H4 close >= H4 EMA40
8. Short risk-relief state:
   - shifted VIX percentile <= 0.45 with shifted 5-day VIX return <= -0.04
   - or shifted 5-day VIX-return z-score <= -0.65
9. Short price confirmation:
   - 12-H4-bar XAU log return <= -0.003
   - completed H4 candle closes below its open
   - close location within the H4 candle range <= 0.42
   - H4 close <= H4 EMA40
10. Only one signal per UTC day and direction is allowed.
11. Entry type: market at the next executable M5 sequence after the H4 signal.
12. Stop: 1.10 * H4 ATR(14).
13. Target: 1.50R.
14. Planned time stop: 6 H4 bars.
15. Max holding window for M5 simulation: 288 M5 bars.
16. No parameter may be changed after first-pass evidence without creating a new versioned hypothesis.

## Expected Behavior

Expected trade count: moderate H4 frequency, likely 40-250 trades per 3-year broker cell if VIX stress and H4 followthrough states occur often enough.
Expected PF: at least 1.30 in 7 of 9 broker-cost cells if the effect is real.
Expected losing-month percentage: below 45%.
Expected worst month: not worse than -10R.
Expected max zero-trade months: no more than 3.
Expected R-multiple distribution: many 1R losses, a smaller set of 1.50R continuation wins, and some time stops around flat-to-small loss.

## Why This Hypothesis Should Exist

VIX is a broad equity-index implied-volatility stress measure. During some risk-off regimes, gold may receive safe-haven demand at the same time equity volatility rises. The rejected reversal lane tested whether gold fades after VIX stress. This lane tests the opposite: when VIX stress is high and H4 gold has already confirmed direction above/below EMA40, continuation may persist for another H4 impulse.

The candidate should only pass if shifted VIX state adds information beyond spot-gold price structure and survives across Capital.com, Pepperstone, and Dukascopy windows after costs.

## What Would Falsify It

Reject the candidate if any of the following happen:

- Fewer than 7 of 9 broker-cost matrix cells reach PF >= 1.30.
- Any required matrix gate fails.
- Trade count is below 40 in any core matrix cell.
- Max zero-trade months exceed 3.
- Concentration fails because one trade, top five trades, or one month explain too much of the result.
- Any pass comes from one broker, one VIX crisis cluster, or one calendar window.
- The strategy requires changing VIX thresholds, H4 momentum rules, stop size, target, or time stop after first-pass evidence.

## Audit Boundary

This candidate is not authorized for Phase 1, Phase 2, Phase 3, demo attachment, or live trading unless it completes the full Phase 0 research path. A first-pass failure permanently rejects this exact v0 definition.
