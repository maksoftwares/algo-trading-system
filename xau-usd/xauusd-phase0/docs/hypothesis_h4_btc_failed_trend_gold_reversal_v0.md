# H4 BTC Failed Trend Gold Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 25-120
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 gold reversal trades after shifted BTC 20-day trend follow-through failure, with wider stops and lower turnover than M5 retest systems.

## Mechanical Definition

This candidate tests BTC trend failure rather than BTC crash/rally pressure or volatility regime. It asks whether a strong BTC 20-day move that fails over the most recent shifted 5-day window creates a short-lived cross-asset rotation window for XAUUSD. It is not a breakout/retest system, not a round-level system, and not a tuning pass of any prior BTC candidate.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Existing public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC daily features are shifted by one completed daily observation before H4 alignment.

BTC failed-trend features:

1. Compute BTC 5-day and 20-day log returns.
2. Compute a 126-day z-score of the BTC 5-day return.
3. Compute a 252-day percentile rank of absolute BTC 5-day return.
4. Failed BTC rally context is active when:
   - shifted BTC 20-day log return is at least `+0.120`
   - shifted BTC 5-day log return is at most `-0.030`
   - shifted BTC 5-day return z-score is at most `-0.25`
   - shifted BTC absolute-return percentile is at least `0.45`
5. Failed BTC selloff context mirrors the rally context with signs reversed.

H4 execution:

1. Compute H4 ATR14, EMA40, 3-bar return, and 6-bar return.
2. Long setup:
   - failed BTC rally context is active
   - H4 3-bar return <= `-0.20%`
   - H4 6-bar return >= `-5.00%`
   - completed H4 candle closes bullish
   - close location >= `0.58`
   - close is between `-3.25 x ATR14` and `+1.25 x ATR14` from EMA40
3. Short setup:
   - failed BTC selloff context is active
   - H4 3-bar return >= `+0.20%`
   - H4 6-bar return <= `+5.00%`
   - completed H4 candle closes bearish
   - close location <= `0.42`
   - close is between `-1.25 x ATR14` and `+3.25 x ATR14` from EMA40
4. At most one signal per ISO week and direction.
5. Trade plan uses market entry, `1.45 x H4 ATR14` stop, `1.55R` target, and a planned 8-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS.

## Expected Behavior

The candidate expects XAU to react most cleanly when BTC is not simply crashing or rallying, but when a recent BTC trend fails. A failed BTC rally should represent a risk-appetite stall and favor H4 XAU bullish rejection after a short downside push. A failed BTC selloff should represent risk relief and favor H4 XAU bearish rejection after a short upside push.

## Why This Hypothesis Should Exist

Earlier BTC branches found a sparse but real clue in strict BTC stress plus H4 XAU rejection, while broader pressure, volatility-regime, and compression-expansion versions diluted into negative activity. This candidate tests a different BTC mechanism: trend exhaustion and follow-through failure. It keeps H4 decision timing and wider stops so the measured-cost issue is not the first blocker.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
