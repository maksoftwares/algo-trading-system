# H4 GDX/GLD Miner Divergence Reversal v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: GDX/GLD miner relative-strength divergence reversal
Entry / decision timeframe: H4 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 40-300
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R reversals after miner/GLD relative-strength divergence. Reject if results require changing the relative-return threshold, z-score, percentile, decision hours, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Data Source

This candidate uses public Yahoo Finance daily OHLCV data for:

- `GLD`: gold ETF proxy for exchange-traded gold participation.
- `GDX`: gold miners ETF proxy for producer/equity-risk confirmation or divergence.

The file is stored at:

```text
data/reference/etf/gdx_gld_daily_yahoo_2015_2025.csv
```

This is not primary COMEX/CME order-flow data. It is a public ETF relative-strength proxy. All daily ETF features are shifted one completed daily observation before being joined to H4 XAUUSD bars.

## Mechanical Definition

For each XAUUSD H4 bar at 12:00, 16:00, or 20:00 UTC:

1. Compute XAU H4 ATR(14), EMA(40), and 12-bar log return.
2. From shifted daily ETF data, compute:
   - `gld_return_1d`
   - `gdx_return_1d`
   - `miner_relative_return_1d = gdx_return_1d - gld_return_1d`
   - 126-day z-score of the miner relative return
   - 252-day rolling percentile of absolute miner relative return
3. Long setup:
   - `miner_relative_return_1d >= 0.012`
   - `miner_relative_z126 >= 0.85`
   - `miner_abs_relative_percentile252 >= 0.65`
   - XAU H4 12-bar return is less than or equal to `-0.0030`
   - current H4 candle closes bullish
   - current H4 close location is at least 0.58 of its range
   - close is not extended more than 0.50 ATR above EMA(40)
4. Short setup:
   - `miner_relative_return_1d <= -0.012`
   - `miner_relative_z126 <= -0.85`
   - `miner_abs_relative_percentile252 >= 0.65`
   - XAU H4 12-bar return is greater than or equal to `0.0030`
   - current H4 candle closes bearish
   - current H4 close location is no more than 0.42 of its range
   - close is not extended more than 0.50 ATR below EMA(40)
5. Only one signal per UTC day and direction is allowed.
6. Entry is market at the H4 signal close.
7. Stop is 1.10 x H4 ATR from entry.
8. Target is 1.50R.
9. Planned time stop is 6 H4 bars.

## Expected Behavior

Expected trade count: at least 40 trades per 3-year cell if the divergence event is frequent enough.

Expected PF: at least 1.30 in 7 of 9 matrix cells after p95 cost.

Expected losing-month percentage: less than 50%.

Expected worst month: no single month should dominate the full result.

Expected max zero-trade months: no more than 3.

Expected R distribution: fewer but cleaner H4 reversal trades than the active breakout-retest family, with lower frequency and lower cost drag.

## Why This Hypothesis Should Exist

Gold miners can behave as a higher-beta, equity-risk-sensitive confirmation market for gold. When miners materially outperform GLD while spot gold is already stretched lower, the selling pressure in XAU may be overextended or not confirmed by gold equities. Conversely, when miners materially underperform GLD while spot gold is stretched higher, spot strength may be fragile. The H4 reversal candle is required so the strategy does not trade purely from daily ETF divergence.

The hoped-for edge is independent from the existing breakout-retest family because it does not use swing levels, round levels, retests, or M5 breakout structure. It uses cross-market relative behavior plus H4 reversal timing.

## What Would Falsify It

Reject this candidate without tuning if any of the following occurs:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any cost-sensitive p95 cell materially collapses versus best-case cost
- fewer than 40 trades occur in any matrix cell
- max zero-trade months exceeds 3
- concentration gates fail
- decile persistence fails if the candidate reaches decile testing
- multisymbol or XAU-specific transfer defense fails if the candidate reaches multisymbol testing
- manual adversarial review finds more than 25% logic-gap losses

## No-Tuning Commitment

This v0 may not be tuned in place. If it fails, it must be marked `REJECTED_FIRST_PASS`. A future `v1` may only be created as a separate result-informed hypothesis with a clear reviewer note.
