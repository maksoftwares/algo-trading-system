# Hypothesis: h1_real_yield_inflation_mix_followthrough_v0

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Hypothesis SHA256: pending registration
Mechanic family: real-yield and inflation-compensation decomposition follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 36-120
Expected median hold hours: 3-10
Expected decisions per week: 0-10
Timeframe diversification qualifies: yes
Expected trade count per year: 75-600
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: frequent 1R losses with clustered 1.35R wins when macro mix and H1 momentum align

## Status

RESEARCH_ONLY / PRE-REGISTERED.

This candidate is not an approved expert. It is the paired follow-through test for the rejected real-yield / inflation-compensation reversal lane. It must pass first pass as a new locked hypothesis; it cannot borrow approval from any related candidate.

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
5. Gold has already started following the supportive macro mix, `h1_return_24 >= 0.003`.
6. Gold has positive near-term follow-through, `h1_return_8 >= 0.0015`.
7. Current H1 candle closes bullish, in the upper 42% of its range.
8. Close is above EMA50 but not more than 2.5% above EMA50.

Short setup:

1. 20-day real yield change is >= 0.08.
2. 5-year breakeven change is <= -0.04 or 10-year breakeven change is <= -0.03.
3. 20-day broad dollar return is not strongly supportive for gold, `>= -0.015`.
4. Real-yield change z-score is >= 0.40 or breakeven change z-score is <= -0.40.
5. Gold has already started following the hostile macro mix, `h1_return_24 <= -0.003`.
6. Gold has negative near-term follow-through, `h1_return_8 <= -0.0015`.
7. Current H1 candle closes bearish, in the lower 42% of its range.
8. Close is below EMA50 but not more than 2.5% below EMA50.

Limit entries to one signal per UTC date per direction. Only evaluate at fixed UTC decision hours: 07, 09, 11, 13, 15, 17, 19, and 21.

Trade plan:

- Entry type: market simulation
- Stop: 1.0 x H1 ATR(14)
- Target: 1.35R
- Time stop: 14 H1 bars
- Hard max holding: 168 M5 bars

## Expected Behavior

This paired version should trade more often than the reversal version because it enters with the local H1 move instead of waiting for spot to reject a prior adverse move. If the macro mix has directional information, this version should produce a broader PF footprint than the reversal lane.

## Why This Hypothesis Should Exist

Gold may follow real-yield and inflation-compensation changes directly rather than mean-reverting after an adverse spot move. A falling-real-yield / rising-breakeven mix is gold-supportive; a rising-real-yield / falling-breakeven mix is gold-hostile. This candidate tests whether the first H1 continuation after those shifted macro conditions align has tradable persistence.

## What Would Falsify It

- Fewer than 40 trades in most broker/cost cells.
- Fewer than 7 of 9 matrix cells with PF >= 1.30.
- Profitability exists only in one broker or one cost model.
- Returns are concentrated in a small number of trades or months.
- The setup works only before costs or only under best-case costs.
- Zero-trade months exceed the Phase 0 activity limits.

## Code Mapping

- Strategy class: `src/phase0/strategies/h1_real_yield_inflation_mix_followthrough_v0.py::H1RealYieldInflationMixFollowthroughV0Strategy`
- Macro context: `src/phase0/macro_real_yield_data.py`
- Inflation context: `src/phase0/inflation_expectations_data.py`
- Registry: `src/phase0/strategies/registry.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h1_real_yield_inflation_mix_followthrough_context`
