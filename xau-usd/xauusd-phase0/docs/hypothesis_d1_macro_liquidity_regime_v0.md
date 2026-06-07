# D1 Macro Liquidity Regime v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 10-80
Expected cost-adjusted PF: 1.00-1.55
Expected losing-month percentage: 35%-85%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 5
Expected R-multiple distribution: slow D1/H4 macro-regime losses near -1R with occasional 1.70R wins when liquidity expansion or contraction aligns with broad-dollar pressure and H4 confirmation.

## Mechanical Definition

Expert: `d1_macro_liquidity_regime_v0`

This is a disabled Phase 0R research candidate. It tests whether official FRED macro-liquidity state, represented by Federal Reserve total assets (`WALCL`) plus broad-dollar pressure (`DTWEXBGS`), can define a lower-frequency gold regime that survives H4 confirmation.

Data source:

- FRED `WALCL` from `data/raw/liquidity/FRED_WALCL.csv`.
- FRED `DTWEXBGS` from `data/raw/macro/FRED_DTWEXBGS.csv`.
- XAUUSD D1 and H4 bars from the existing broker matrix windows.

Feature construction:

1. Compute 13-week log return of Fed total assets.
2. Compute rolling z-score of that 13-week return over a long 780-observation window.
3. Compute 20-day broad-dollar log return and 252-day z-score.
4. Shift all macro features by one observation before merging into H4 decisions.
5. Compute shifted D1 ATR(14), D1 5-day return, and D1 20-day return.
6. Compute H4 ATR(14), EMA(40), 3-bar return, and 12-bar return.

Long setup:

- 13-week Fed asset return is at least `0.012`.
- Fed asset return z-score is at least `0.35`.
- Broad-dollar 20-day return is at most `-0.0040`.
- Broad-dollar z-score is at most `-0.25`.
- D1 20-day XAU return is not deeply negative.
- H4 prints a bullish confirmation candle with close in the upper 42% of its range.

Short setup:

- 13-week Fed asset return is at most `-0.012`.
- Fed asset return z-score is at most `-0.35`.
- Broad-dollar 20-day return is at least `0.0040`.
- Broad-dollar z-score is at least `0.25`.
- D1 20-day XAU return is not deeply positive.
- H4 prints a bearish confirmation candle with close in the lower 42% of its range.

Execution:

1. Use at most one signal per ISO week per direction.
2. Entry is next simulated market entry after the completed H4 signal bar.
3. Stop is 1.45 H4 ATR from the signal close.
4. Target is 1.70R.
5. Planned time stop is 12 H4 bars.

Implementation mapping:

- Loader: `src/phase0/macro_liquidity_data.py`
- Strategy: `src/phase0/strategies/d1_macro_liquidity_regime_v0.py`
- Synthetic fixture: `src/phase0/synthetic.py::_d1_macro_liquidity_regime_context`
- Test: `tests/test_d1_macro_liquidity_regime_v0.py`

## Expected Behavior

This candidate should trade less often than intraday level/retest strategies and should have wider ATR stops. It should win only if gold behaves differently during major liquidity expansion plus dollar weakness or liquidity contraction plus dollar strength.

It should fail if the macro regime is too slow to time H4 entries, if the signal is too sparse, or if one broker carries the result.

## Why This Hypothesis Should Exist

The lower-cost Phase 0R plan explicitly leaves macro/intermarket stress behavior open when a primary-quality data source is available. `WALCL` and `DTWEXBGS` are official FRED series and create a different information class from XAU-only OHLC, BTC, ETF rotation, COT, or retest mechanics.

This is not a tuning edit to real-yield, financial-conditions, or credit-spread candidates. It uses a separate central-bank liquidity mechanism.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- fewer than 7 of 9 matrix cells reach the 40-trade floor
- max consecutive zero-trade months exceeds 5
- concentration gates fail
- one broker/cost pocket carries the result
- measured P95 spread would exceed 0.30R for typical trades
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
