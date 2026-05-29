# Quarter Round Retest v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Same-family level-and-pullback / round-number retest
Entry / decision timeframe: M5 breakout/retest decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 6-96
Expected median hold hours: 0.5-8
Expected decisions per week: 10-80
Timeframe diversification qualifies: no
Expected trade count per year: 800-8000
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 35%-70%
Expected worst single month: -15R to -35R
Expected max consecutive zero months: 0
Expected R-multiple distribution: Many small 1R losses, many 1.50R target winners, and enough observations to expose cost sensitivity. Reject if results require changing increments, break/retest logic, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is not an independent diversification candidate. It is a same-family level-and-pullback candidate intended to test whether denser quarter-round levels can become an additional future EA candidate. It must not be counted as portfolio diversification.

## Mechanical Definition

`quarter_round_retest_v0` inherits the locked breakout/retest state machine used by the round-number retest family, but replaces the level set with denser symbol-scaled quarter-round levels.

For XAUUSD:

- 5.0
- 10.0
- 25.0
- 50.0

For symbols with smaller point sizes, the increments are scaled mechanically:

- point size <= 0.0001: 0.0025, 0.0050, 0.0100, 0.0250
- point size < 0.005: 0.25, 0.50, 1.00, 2.50
- otherwise: 5.0, 10.0, 25.0, 50.0

Signal rules:

1. Use the existing M5 breakout/retest state machine.
2. Candidate long levels are round levels below current close.
3. Candidate short levels are round levels above current close.
4. Levels closer than 10 points to a kept level are de-duplicated.
5. Entry, stop, target, retest, confirmation, and one-open-position rules are inherited from the existing breakout/retest implementation.

## Expected Behavior

Expected trade count: high enough to clear all 9 matrix trade-count cells.
Expected PF: at least 1.30 in 7 of 9 matrix cells if denser quarter-round levels preserve the same structural behavior as the approved round-number family.
Expected losing-month percentage: below 50%.
Expected worst month: no worse than -20R on fixed-notional reporting.
Expected zero-trade months: none.

## Why This Hypothesis Should Exist

The current evidence says level-and-pullback retests are the only robust family in the available XAUUSD data. `round_number_retest_v0`, `symbol_normalized_round_retest_v0`, and `session_extreme_retest_v0` show that mechanical level retests can survive the automated gates, though they do not diversify the portfolio. A denser quarter-round level set tests whether the same mechanism remains robust when the level universe is expanded mechanically rather than hand-picked.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- decile persistence fails
- multisymbol transfer or XAU-specific defense fails
- manual adversarial review finds more than 25% logic-gap losses

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
