# D1 Compression H4 Expansion v0

Expert candidate ID: d1_compression_h4_expansion_v0
Version: v0
Status: DRAFT
Mechanic family: volatility expansion / compression-release
Entry / decision timeframe: D1/H4
Reference timeframe: H4
Expected median hold bars M5-equivalent: 288-1152
Expected median hold hours: 24-96
Expected decisions per week: 0-2
Expected trades per year: <100
Timeframe diversification qualifies: yes
Same-family as breakout_retest: no
Expected median stop distance points: 500
Expected median cost_R under measured P95 spread: 0.150R
Expected PF after measured cost: unproven; must meet Phase 0R matrix and measured-cost gates
Expected average net R: unproven; promotion requires >= +0.15R after measured cost
Expected win rate range: 35%-50%
Expected worst month R: -8R to -22R
Expected losing-month percentage: 45%-70%
Expected max zero-trade months: 3
Why this behavior should exist on XAUUSD: Gold can reprice directionally after multi-day volatility compression when macro expectations or positioning force a release.
What would falsify this hypothesis: Failure of matrix, decile, measured-cost, or adversarial gates; concentration in one event cluster; or observed stops too tight for measured cost.
Forbidden changes after lock: Do not change ATR percentile, compression-box logic, H4 body threshold, stop rule, or target logging after seeing results.
Allowed bug fixes after lock: Correct implementation errors that diverge from this file, logging schema mistakes, or deterministic timestamp handling defects.

## Mechanical Definition

D1 compression requires D1 ATR(14) percentile over 252 trading days at or below the 30th percentile and a 5-day D1 range that narrows versus the 20-day median range. The H4 trigger is a completed candle closing outside the 5-day compression box with body at least 50% of candle range.

The observer records theoretical entry at H4 close. Stop projection uses the opposite side of the compression box or 1.0 x H4 ATR(14), whichever is wider. Targets at 1.5R and 2.0R are logged for analysis only.
