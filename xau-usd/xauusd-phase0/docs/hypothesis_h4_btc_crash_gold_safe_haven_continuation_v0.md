# H4 BTC Crash Gold Safe-Haven Continuation v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 15-110
Expected cost-adjusted PF: 1.00-1.50
Expected losing-month percentage: 35%-82%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H4 continuation losses near -1R with fewer 1.35R winners during crypto crash / XAU safe-haven confirmation regimes.

## Mechanical Definition

Expert: `h4_btc_crash_gold_safe_haven_continuation_v0`

This is a new disabled Phase 0R research candidate. It is not an edit to the rejected BTC stress-reversal family. The rejected family faded XAU after BTC stress; this hypothesis follows XAU only when BTC has crashed and gold has already confirmed safe-haven demand by breaking above recent H4 resistance.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H4 decisions.
- XAUUSD H4 bars from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H4 ATR(14), EMA(40), 3-bar log return, 6-bar log return, and prior 12-bar high.
3. BTC crash state is active only when all are true:
   - `btc_return_5d <= -0.075`
   - `btc_return_z126 <= -0.35`
   - `btc_abs_return_percentile252 >= 0.60`
   - `btc_volume_z126 >= -0.10`
4. Long setup:
   - Completed H4 candle is bullish.
   - Close is above EMA(40).
   - Close breaks the prior 12-bar H4 high.
   - XAU H4 has positive local confirmation: `h4_return_3 >= 0.0025`.
   - XAU H4 is not an extreme runaway: `h4_return_6 <= 0.0525`.
   - Close is in the upper 42% of the candle range.
   - Close is between 0.0 and 3.40 ATR above EMA(40).
   - Breakout distance is no more than 1.65 ATR above the prior 12-bar high.
5. Use at most one signal per ISO week.
6. Entry is next simulated market entry after the completed H4 signal bar.
7. Stop is 1.25 times H4 ATR(14) below the signal close.
8. Target is 1.35R.
9. Planned time stop is 8 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_btc_crash_gold_safe_haven_continuation_v0.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_btc_crash_gold_safe_haven_continuation_context`
- Test: `tests/test_h4_btc_crash_gold_safe_haven_continuation_v0.py`

## Expected Behavior

The candidate should produce more observations than the very sparse H4 BTC stress-reversal v0 but avoid the broad low-quality activity of the H1 BTC variants. It should only work if crypto crash stress sometimes channels into immediate H4 XAU safe-haven continuation after a completed breakout candle.

## Why This Hypothesis Should Exist

BTC stress-reversal v0 had a strong but too-sparse PF profile, while broader follow-ups failed. This candidate asks a different question: when BTC downside stress is already known from shifted daily data, does XAU continuation after its own H4 confirmation survive costs better than reversal timing?

This remains independent from round-number, session, GLD-flow, COT, futures-volume, macro-rate, and ETF-rotation candidates because it uses shifted BTC daily crash pressure plus completed H4 XAU breakout continuation structure.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 5
- cost sensitivity fails under p95 measured spread
- BTC features are not shifted before XAU H4 decisions
- one broker window carries the result while the others fail materially
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
