# H4 BTC Rally Gold Risk-On Continuation v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 15-110
Expected cost-adjusted PF: 1.00-1.50
Expected losing-month percentage: 35%-82%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H4 bearish continuation losses near -1R with fewer 1.35R winners during BTC rally / risk-on confirmation regimes.

## Mechanical Definition

Expert: `h4_btc_rally_gold_risk_on_continuation_v0`

This is a new disabled Phase 0R research candidate. It is not an edit to the rejected BTC stress-reversal family or the BTC crash safe-haven-continuation candidate. It tests the opposite continuation quadrant: shifted BTC rally pressure as a risk-on signal, with XAU short only after gold confirms by breaking below recent H4 support.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H4 decisions.
- XAUUSD H4 bars from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H4 ATR(14), EMA(40), 3-bar log return, 6-bar log return, and prior 12-bar low.
3. BTC rally state is active only when all are true:
   - `btc_return_5d >= 0.075`
   - `btc_return_z126 >= 0.35`
   - `btc_abs_return_percentile252 >= 0.60`
   - `btc_volume_z126 >= -0.10`
4. Short setup:
   - Completed H4 candle is bearish.
   - Close is below EMA(40).
   - Close breaks the prior 12-bar H4 low.
   - XAU H4 has negative local confirmation: `h4_return_3 <= -0.0025`.
   - XAU H4 is not an extreme runaway: `h4_return_6 >= -0.0525`.
   - Close is in the lower 42% of the candle range.
   - Close is between 0.0 and 3.40 ATR below EMA(40).
   - Breakdown distance is no more than 1.65 ATR below the prior 12-bar low.
5. Use at most one signal per ISO week.
6. Entry is next simulated market entry after the completed H4 signal bar.
7. Stop is 1.25 times H4 ATR(14) above the signal close.
8. Target is 1.35R.
9. Planned time stop is 8 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_btc_rally_gold_risk_on_continuation_v0.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_btc_rally_gold_risk_on_continuation_context`
- Test: `tests/test_h4_btc_rally_gold_risk_on_continuation_v0.py`

## Expected Behavior

The candidate should be sparse but not single-trade dominated if BTC rally regimes repeatedly coincide with gold risk-on breakdowns. It should fail if BTC rally pressure is only coincident noise or if XAU breakdown continuation does not generalize across broker windows.

## Why This Hypothesis Should Exist

The BTC crash safe-haven-continuation test failed, but it covered only the BTC downside / XAU upside quadrant. This candidate closes the remaining continuation quadrant by asking whether BTC upside pressure can identify gold downside continuation after XAU has already confirmed with a completed H4 support break.

This remains independent from round-number, session, GLD-flow, COT, futures-volume, macro-rate, and ETF-rotation candidates because it uses shifted BTC daily rally pressure plus completed H4 XAU bearish continuation structure.

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
