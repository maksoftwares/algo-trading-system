# H4 Trend Pullback D1 Bias v0

Expert candidate ID: h4_trend_pullback_d1_bias_v0
Version: v0
Status: DRAFT
Mechanic family: trend continuation / pullback
Entry / decision timeframe: D1/H4
Reference timeframe: H4
Expected median hold bars M5-equivalent: 144-864
Expected median hold hours: 12-72
Expected decisions per week: 2-6
Expected trades per year: 100-300 maximum
Timeframe diversification qualifies: yes
Same-family as breakout_retest: no
Expected median stop distance points: 375
Expected median cost_R under measured P95 spread: 0.200R
Expected PF after measured cost: unproven; must meet Phase 0R matrix and measured-cost gates
Expected average net R: unproven; promotion requires >= +0.15R after measured cost
Expected win rate range: 38%-55%
Expected worst month R: -10R to -25R
Expected losing-month percentage: 40%-65%
Expected max zero-trade months: 2
Why this behavior should exist on XAUUSD: Gold trends can persist when daily moving-average structure is aligned and H4 pullbacks reset entry risk without relying on M5 confirmation.
What would falsify this hypothesis: Cost-adjusted matrix failure, decile instability, trend-state concentration, repeated stop distances below the structural cost floor, or adversarial evidence of hidden M5 behavior.
Forbidden changes after lock: Do not alter EMA periods, pullback distance, rejection candle definition, stop padding, or fixed target after seeing results.
Allowed bug fixes after lock: Correct coding mistakes that diverge from this file, missing-data handling, or passive log formatting defects.

## Mechanical Definition

Long bias requires D1 EMA(50) above EMA(200) and positive EMA(50) slope over 20 D1 bars. Short bias reverses those conditions. H4 pullback requires price within 0.5 x H4 ATR(14) of H4 EMA(21) or EMA(50) without violating the D1 trend structure.

The H4 confirmation candle must reject in the trend direction and close in the top or bottom 35% of its range. Stop projection uses the pullback swing with 0.25 x H4 ATR(14) padding. Target projection is 1.5R, with 2.0R logged only for schema comparability.
