# A1 XAU M5 Missing-Regime Bounded Discovery Preregistration

Date: `2026-07-13`

Status: `FROZEN_BEFORE_BOUNDED_DISCOVERY_MT5_EXECUTION`

## Purpose

Existing M5 profiles produced one ten-year-confirmed R2/DOWNTREND specialist.
R1 was profitable but its ten-year PF fell to `1.14`; R3 was either too sparse
or low-PF; R4 trend and sweep mechanisms lost money. This final bounded set
tests the mechanism implied by each failure without running a broad optimizer.

## Frozen candidates

### R1 UPTREND

The five-year V3 result passed at `0.7R` but ten-year PF failed. Test the fixed
neighbor bracket only: the same entry and hour mask at `0.6R` and `0.8R`.

### R3 COMPRESSION

- six-bar compression, maximum range `1.60 ATR`, break `0.05 ATR`, `0.6R`;
- four-bar compression, maximum range `2.00 ATR`, break `0`, `0.7R`;
- V4-hour-masked break release at `0.7R`.

All are both-direction M5 entries owned only by R3.

### R4 CHOP

Test three true M5 mean-reversion events at `0.7R`: opening-range reversal,
prior-day reclaim with `InpPriorDayLevelMode=1`, and daily-extreme reclaim.
All use the fixed V13 general hour mask and R4 as sole owner.

## Frozen validation

Five years (`2021-07-01` through `2026-07-01`), XAUUSD M5, every tick,
`$1,000 USD`, fixed `0.01 lot`, one position, quality `>=98%`.

Every gate must pass: at least `100` trades, PF `>=1.20`, win rate `>=35%`,
positive net, and relative equity DD `<=20%`. Any five-year survivor is rerun
unchanged for ten years. SHOCK remains no-trade. No demo/live authorization is
created by this phase.
