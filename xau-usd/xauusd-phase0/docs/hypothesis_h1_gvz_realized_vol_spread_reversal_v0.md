# H1 GVZ Realized Vol Spread Reversal v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: options-implied versus realized volatility spread reversal
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 40-500
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, occasional 1.50R reversals when implied volatility is rich versus recent H1 realized volatility and price exhaustion confirms. Reject if results require changing GVZ percentile, spread threshold, reversal confirmation, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

This candidate tests whether gold implied volatility that is high relative to recent realized XAU volatility marks short-term H1 exhaustion/reversal opportunities.

The strategy is fully mechanical:

1. Trade XAUUSD only.
2. Use completed H1 bars for XAU price and shifted FRED `GVZCLS` daily observations for gold implied volatility.
3. Compute H1 ATR(14), EMA(40), 8-bar log return, 24-bar log return, and 72-bar realized volatility from completed H1 log returns.
4. Convert realized volatility to an annualized percentage and compare it to shifted GVZ close.
5. Compute shifted daily GVZ 5-business-day return, shifted GVZ 252-day percentile, shifted GVZ minus realized-volatility spread, and a 252-observation z-score of that spread.
6. Long setup:
   - shifted GVZ percentile >= 0.65,
   - shifted GVZ 5-day return >= 0.03,
   - implied-minus-realized spread z-score >= 0.45 or raw spread >= 4.0 points,
   - completed H1 24-bar return <= -0.004,
   - completed H1 8-bar return >= -0.0035,
   - completed H1 candle closes above open,
   - completed H1 close location within candle range >= 0.60,
   - close is not more than 0.75 ATR above EMA(40).
7. Short setup:
   - shifted GVZ percentile >= 0.65,
   - shifted GVZ 5-day return >= 0.03,
   - implied-minus-realized spread z-score >= 0.45 or raw spread >= 4.0 points,
   - completed H1 24-bar return >= 0.004,
   - completed H1 8-bar return <= 0.0035,
   - completed H1 candle closes below open,
   - completed H1 close location within candle range <= 0.40,
   - close is not more than 0.75 ATR below EMA(40).
8. Entry is simulated at market on the signal bar close.
9. Stop is 1.05 ATR from estimated entry.
10. Target is 1.50R.
11. Planned time stop is 18 H1 bars.
12. One trade per direction per UTC day.

## Expected Behavior

Expected trade count: at least 40 trades per 3-year cost/broker cell if the GVZ-realized-volatility spread occurs often enough.

Expected PF: at least 1.30 in 7 of 9 cells if the options-implied stress premium captures tradable XAU exhaustion rather than simply lagging realized movement.

Expected losing-month percentage: below 45%.

Expected worst month: no single month should dominate more than 25% of total profit.

Expected zero-trade months: no more than 3 consecutive zero-trade months.

Expected R distribution: moderate win rate with right-skew from 1.50R targets.

## Why This Hypothesis Should Exist

GVZ is a gold options implied-volatility measure. When implied volatility expands faster than recent realized H1 volatility, options markets may be pricing fear or hedging demand that is not yet fully reflected in spot movement. If XAU then shows a completed H1 exhaustion candle after an intraday directional move, the volatility premium may identify crowded near-term hedging/overreaction rather than a continuation regime.

This is separate from the prior GVZ-only panic lane and the GVZ/VIX relative-premium lane because it compares gold implied volatility to realized XAU volatility, not to another implied-volatility index.

## What Would Falsify It

Reject without tuning if any of the following occurs:

- fewer than 7 of 9 cells reach PF >= 1.30,
- any broker/cost window has too few trades for the first-pass matrix gate,
- the result depends on one broker or one cost assumption,
- P95 cost materially erases the edge,
- concentration, activity, or catastrophic-loss gates fail,
- the only positive evidence comes from one calendar episode,
- later edits change the GVZ percentile, spread threshold, reversal candle, ATR stop, target, time stop, or daily frequency rule after seeing the first result.

## Code Mapping

- Strategy class: `src/phase0/strategies/h1_gvz_realized_vol_spread_reversal_v0.py`
- Data loader: `src/phase0/gvz_volatility_data.py`
- Synthetic smoke: `src/phase0/synthetic.py`
- Matrix orchestration: `src/phase0/matrix.py`
