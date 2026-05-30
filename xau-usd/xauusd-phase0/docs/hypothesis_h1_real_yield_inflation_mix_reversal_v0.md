# Hypothesis: h1_real_yield_inflation_mix_reversal_v0

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Hypothesis SHA256: pending registration
Mechanic family: real-yield and inflation-compensation decomposition reversal
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-500
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: frequent 1R losses, occasional 1.45R reversals after macro mix dislocations

## Status

RESEARCH_ONLY / PRE-REGISTERED.

This candidate is not an approved expert. It must pass the research matrix without tuning before it can be considered for any later dry-run or demo work.

## Mechanical Definition

Use shifted daily public FRED inputs:

- `DFII10`: 10-year real yield
- `DTWEXBGS`: broad dollar index
- `T5YIE`: 5-year breakeven inflation expectation
- `T10YIE`: 10-year breakeven inflation expectation

Build H1 XAUUSD features from completed bars only:

- ATR(14)
- EMA(50)
- 8-hour log return
- 24-hour log return
- candle close location inside the H1 range

Daily macro features are merged backward into H1 bars after shifting the external feature columns by one observation.

Long setup:

1. 20-day real yield change is <= -0.08.
2. 5-year breakeven change is >= 0.04 or 10-year breakeven change is >= 0.03.
3. 20-day broad dollar return is not strongly adverse, `<= 0.015`.
4. Real-yield change z-score is <= -0.40 or breakeven change z-score is >= 0.40.
5. Gold has sold off over 24 H1 bars, `h1_return_24 <= -0.004`.
6. Gold has stopped accelerating lower, `h1_return_8 >= -0.0025`.
7. Current H1 candle closes bullish, in the upper 40% of its range.
8. Price is not more than 1.2% above EMA50.

Short setup:

1. 20-day real yield change is >= 0.08.
2. 5-year breakeven change is <= -0.04 or 10-year breakeven change is <= -0.03.
3. 20-day broad dollar return is not strongly supportive for gold, `>= -0.015`.
4. Real-yield change z-score is >= 0.40 or breakeven change z-score is <= -0.40.
5. Gold has rallied over 24 H1 bars, `h1_return_24 >= 0.004`.
6. Gold has stopped accelerating higher, `h1_return_8 <= 0.0025`.
7. Current H1 candle closes bearish, in the lower 40% of its range.
8. Price is not more than 1.2% below EMA50.

Limit entries to one signal per UTC date per direction. Only evaluate at fixed UTC decision hours: 07, 09, 11, 13, 15, 17, 19, and 21.

Trade plan:

- Entry type: market simulation
- Stop: 1.0 x H1 ATR(14)
- Target: 1.45R
- Time stop: 18 H1 bars
- Hard max holding: 216 M5 bars

## Expected Behavior

This is expected to be lower frequency than M5 breakout-retest and higher frequency than H4/D1 macro candidates. It should produce enough activity only during periods where real yields and inflation compensation diverge meaningfully and gold has already moved against the supportive macro mix.

## Why This Hypothesis Should Exist

Gold can respond differently to nominal-rate shocks depending on whether the rate move is driven by real yields or inflation compensation. A falling-real-yield / rising-breakeven mix should be supportive for gold even if spot has recently sold off. A rising-real-yield / falling-breakeven mix should be hostile for gold even if spot has recently rallied. This candidate tests whether the first H1 rejection after that macro mix creates a tradable mean-reversion impulse.

## What Would Falsify It

- Fewer than 40 trades in most broker/cost cells.
- Fewer than 7 of 9 matrix cells with PF >= 1.30.
- Profitability exists only in one broker or one cost model.
- Returns are concentrated in a small number of trades or months.
- The setup works only before costs or only under best-case costs.
- Zero-trade months exceed the Phase 0 activity limits.

## Code Mapping

- Strategy class: `src/phase0/strategies/h1_real_yield_inflation_mix_reversal_v0.py::H1RealYieldInflationMixReversalV0Strategy`
- Macro context: `src/phase0/macro_real_yield_data.py`
- Inflation context: `src/phase0/inflation_expectations_data.py`
- Registry: `src/phase0/strategies/registry.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h1_real_yield_inflation_mix_reversal_context`
