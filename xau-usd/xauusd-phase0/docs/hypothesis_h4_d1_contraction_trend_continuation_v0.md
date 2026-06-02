# H4/D1 Contraction Trend Continuation v0 Hypothesis

Hypothesis date: 2026-06-02
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 trend continuation after D1 volatility contraction
Entry / decision timeframe: D1 contraction state with H4 completed-candle decision
M5 usage: execution sequencing only inside the Phase 0 simulator
Expected median hold hours: 12-72
Expected trade count per year: 20-100
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 40%-60%
Expected worst single month: -6R to -14R
Expected max consecutive zero months: 2
Expected R-multiple distribution: lower-turnover H4 trend-continuation losses at -1R, fewer 1.70R continuation wins, and no acceptable pass if one broker or one month carries the edge
Expected median stop distance: 425 points
Measured median spread assumption: 50 points
Measured P95 spread assumption: 75 points
Expected measured median cost_R: 0.1176R
Expected measured P95 cost_R: 0.1765R
Timeframe diversification qualifies: yes, if implemented without M5 retest, round-number, fixed level, session-extreme, or same-family break/retest mechanics

## Audit Note

This is a fresh Phase 0R lower-cost replacement candidate. It is not a revision or rescue filter for `breakout_retest`, `d1_momentum_h4_pullback_v0`, `h4_d1_momentum_expansion_continuation_v0`, or `h4_d1_volatility_contraction_expansion_v0`. It tests a different post-contraction behavior: continuation after an H4 trend state and pullback/reclaim, not a single H4 expansion candle. The candidate must be SHA256-registered before any implementation or matrix run. If the first pass fails, this v0 must remain rejected unless a new versioned hypothesis is written before new tests.

## Mechanical Definition

This candidate tests whether XAUUSD H4 trend continuation is more reliable after completed D1 volatility contraction. It is slower than M5 breakout/retest mechanics and uses wider H4 invalidation so that measured 50/75-point spread remains below the +0.15R measured-cost floor target.

The mechanical setup is:

1. Market: XAUUSD only for the initial Phase 0R test.
2. Setup timeframe: D1.
3. Decision timeframe: H4 completed candle.
4. D1 contraction state: latest completed D1 ATR(14) must be in the bottom 40% of the prior 60 completed D1 ATR(14) values.
5. D1 range compression state: rolling 3-day high-low width must be below the prior 40-day median rolling 3-day width.
6. H4 trend state: H4 EMA(50) slope over the prior 6 completed H4 bars must be positive for longs or negative for shorts.
7. H4 trend quality: H4 ADX(14) must be at least 18.0 and close must be on the trend side of EMA(50).
8. Long trigger: after the D1 contraction state, the completed H4 candle must have touched or closed within 0.35 H4 ATR(14) of H4 EMA(21), then close bullish above EMA(21), with close in the upper 40% of the candle range.
9. Short trigger: after the D1 contraction state, the completed H4 candle must have touched or closed within 0.35 H4 ATR(14) of H4 EMA(21), then close bearish below EMA(21), with close in the lower 40% of the candle range.
10. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp.
11. Stop: place stop beyond the H4 pullback candle opposite extreme by 0.65 times H4 ATR(14). If computed stop distance is below 325 points, reject the setup.
12. Target: fixed 1.70R target.
13. Frequency control: at most one setup per direction per completed D1 contraction state.
14. Exclusions: no level/retest check, no round-number rule, no session filter, no spread rescue filter, no news filter, no post-result broker-specific filter.

## Expected Behavior

The candidate should win when quiet D1 volatility resolves into a clean H4 trend that pauses and continues. It should lose during failed post-contraction trend attempts that revert into range. Because it uses H4 pullback invalidation rather than tight M5 retest invalidation, measured P95 spread should remain below 0.20R for the expected median stop distance.

Expected evidence profile:

- At least 40 trades in every Phase 0R matrix cell unless a low-frequency gate is explicitly pre-registered before the run.
- PF >= 1.30 in at least 7 of 9 cells.
- Measured-cost structural and revalidation checks remain PASS using the 50/75-point spread model from the start.
- No single broker, month, or historical pocket may carry the result.
- Concentration gates must pass or a frequency-normalized concentration audit must explicitly pass.
- Manual adversarial review must confirm the trigger is not secretly a same-family level/retest.

## Why This Hypothesis Should Exist

Gold often transitions from quiet daily volatility into multi-session directional movement. A pullback/reclaim inside an established H4 trend after D1 contraction may capture the continuation leg with wider stops and lower turnover than M5 breakout/retest entries. The hypothesized edge is volatility-regime continuation, not local level acceptance.

## What Would Falsify It

The hypothesis is falsified if any of the following occur:

- Measured P95 cost_R exceeds 0.30R after implementation.
- Fewer than 7 of 9 matrix cells reach PF >= 1.30.
- The candidate fails trade-count gates without a pre-registered low-frequency gate.
- Concentration gates fail and the frequency-normalized audit does not pass.
- The candidate works only for one broker or one historical pocket.
- Measured-cost revalidation fails.
- Manual adversarial review finds hidden level/retest, same-family, or post-result filter behavior.
- Any future edit adds filters after seeing first-pass results.

## Code Mapping After Implementation

- D1 contraction feature construction: `src/phase0/strategies/h4_d1_contraction_trend_continuation_v0.py::H4D1ContractionTrendContinuationV0Strategy.prepare_features`
- D1 contraction-state classification: `src/phase0/strategies/h4_d1_contraction_trend_continuation_v0.py::H4D1ContractionTrendContinuationV0Strategy._d1_contraction_at_timestamp`
- H4 pullback/reclaim trigger: `src/phase0/strategies/h4_d1_contraction_trend_continuation_v0.py::H4D1ContractionTrendContinuationV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/h4_d1_contraction_trend_continuation_v0.py::H4D1ContractionTrendContinuationV0Strategy.build_trade_plan`
