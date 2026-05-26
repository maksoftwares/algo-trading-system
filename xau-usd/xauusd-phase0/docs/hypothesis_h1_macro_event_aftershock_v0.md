# H1 Macro Event Aftershock v0 Hypothesis

Hypothesis date: 2026-05-26
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: scheduled macro-event aftershock continuation
Entry / decision timeframe: H1 completed-candle decision after standardized US macro event slots with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-144
Expected median hold hours: 3-12
Expected decisions per week: 0-3
Timeframe diversification qualifies: yes
Expected trade count per year: 35-110
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 45%-85%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Event aftershock attempts should have many small losses and occasional 1.35R continuation wins; reject if behavior is one-broker-only, one-event-type-only, or needs post-result changes to event timing.

## Mechanical Definition

This candidate is a research-only scheduled macro-event timing hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield/dollar proxy, breakeven-inflation, Treasury curve, credit-spread, COT positioning, GVZ, VIX, financial-conditions NFCI/ANFCI, policy-uncertainty, fixed macro-composite vote, generic price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Event calendar: deterministic standardized US macro event slots generated before the run:
   - `NFP_FIRST_FRIDAY`: first Friday of each month at 08:30 New York time.
   - `CPI_SECOND_WEDNESDAY`: second Wednesday of each month at 08:30 New York time.
   - `FOMC_THIRD_WEDNESDAY`: third Wednesday in Jan/Mar/May/Jun/Jul/Sep/Nov/Dec at 14:00 New York time.
4. DST handling: New York wall-clock event slots are converted to UTC with a fixed US DST rule before merging with H1 bars.
5. No-lookahead rule: the strategy uses only H1 bars completed after the event slot. It does not use the event outcome, released economic value, later candles, or future event results.
6. Confirmation bar: use the first H1 close at least 75 minutes after the event slot and no later than 4 hours after the event slot.
7. Pre-event reference: use the last completed H1 close before the event slot.
8. Event move: confirmation close minus pre-event close, divided by H1 ATR14 at the confirmation bar.
9. Event range: max high minus min low between the pre-event bar and the confirmation bar, divided by H1 ATR14.
10. Signal filter: absolute event move must be at least 0.08 ATR and event range must be at least 0.30 ATR.
11. Direction: continue the aftershock direction. Positive event move is long; negative event move is short.
12. Frequency control: at most one signal per generated event slot.
13. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
14. Stop: 0.95 H1 ATR14 from the estimated entry price.
15. Target: fixed 1.35R target.
16. Time stop: 144 M5 bars, matching a 12-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if scheduled macro-event timing adds information beyond ordinary hour-of-week drift and generic H1 momentum. It should fail if all strength comes from one broker, one matrix window, one event type, or an accidental DST/calendar artifact.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked event slot, first aftershock move, and H1 ATR stop/target rules.

## Why This Hypothesis Should Exist

The search has tested slow macro states and fixed macro votes without finding an approved independent EA. Scheduled high-impact US event timing is a different information class: it asks whether gold has repeatable post-event aftershock behavior even when the event outcome itself is not used.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one event type, one calendar window, or one DST conversion artifact.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the event slot definitions, confirmation timing, movement thresholds, stop size, target, or frequency rule after seeing this v0 result.
