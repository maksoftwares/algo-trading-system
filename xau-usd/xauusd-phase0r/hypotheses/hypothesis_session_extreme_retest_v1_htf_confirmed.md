# Session Extreme Retest v1 HTF Confirmed

Expert candidate ID: session_extreme_retest_v1_htf_confirmed
Version: v1
Status: DRAFT
Mechanic family: session extreme rejection / higher-timeframe confirmed retest
Entry / decision timeframe: D1/H4/M15
Reference timeframe: H4
Expected median hold bars M5-equivalent: 72-576
Expected median hold hours: 6-48
Expected decisions per week: 1-5
Expected trades per year: <120
Timeframe diversification qualifies: no
Same-family as breakout_retest: yes
Expected median stop distance points: 500
Expected median cost_R under measured P95 spread: 0.150R
Expected PF after measured cost: unproven; must meet Phase 0R matrix and measured-cost gates
Expected average net R: unproven; promotion requires >= +0.15R after measured cost
Expected win rate range: 38%-55%
Expected worst month R: -8R to -18R
Expected losing-month percentage: 40%-65%
Expected max zero-trade months: 3
Why this behavior should exist on XAUUSD: Gold session extremes often mark liquidity sweeps, but the weak v0 sample suggests the raw session-extreme trigger is too permissive. A higher-timeframe rejection requirement should keep only extremes that align with broader auction failure instead of fading every local stretch.
What would falsify this hypothesis: Failure after measured cost, p95 cost_R above 0.30R, duplicate-family exposure not reduced versus v0, losses still clustered in ASIA or OFF_HOURS, or no improvement in net expectancy after deduplication.
Forbidden changes after lock: Do not change the HTF confirmation rule, minimum stop geometry, duplicate-suppression rule, session eligibility, target model, or cost_R ceiling after seeing results.
Allowed bug fixes after lock: Correct timestamp alignment defects, session-label mapping errors, duplicate-key defects, or passive CSV schema defects that do not alter the setup definition.

## Failure Addressed

The current `session_extreme_retest_v0` demo sample is weak, especially on XAUUSD, and it contributed a material share of actual demo losses. The v1 candidate is not a direct tune of v0. It is a new hypothesis that asks whether session-extreme retests need higher-timeframe confirmation and cleaner cost geometry to be testable.

## Mechanical Definition

A candidate setup may only be considered when all of these are true:

- The symbol is XAUUSD.
- The event occurs during LONDON or NY, not ASIA, ROLLOVER, or OFF_HOURS.
- Price sweeps the current session high or low and then closes back inside the prior session extreme zone.
- H4 context shows rejection in the same direction: either a close back inside the prior H4 range after a sweep or a wick/body rejection at least 1.5 x body.
- D1 context is not strongly trending against the intended fade, based on D1 close location and EMA slope.
- Expected stop distance is at least 450 points, with 500 points as the median planning assumption.
- Projected measured P95 cost_R is <= 0.30R.
- Same-family duplicate exposure is suppressed. If a canonical or accepted same-family row fires on the same bar, symbol, and direction, v1 is logged as blocked rather than counted as independent exposure.

## Scoring Notes

The setup is still same-family until proven otherwise. It cannot be counted as diversification, cannot reopen Phase 2, and cannot be promoted from demo observations alone.

The first valid test must report:

- raw and deduplicated trade counts
- win rate and net expectancy_R after measured cost
- session buckets
- stop-distance buckets
- duplicate-family blocked rows
- loss-quality classes
- concentration by day, week, and month
