# H4/D1 Volatility Contraction Expansion v0 Hypothesis

Hypothesis date: 2026-06-02
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4/D1 volatility contraction then expansion
Entry / decision timeframe: D1 state with H4 completed-candle decision
M5 usage: execution sequencing only inside the Phase 0 simulator
Expected median hold hours: 12-96
Expected trades per year: 15-80
Expected median stop distance: 400 points
Measured median spread assumption: 50 points
Measured P95 spread assumption: 75 points
Expected measured median cost_R: 0.1250R
Expected measured P95 cost_R: 0.1875R
Timeframe diversification qualifies: yes, if implemented without M5 retest, round-number, session-extreme, or same-family level/retest mechanics

## Audit Note

This is a fresh Phase 0R lower-cost replacement candidate. It is not a revision or rescue filter for `breakout_retest`, `d1_compression_h4_expansion_v0`, or any other failed v0 candidate. The candidate must be SHA256-registered before any matrix run. If the first pass fails, this v0 must remain rejected unless a new versioned hypothesis is written before new tests.

## Mechanical Definition

This candidate tests whether XAUUSD continuation after a completed H4 expansion candle is more reliable when that candle follows a multi-day volatility contraction state. It is deliberately slower than the M5 breakout-retest family and is designed to survive the measured 50/75-point spread environment through wider stops and lower turnover.

The mechanical setup is:

1. Market: XAUUSD only for the initial Phase 0R test.
2. Setup timeframe: D1.
3. Decision timeframe: H4 completed candle.
4. D1 contraction state: the latest completed D1 bar must have D1 ATR(14) in the bottom 35% of the prior 60 completed D1 ATR(14) values.
5. D1 range compression state: the rolling 3-day high-low width must be below the prior 40-day median rolling 3-day width.
6. Long trigger: the completed H4 candle must close above its open, have range >= 1.20 times H4 ATR(14), and close in the upper 30% of its range.
7. Short trigger: the completed H4 candle must close below its open, have range >= 1.20 times H4 ATR(14), and close in the lower 30% of its range.
8. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp.
9. Stop: place the stop beyond the H4 expansion candle opposite extreme by 0.35 times H4 ATR(14). If the computed stop distance is below 300 points, reject the setup.
10. Target: fixed 1.60R target.
11. Frequency control: at most one setup per direction per completed D1 contraction state.
12. Exclusions: no level/retest check, no round-number rule, no session filter, no spread rescue filter, no news filter, no post-result broker-specific filter.

## Expected Behavior

Expected behavior is sparse and regime-dependent. The candidate should lose during false expansion candles that immediately revert back into compression, and should win when the expansion candle starts a multi-session directional release. Because stops are expected to be materially wider than M5 retest variants, measured P95 spread should stay below 0.20R for the expected median stop distance.

Expected evidence profile:

- At least 40 trades in every Phase 0R matrix cell unless a low-frequency gate is explicitly pre-registered before the run.
- PF >= 1.30 in at least 7 of 9 cells.
- Measured-cost revalidation PASS using the 50/75-point spread model from the start.
- No single broker or time-slice pocket may carry the result.
- Concentration gates must pass or a frequency-normalized concentration audit must explicitly pass.
- Manual adversarial review must confirm the trigger is not secretly a same-family retest.

## Why This Hypothesis Should Exist

Gold can move from quiet multi-day compression into directional repricing when macro expectations, liquidity, and positioning adjust after a low-volatility period. A completed H4 expansion candle after a D1 contraction state is a slower, wider-stop expression of volatility release. It is expected to be less sensitive to retail spread than M5 retest mechanics because it avoids tight invalidation and rapid turnover.

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

- D1 contraction feature construction: `src/phase0/strategies/h4_d1_volatility_contraction_expansion_v0.py::H4D1VolatilityContractionExpansionV0Strategy.prepare_features`
- D1 contraction-state classification: `src/phase0/strategies/h4_d1_volatility_contraction_expansion_v0.py::H4D1VolatilityContractionExpansionV0Strategy._d1_contraction_at_timestamp`
- H4 expansion trigger: `src/phase0/strategies/h4_d1_volatility_contraction_expansion_v0.py::H4D1VolatilityContractionExpansionV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/h4_d1_volatility_contraction_expansion_v0.py::H4D1VolatilityContractionExpansionV0Strategy.build_trade_plan`
