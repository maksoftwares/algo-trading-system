# H4 BTC GVZ Dual Vol Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 15-100
Expected cost-adjusted PF: 1.00-1.50
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 gold rejection trades during combined BTC volatility stress and gold-volatility premium.

## Mechanical Definition

This candidate tests whether BTC volatility stress becomes more useful when gold's own implied volatility is outperforming equity volatility. It is not a BTC-only pressure strategy, not a BTC whipsaw/path-efficiency strategy, not a GLD-flow strategy, and not a threshold edit of the rejected single-source GVZ/VIX or BTC volatility-regime candidates. Both external regimes must be active before H4 XAU rejection can trigger.

Data sources:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- Public FRED GVZCLS observations.
- Public FRED VIXCLS observations.
- BTC, GVZ, and VIX daily features are shifted by one completed daily observation before H4 alignment.

BTC volatility-stress state:

1. Compute BTC 1-day log returns.
2. Compute 10-day and 40-day BTC realized volatility.
3. Compute `btc_vol_ratio_10_40 = realized_vol_10d / realized_vol_40d`.
4. Compute 252-day percentile ranks for BTC 10-day volatility and absolute 1-day return.
5. BTC volatility stress is active when:
   - `btc_vol_ratio_10_40 >= 1.08`
   - `btc_vol_percentile252 >= 0.55`
   - `btc_abs_return_percentile252 >= 0.45`

Gold-volatility premium state:

1. Compute GVZ and VIX 5-day returns.
2. Compute GVZ/VIX ratio, 252-day z-score, 5-day ratio change, and 126-day change z-score.
3. Gold-volatility premium is active when:
   - `gvz_vix_ratio_z252 >= 0.35`
   - `gvz_return_5d > vix_return_5d`
   - `gvz_vix_ratio_change_5d >= 0.020` or `gvz_vix_ratio_change_z126 >= 0.35`

H4 execution:

1. Compute H4 ATR14, EMA40, 6-bar return, and 12-bar return.
2. Long setup:
   - BTC volatility stress is active
   - gold-volatility premium is active
   - H4 6-bar return <= `-0.35%`
   - H4 12-bar return >= `-5.50%`
   - completed H4 candle closes bullish
   - close location >= `0.58`
   - close is no farther than `1.00 x ATR14` above EMA40
3. Short setup mirrors the long setup after upside overextension.
4. At most one signal per ISO week and direction.
5. Trade plan uses market entry, `1.30 x H4 ATR14` stop, `1.55R` target, and a planned 7-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS expected before real matrix.

## Expected Behavior

The candidate expects XAU H4 reversal trades to be cleaner when BTC confirms speculative volatility stress and GVZ confirms that gold-specific option demand is rising faster than broad equity fear.

## Why This Hypothesis Should Exist

BTC-only volatility and whipsaw branches either failed PF or became sparse. GVZ/VIX H4 reversal had positive-PnL persistence but insufficient PF coverage. This candidate tests whether requiring both cross-asset crypto volatility and gold-specific volatility premium improves selection quality enough to survive the 9-cell gates.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
