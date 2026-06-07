# H4 COT + GC Volume Capitulation Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 10-80
Expected cost-adjusted PF: 1.00-1.55
Expected losing-month percentage: 35%-85%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 6
Expected R-multiple distribution: sparse H4 capitulation reversals with losses near -1R and fewer 1.55R winners.

## Mechanical Definition

Expert: `h4_cot_gc_volume_capitulation_reversal_v0`

This is a new disabled Phase 0R research candidate. It is not a retune of the rejected standalone COT positioning reversal or standalone GC futures-volume climax candidate. It tests whether the combination of slow official CFTC positioning extremes and a fresh GC futures daily-volume climax provides better timing than either source alone.

Data sources:

- Official CFTC gold disaggregated futures-only COT reference file at `data/reference/cot/gold_disaggregated_futures_only_2016_2024.csv`.
- Public Yahoo `GC=F` continuous futures daily OHLCV proxy at `data/reference/futures/gc_continuous_daily_yahoo_2015_2025.csv`.
- XAUUSD H4 and D1 bars from the existing broker matrix windows.

Feature construction:

1. COT features are usable only after a six-day delay from report date.
2. Calculate managed-money net open-interest share, producer net open-interest share, 156-week rolling percentiles, and managed-money 4-week net change.
3. Calculate shifted GC futures daily volume percentile over 252 days and z-score over 126 days.
4. Calculate shifted XAU prior D1 return and prior D1 range relative to D1 ATR(14).
5. Calculate XAU H4 ATR(14), EMA(40), 6-bar return, and completed-candle close location.

Long setup:

- Managed-money percentile is <= 0.35.
- Producer percentile is >= 0.65.
- Managed-money 4-week change is positive.
- Prior XAU D1 return is <= -0.0035.
- Prior XAU D1 range is at least 1.05 ATR.
- Shifted GC volume percentile is >= 0.78.
- Shifted GC volume z-score is >= 0.75.
- Completed H4 candle is bullish and closes in the upper 44% of its range.
- H4 6-bar return is not below -0.0200.
- Close is no more than 1.20 ATR above EMA(40).

Short setup:

- Managed-money percentile is >= 0.65.
- Producer percentile is <= 0.35.
- Managed-money 4-week change is negative.
- Prior XAU D1 return is >= 0.0035.
- Prior XAU D1 range is at least 1.05 ATR.
- Shifted GC volume percentile is >= 0.78.
- Shifted GC volume z-score is >= 0.75.
- Completed H4 candle is bearish and closes in the lower 44% of its range.
- H4 6-bar return is not above 0.0200.
- Close is no more than 1.20 ATR below EMA(40).

Trade management:

- Use at most one signal per COT report week per direction.
- Entry is next simulated market entry after the completed H4 signal bar.
- Stop is 1.20 times H4 ATR(14) beyond the signal close.
- Target is 1.55R.
- Planned time stop is 8 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_cot_gc_volume_capitulation_reversal_v0.py`
- COT data loader: `src/phase0/cot_gold_data.py`
- GC volume data loader: `src/phase0/gc_futures_volume_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_cot_gc_volume_capitulation_reversal_context`
- Test: `tests/test_h4_cot_gc_volume_capitulation_reversal_v0.py`

## Expected Behavior

The candidate should be sparse, but it should not be single-broker or single-trade dominated if the thesis is real. The intended edge is a positioning capitulation reversal: slow money is already at an extreme and starting to turn, then a fresh high-volume GC/XAU down-day or up-day creates an H4 reversal opportunity.

## Why This Hypothesis Should Exist

Standalone COT reversal was too sparse and weak. Standalone GC volume climax was also too sparse and weak. This candidate asks a different, stricter question: does requiring both official positioning stress and fresh futures-volume capitulation improve signal quality enough to survive broker/cost variation?

This remains independent from BTC, GLD-flow, ETF-rotation, macro-rate, session, round-number, and pure OHLC candidates because it requires two separate external gold-specific data classes.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 6
- cost sensitivity fails under p95 measured spread
- COT data is used before its six-day availability lag
- GC volume features are not shifted before XAU H4 decisions
- one broker window carries the result while the others fail materially
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
