# Weekly Level H4 Rejection v0

Expert candidate ID: weekly_level_h4_rejection_v0
Version: v0
Status: DRAFT
Mechanic family: higher-timeframe rejection / mean reversion
Entry / decision timeframe: W1/D1/H4
Reference timeframe: H4
Expected median hold bars M5-equivalent: 288-1440
Expected median hold hours: 24-120
Expected decisions per week: 0-3
Expected trades per year: <150
Timeframe diversification qualifies: yes
Same-family as breakout_retest: no
Expected median stop distance points: 425
Expected median cost_R under measured P95 spread: 0.176R
Expected PF after measured cost: unproven; must meet Phase 0R matrix and measured-cost gates
Expected average net R: unproven; promotion requires >= +0.15R after measured cost
Expected win rate range: 40%-58%
Expected worst month R: -8R to -20R
Expected losing-month percentage: 40%-65%
Expected max zero-trade months: 3
Why this behavior should exist on XAUUSD: Gold often reacts around completed weekly highs, lows, and four-week structure as larger participants defend or fade stretched moves.
What would falsify this hypothesis: Failure after measured cost, evidence that signals are just M5 breakout-retest behavior in disguise, insufficient sparse sample, or concentration around one calendar regime.
Forbidden changes after lock: Do not change the weekly level set, touch zone, wick/body rejection threshold, stop padding, or target rule after seeing results.
Allowed bug fixes after lock: Correct implementation mistakes, timestamp alignment defects, or passive CSV schema defects that do not alter the setup definition.

## Mechanical Definition

Levels are the previous completed weekly high or low and the prior 4-week high or low. H4 touch occurs when the candle trades into a level zone within 0.25 x H4 ATR(14). Rejection requires wick rejection at least 1.5 x body and H4 close away from the level in the rejection direction.

The observer records theoretical entry at H4 close. Stop projection is beyond the rejection wick by 0.25 x H4 ATR(14). Target projection is fixed at 1.5R, with 2.0R logged for schema comparability.
